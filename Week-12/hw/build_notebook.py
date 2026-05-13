"""Generate Week12_ARIA_v80_Homework.ipynb from this script.

Run:  python build_notebook.py
"""
from __future__ import annotations
import nbformat as nbf
from pathlib import Path

nb = nbf.v4.new_notebook()
cells = []

def md(src: str):
    cells.append(nbf.v4.new_markdown_cell(src.strip("\n")))

def code(src: str):
    cells.append(nbf.v4.new_code_cell(src.strip("\n")))


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
md(r"""
# Week 12 Homework — ARIA v8.0 : The Classification Engine

**Course:** 遙測與空間資訊之分析與應用 (NTU)
**Instructor:** Prof. Su Wen-Ray
**Case Study:** 2024-04-03 花蓮地震（M7.4）後秀林 / 太魯閣土地覆蓋分類

---

## Mission

> 指揮官不再滿足於「哪裡有異常」。他需要一張完整的災後**土地覆蓋圖**——
> 每個像素對應一個類別：水體、森林、農田、裸地/崩塌、建物/都市。
> 這張圖是所有後續分析（避難所評估、路網可達性、崩塌面積計算）的基礎圖資。

**Upgrade ladder：**

| 版本 | 任務 | 方法 |
|---|---|---|
| v5.0 (W8) | 異常偵測 | 目視 + 假彩色 |
| v6.0 (W9) | 變遷偵測 | ΔNDVI + 變遷信心 |
| v7.0 (W10) | 全天候融合 | SAR + NDWI + DEM |
| **v8.0 (W12)** | **多類分類** | **K-means + Random Forest** |

This notebook implements all 4 tasks for the Xiulin / Taroko study area —
**a mountainous coastal region different from the in-class Hualien City demo**.
""")

# ─────────────────────────────────────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────────────────────────────────────
md(r"""
## [S1] Environment & Configuration

讀取 `.env` 並設定全域參數。若在 Colab 上執行，請先把 `.env`、
`data/20240802新生崩塌地.kml` 上傳到 working directory。
""")

code(r"""
import os, sys, time, warnings
warnings.filterwarnings('ignore')
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BBOX = [
    float(os.getenv('BBOX_WEST',  121.40)),
    float(os.getenv('BBOX_SOUTH', 24.10)),
    float(os.getenv('BBOX_EAST',  121.80)),
    float(os.getenv('BBOX_NORTH', 24.25)),
]
RESOLUTION   = int(os.getenv('RESOLUTION', 20))
KMEANS_K     = int(os.getenv('KMEANS_K', 5))
RF_TREES     = int(os.getenv('RF_TREES', 200))
RANDOM_STATE = int(os.getenv('RANDOM_STATE', 42))
OUTPUT_DIR   = Path(os.getenv('OUTPUT_DIR', 'output'))
SWCB_KML     = Path(os.getenv('SWCB_KML', 'data/20240802新生崩塌地.kml'))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f'BBOX        : {BBOX}')
print(f'Resolution  : {RESOLUTION} m')
print(f'K-means K   : {KMEANS_K}')
print(f'RF trees    : {RF_TREES}')
print(f'Random seed : {RANDOM_STATE}')
print(f'Output dir  : {OUTPUT_DIR.resolve()}')
print(f'SWCB KML    : {SWCB_KML}  (exists={SWCB_KML.exists()})')
""")

code(r"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import xarray as xr

import pystac_client
import planetary_computer as pc
import stackstac

from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    confusion_matrix, classification_report, ConfusionMatrixDisplay,
)

print('libraries loaded ✅')
""")

# ─────────────────────────────────────────────────────────────────────────────
# Captain's Log #1
# ─────────────────────────────────────────────────────────────────────────────
md(r"""
### 🧭 Captain's Log #1 — Why classification?

W7–W10 我們學會了「閾值法」（NDVI > T、VV < T_dB），它的優點是直觀，
但本質是「**一次只能用一個指標把世界分成兩半**」。

```
閾值法    NDVI > 0.3 → 植被 / 非植被
                                    ↓
分類器    f(B02,...,B12) → {水, 森林, 農田, 崩塌, 建物}
```

當地物超過 2 類、且光譜重疊時（例如崩塌與裸地、農田與草地），閾值法就會失靈。
這一週我們把 ARIA 從**單維分類**升級成**多維分類**：

* **Task 1 (K-means)** — 非監督，「資料自己分群」，沒有 label。
* **Task 2 (Random Forest)** — 監督式，「我說這幾個像素是水體，請學會所有水體」。
* **Task 3 (Accuracy)** — 內部 confusion matrix + 外部 SWCB 比對（雙重檢驗）。
* **Task 4 (LLM)** — 用 Gemini 把面積數字翻成指揮官報告，再批判它。
""")

# ─────────────────────────────────────────────────────────────────────────────
# S2 STAC search
# ─────────────────────────────────────────────────────────────────────────────
md(r"""
## [S2] STAC Search — Post-earthquake Sentinel-2 (Progressive)

太魯閣地區地震後正值春雨季，雲量大。採三階段**漸進式搜尋**：
"嚴格 → 放寬"，直到找到至少一景。
""")

code(r"""
catalog = pystac_client.Client.open(
    'https://planetarycomputer.microsoft.com/api/stac/v1',
    modifier=pc.sign_inplace,
)

search_configs = [
    (os.getenv('PHASE1_RANGE'), int(os.getenv('PHASE1_CC', 20)), 'Phase 1: 2 months post-quake, CC < 20%'),
    (os.getenv('PHASE2_RANGE'), int(os.getenv('PHASE2_CC', 30)), 'Phase 2: 5 months post-quake, CC < 30%'),
    (os.getenv('PHASE3_RANGE'), int(os.getenv('PHASE3_CC', 50)), 'Phase 3: full year post-quake, CC < 50%'),
]

items = []
for dt_range, max_cc, desc in search_configs:
    print(f'→ {desc}  range={dt_range}')
    search = catalog.search(
        collections=['sentinel-2-l2a'],
        bbox=BBOX,
        datetime=dt_range,
        query={'eo:cloud_cover': {'lt': max_cc}},
    )
    items = list(search.items())
    print(f'  found {len(items)} scenes')
    if items:
        break

items_sorted = sorted(items, key=lambda x: x.properties['eo:cloud_cover'])
print('\nTop 5 candidates (sorted by cloud cover):')
for it in items_sorted[:5]:
    print(f"  {it.id}  CC={it.properties['eo:cloud_cover']:.1f}%  "
          f"date={it.datetime.date()}")

best_item = items_sorted[0]
print(f"\n✅ Selected: {best_item.id}")
print(f"   cloud_cover = {best_item.properties['eo:cloud_cover']:.1f}%")
print(f"   datetime    = {best_item.datetime}")
""")

# ─────────────────────────────────────────────────────────────────────────────
# S3 Stream cube + SCL cloud mask
# ─────────────────────────────────────────────────────────────────────────────
md(r"""
## [S3] Stream + SCL Cloud Mask

* **6 反射波段 + SCL（Scene Classification Layer）**
* SCL 是 Sentinel-2 L2A 內建的場景分類層；3=雲影、8/9=雲、10=薄雲、11=雪
* 在分類前**先把雲/雲影/雪的像素設為 NaN**，避免污染訓練資料
""")

code(r"""
BANDS = ['B02', 'B03', 'B04', 'B08', 'B11', 'B12']
BAND_LABELS = {
    'B02': 'Blue (490 nm)',
    'B03': 'Green (560 nm)',
    'B04': 'Red (665 nm)',
    'B08': 'NIR (842 nm)',
    'B11': 'SWIR1 (1610 nm)',
    'B12': 'SWIR2 (2190 nm)',
}
BANDS_ALL = BANDS + ['SCL']

t0 = time.time()
# Taiwan is in UTM zone 51N (EPSG:32651); resolution in METRES.
cube = stackstac.stack(
    [best_item],
    assets=BANDS_ALL,
    bounds_latlon=BBOX,
    resolution=RESOLUTION,
    epsg=32651,
    chunksize=2048,
)
print(f'cube shape (raw)    : {cube.shape}   dims={cube.dims}')
print(f'cube CRS            : EPSG:32651 (UTM zone 51N)')

img = cube.isel(time=0).compute()
print(f'image after compute : {img.shape}   in {time.time()-t0:.1f}s')

# Surface reflectance (S2 L2A scale = 10000)
img_refl = (img.sel(band=BANDS).astype('float32') / 10000.0)
scl      = img.sel(band='SCL').astype('uint8')

# Mask cloud / cloud-shadow / snow using SCL
SCL_BAD = {0, 1, 3, 8, 9, 10, 11}   # NoData, saturated, shadow, cloud, thin-cirrus, snow
bad_mask = np.isin(scl.values, list(SCL_BAD))
print(f'SCL bad pixels      : {bad_mask.sum():,}  ({bad_mask.mean()*100:.1f}%)')

img_refl = img_refl.where(~bad_mask)        # broadcast: same (y,x) shape → NaN on bad pixels

print(f'reflectance shape   : {img_refl.shape}  (band,y,x)')
""")

code(r"""
# Quick-look: true-colour + false-colour (sanity check)
def stretch(a, p=(2, 98)):
    lo, hi = np.nanpercentile(a, p)
    return np.clip((a - lo) / (hi - lo + 1e-9), 0, 1)

rgb_true  = np.dstack([stretch(img_refl.sel(band=b).values) for b in ['B04','B03','B02']])
rgb_false = np.dstack([stretch(img_refl.sel(band=b).values) for b in ['B08','B04','B03']])

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
axes[0].imshow(rgb_true);  axes[0].set_title('True-colour (B04,B03,B02)')
axes[1].imshow(rgb_false); axes[1].set_title('False-colour (NIR,Red,Green)')
for a in axes: a.set_axis_off()
plt.tight_layout()
plt.savefig(OUTPUT_DIR/'S3_quicklook.png', dpi=120, bbox_inches='tight')
plt.show()
""")

# ─────────────────────────────────────────────────────────────────────────────
# Task 1 — K-means
# ─────────────────────────────────────────────────────────────────────────────
md(r"""
## Task 1 — K-means Unsupervised Classification (15%)

**Goal:** 在沒有訓練資料的情況下，讓影像「自己分 5 群」，
然後用 cluster mean spectrum 推測每群代表什麼地物。
""")

code(r"""
# Build feature matrix
n_bands, h, w = img_refl.shape
X = img_refl.values.reshape(n_bands, -1).T      # (h*w, 6)
valid = ~np.isnan(X).any(axis=1)
X_valid = X[valid]
print(f'Image grid    : {h} × {w}')
print(f'Total pixels  : {h*w:,}')
print(f'Valid pixels  : {X_valid.shape[0]:,}  ({valid.mean()*100:.1f}%)')

# Optional sub-sample (speed)
MAX_FIT = 200_000
rng = np.random.default_rng(RANDOM_STATE)
if X_valid.shape[0] > MAX_FIT:
    idx_fit = rng.choice(X_valid.shape[0], size=MAX_FIT, replace=False)
    X_fit   = X_valid[idx_fit]
    print(f'Fitting K-means on a {MAX_FIT:,} pixel subsample for speed')
else:
    X_fit = X_valid
""")

code(r"""
t0 = time.time()
kmeans = KMeans(n_clusters=KMEANS_K, random_state=RANDOM_STATE, n_init=10)
kmeans.fit(X_fit)
print(f'KMeans fit in {time.time()-t0:.1f}s')

# Predict all valid pixels
labels = kmeans.predict(X_valid)

# Rebuild as 2-D map
label_map = np.full(h * w, np.nan)
label_map[valid] = labels
label_map = label_map.reshape(h, w)
print(f'Cluster sizes: {np.bincount(labels)}')
""")

code(r"""
# Cluster-mean spectra (used for manual labelling)
cluster_means = np.array([X_valid[labels == k].mean(axis=0) for k in range(KMEANS_K)])
cluster_df = pd.DataFrame(cluster_means, columns=BANDS,
                          index=[f'cluster_{k}' for k in range(KMEANS_K)]).round(3)
cluster_df['n_pixels'] = [int((labels == k).sum()) for k in range(KMEANS_K)]
cluster_df['NDVI']     = ((cluster_df['B08'] - cluster_df['B04']) /
                          (cluster_df['B08'] + cluster_df['B04'])).round(3)
cluster_df['NDWI']     = ((cluster_df['B03'] - cluster_df['B08']) /
                          (cluster_df['B03'] + cluster_df['B08'])).round(3)
print('— Cluster mean spectra —')
print(cluster_df)
""")

code(r"""
# Manual cluster → land-cover label inference (heuristic)
def guess_label(row):
    # Heuristics: Water=low NIR + NDWI>0; Forest=NDVI>0.55;
    # Cropland=0.25-0.55 NDVI; Bare=low NDVI+high SWIR; Built-up=otherwise
    if row['NDWI'] > 0.1 and row['B08'] < 0.15:
        return 'Water'
    if row['NDVI'] > 0.55:
        return 'Forest'
    if row['NDVI'] > 0.25:
        return 'Cropland'
    if row['B11'] > 0.20 and row['NDVI'] < 0.2:
        return 'Bare/Landslide'
    return 'Built-up'

cluster_df['guess_label'] = cluster_df.apply(guess_label, axis=1)
print(cluster_df[['B02','B03','B04','B08','B11','B12','NDVI','NDWI','guess_label']])

cluster_df.to_csv(OUTPUT_DIR/'Task1_cluster_means.csv')
""")

code(r"""
# Visualise K-means classification
cmap_k = plt.get_cmap('tab10', KMEANS_K)
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
axes[0].imshow(rgb_true)
axes[0].set_title('Reference: true-colour (B04,B03,B02)')
axes[0].set_axis_off()

im = axes[1].imshow(label_map, cmap=cmap_k, vmin=-0.5, vmax=KMEANS_K-0.5)
axes[1].set_title(f'K-means (K={KMEANS_K})')
axes[1].set_axis_off()
cbar = plt.colorbar(im, ax=axes[1], ticks=range(KMEANS_K),
                    fraction=0.04, pad=0.02)
cbar.ax.set_yticklabels([f'{k}: {cluster_df.iloc[k]["guess_label"]}'
                         for k in range(KMEANS_K)])
plt.tight_layout()
plt.savefig(OUTPUT_DIR/'kmeans_classification.png', dpi=150, bbox_inches='tight')
plt.show()
""")

code(r"""
# Mean-spectrum plot — easier than reading the table
fig, ax = plt.subplots(figsize=(10, 5))
wavelen_nm = [490, 560, 665, 842, 1610, 2190]
for k in range(KMEANS_K):
    ax.plot(wavelen_nm, cluster_means[k], '-o',
            label=f"C{k} → {cluster_df.iloc[k]['guess_label']}  (n={int(cluster_df.iloc[k]['n_pixels']):,})")
ax.set_xlabel('Wavelength (nm)')
ax.set_ylabel('Surface reflectance')
ax.set_title('K-means cluster mean spectra')
ax.legend()
ax.grid(alpha=.3)
plt.tight_layout()
plt.savefig(OUTPUT_DIR/'Task1_cluster_spectra.png', dpi=150, bbox_inches='tight')
plt.show()
""")

md(r"""
### 💬 Task 1 Discussion

| Cluster | 推測類別 | 信心 | 判讀依據 |
|---|---|---|---|
| 易判讀 | **Water** | 高 | 太平洋大面積、NIR 極低、NDWI > 0 — 沒有混淆 |
| 易判讀 | **Forest** | 高 | 中央山脈植被覆蓋率最大、NDVI 高、占地最廣 |
| 較難判 | **Cropland** | 中 | 太魯閣山區農田極少；可能與草地、疏林混淆 |
| 較難判 | **Bare/Landslide** | 中 | 崩塌、岩石、河床都是「低 NDVI + 高 SWIR」，光譜重疊嚴重 |
| 較難判 | **Built-up** | 低 | 山區聚落很小、像素少（< 1%），常被併入 bare 或 cropland |

> **結論：K-means 解開了「天然光譜結構」，但類別命名仍需要人類判讀**——
> cluster 自己不會說自己是水或森林。這就是為什麼下一步要做 supervised RF。
""")

# ─────────────────────────────────────────────────────────────────────────────
# Task 2 — Random Forest
# ─────────────────────────────────────────────────────────────────────────────
md(r"""
## Task 2 — Random Forest Supervised Classification (25%)

**Goal:** 給定每類至少 50 個像素的訓練樣本，用 Random Forest 訓練多類別分類器，
產出**有命名的**土地覆蓋圖。

### 訓練樣本策略（Method A — geographic coords）

為了讓樣本與影像 grid 無關，我們用**經緯度**指定 ROI 中心，然後用一個小視窗
（半徑 r 個像素）擴展成 patch。這比手動選 row/col 更可重現。

| 類別 | ROI 中心 (lon,lat) | 半徑 | 選擇理由 |
|---|---|---|---|
| Water | (121.787, 24.165), (121.787, 24.215) | 5 | 太平洋外海，絕對純淨 |
| Forest | (121.55, 24.18), (121.60, 24.20), (121.50, 24.15) | 4 | 中央山脈密林 |
| Cropland | (121.66, 24.135), (121.65, 24.14) | 3 | 新城、北埔農地（沿台 9 線） |
| Bare/Landslide | (121.595, 24.175), (121.58, 24.19), (121.62, 24.165) | 3 | 太魯閣峽谷地震崩塌 |
| Built-up | (121.69, 24.13), (121.66, 24.13) | 3 | 新城、富世聚落 |
""")

code(r"""
from typing import List, Tuple
from pyproj import Transformer

# img_refl is on UTM 51N (EPSG:32651) grid — x,y are easting/northing in metres.
xs = img_refl['x'].values           # easting per column
ys = img_refl['y'].values           # northing per row (descending)
ll2utm = Transformer.from_crs(4326, 32651, always_xy=True)

def lonlat_to_rc(lon, lat):
    x, y = ll2utm.transform(lon, lat)
    col = int(np.argmin(np.abs(xs - x)))
    row = int(np.argmin(np.abs(ys - y)))
    return row, col

# Patch sampler: take a (2r+1)^2 window around (lon,lat), drop NaN pixels.
def patch_pixels(lon, lat, r, name):
    r0, c0 = lonlat_to_rc(lon, lat)
    rmin = max(0, r0 - r); rmax = min(h, r0 + r + 1)
    cmin = max(0, c0 - r); cmax = min(w, c0 + r + 1)
    patch = img_refl.values[:, rmin:rmax, cmin:cmax]   # (band, dy, dx)
    flat  = patch.reshape(n_bands, -1).T                # (n, 6)
    good  = ~np.isnan(flat).any(axis=1)
    flat  = flat[good]
    return flat, (r0, c0, rmin, rmax, cmin, cmax)

CLASS_NAMES = ['Water', 'Forest', 'Cropland', 'Bare/Landslide', 'Built-up']
CLASS_COLORS = ['#0077BE', '#228B22', '#DAA520', '#CD853F', '#808080']

# ROI definitions — (lon, lat, radius_in_pixels)
TRAINING_ROIS = {
    'Water':          [(121.787, 24.155, 6), (121.795, 24.210, 5), (121.790, 24.180, 6)],
    'Forest':         [(121.55, 24.18, 4), (121.60, 24.20, 4), (121.50, 24.155, 4),
                       (121.45, 24.22, 4), (121.58, 24.155, 4)],
    'Cropland':       [(121.660, 24.135, 3), (121.650, 24.140, 3),
                       (121.640, 24.145, 3), (121.670, 24.145, 3)],
    'Bare/Landslide': [(121.595, 24.175, 3), (121.580, 24.190, 3),
                       (121.620, 24.165, 3), (121.605, 24.185, 3),
                       (121.560, 24.195, 3)],
    'Built-up':       [(121.687, 24.130, 3), (121.660, 24.130, 3),
                       (121.677, 24.130, 3)],
}

train_X, train_y, roi_boxes = [], [], []
for class_id, cname in enumerate(CLASS_NAMES):
    n_for_class = 0
    for lon, lat, r in TRAINING_ROIS[cname]:
        flat, box = patch_pixels(lon, lat, r, cname)
        train_X.append(flat)
        train_y.append(np.full(len(flat), class_id))
        n_for_class += len(flat)
        roi_boxes.append((class_id, cname, box))
    print(f'{cname:<16} → {n_for_class} pixels')

X_train_full = np.vstack(train_X)
y_train_full = np.concatenate(train_y)
print(f'\nTotal training pixels: {len(X_train_full)}   (across {len(CLASS_NAMES)} classes)')
""")

code(r"""
# Visualise ROI locations on the false-colour quicklook
fig, ax = plt.subplots(figsize=(14, 6))
ax.imshow(rgb_false)
for class_id, cname, (r0, c0, rmin, rmax, cmin, cmax) in roi_boxes:
    rect = plt.Rectangle((cmin, rmin), cmax-cmin, rmax-rmin,
                         linewidth=1.5, edgecolor=CLASS_COLORS[class_id],
                         facecolor='none')
    ax.add_patch(rect)
# Legend
from matplotlib.patches import Patch
handles = [Patch(facecolor='none', edgecolor=c, label=n)
           for n, c in zip(CLASS_NAMES, CLASS_COLORS)]
ax.legend(handles=handles, loc='lower right')
ax.set_title('Training ROI locations on false-colour (NIR/R/G)')
ax.set_axis_off()
plt.tight_layout()
plt.savefig(OUTPUT_DIR/'Task2_training_rois.png', dpi=150, bbox_inches='tight')
plt.show()
""")

code(r"""
# Stratified 80/20 train/test split
X_tr, X_te, y_tr, y_te = train_test_split(
    X_train_full, y_train_full,
    test_size=0.2,
    random_state=RANDOM_STATE,
    stratify=y_train_full,
)
print(f'Train: {len(X_tr)}   Test: {len(X_te)}')

# Train Random Forest with OOB enabled
rf = RandomForestClassifier(
    n_estimators=RF_TREES,
    random_state=RANDOM_STATE,
    n_jobs=-1,
    oob_score=True,
    class_weight='balanced',          # helps with imbalanced classes
)
rf.fit(X_tr, y_tr)

print(f'Train acc : {rf.score(X_tr, y_tr):.4f}')
print(f'Test  acc : {rf.score(X_te, y_te):.4f}')
print(f'OOB   acc : {rf.oob_score_:.4f}')
""")

code(r"""
# Predict full image
t0 = time.time()
y_pred_all = rf.predict(X_valid)
class_map = np.full(h * w, np.nan)
class_map[valid] = y_pred_all
class_map = class_map.reshape(h, w)
print(f'Full-scene inference in {time.time()-t0:.1f}s')

# Class area summary
print('\n— Pixel counts —')
for i, name in enumerate(CLASS_NAMES):
    n = int(np.sum(class_map == i))
    pct = n / np.sum(~np.isnan(class_map)) * 100
    print(f'  {name:<16} {n:>9,}  ({pct:5.2f}%)')
""")

code(r"""
# Optional median filter (post-process salt-and-pepper)
from scipy.ndimage import median_filter
class_map_int = np.where(np.isnan(class_map), -1, class_map).astype(np.int8)
class_map_smooth = median_filter(class_map_int, size=3)
class_map_smooth = np.where(class_map_int < 0, np.nan, class_map_smooth)

cmap_rf = ListedColormap(CLASS_COLORS)

fig, axes = plt.subplots(1, 2, figsize=(18, 8))
axes[0].imshow(rgb_true); axes[0].set_axis_off()
axes[0].set_title('True-colour reference')

im = axes[1].imshow(class_map_smooth, cmap=cmap_rf, vmin=-0.5, vmax=len(CLASS_NAMES)-0.5)
axes[1].set_title(f'Random Forest classification (n_estimators={RF_TREES})')
axes[1].set_axis_off()
cbar = plt.colorbar(im, ax=axes[1], ticks=range(len(CLASS_NAMES)),
                    fraction=0.04, pad=0.02)
cbar.ax.set_yticklabels(CLASS_NAMES)
plt.tight_layout()
plt.savefig(OUTPUT_DIR/'rf_classification.png', dpi=150, bbox_inches='tight')
plt.show()
""")

code(r"""
# Feature importance
importance = rf.feature_importances_
order = np.argsort(importance)

fig, ax = plt.subplots(figsize=(8, 4))
ax.barh([f"{BANDS[i]} — {BAND_LABELS[BANDS[i]]}" for i in order],
        importance[order], color='steelblue')
ax.set_xlabel('Mean decrease in impurity')
ax.set_title('Random Forest — Band importance')
for i, v in enumerate(importance[order]):
    ax.text(v + 0.005, i, f'{v:.3f}', va='center')
plt.tight_layout()
plt.savefig(OUTPUT_DIR/'Task2_feature_importance.png', dpi=150, bbox_inches='tight')
plt.show()

for b, imp in sorted(zip(BANDS, importance), key=lambda x: -x[1]):
    print(f'  {b}  {BAND_LABELS[b]:<16}  importance = {imp:.4f}')
""")

md(r"""
### 💬 Task 2 Discussion

* **B08 (NIR) 與 B11 (SWIR1) 通常排名最前**——
  NIR 區分植被 vs 非植被，SWIR 區分水分含量、區分崩塌（乾燥裸地）vs 河床（含水）。
* **B02 (Blue) 對水體也很重要**——水的藍光反射率比其他類別高。
* 山區建物與崩塌**容易混淆**（兩者都低 NDVI、高反射率）——這是後續 Task 3
  外部驗證會放大顯示的問題。
""")

# ─────────────────────────────────────────────────────────────────────────────
# Task 3a — confusion matrix
# ─────────────────────────────────────────────────────────────────────────────
md(r"""
## Task 3 — Accuracy Assessment (35%)

### Part A — Internal Validation (Confusion Matrix + OOB + Macro/Weighted F1)
""")

code(r"""
y_pred_test = rf.predict(X_te)
cm = confusion_matrix(y_te, y_pred_test)

fig, ax = plt.subplots(figsize=(8, 7))
disp = ConfusionMatrixDisplay(cm, display_labels=CLASS_NAMES)
disp.plot(cmap='Blues', values_format='d', ax=ax, colorbar=False)
plt.xticks(rotation=30, ha='right')
ax.set_title('Random Forest — Test confusion matrix')
plt.tight_layout()
plt.savefig(OUTPUT_DIR/'confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.show()

print(classification_report(y_te, y_pred_test, target_names=CLASS_NAMES, digits=3))
""")

code(r"""
# OOB vs Test + macro/weighted F1 gap
from sklearn.metrics import f1_score, precision_recall_fscore_support
prec, rec, f1, supp = precision_recall_fscore_support(y_te, y_pred_test, average=None)
macro_f1    = f1_score(y_te, y_pred_test, average='macro')
weighted_f1 = f1_score(y_te, y_pred_test, average='weighted')

print(f'OOB accuracy      : {rf.oob_score_:.4f}')
print(f'Test accuracy     : {rf.score(X_te, y_te):.4f}')
print(f'Macro    F1       : {macro_f1:.4f}')
print(f'Weighted F1       : {weighted_f1:.4f}')
print(f'Gap (M-W)         : {macro_f1 - weighted_f1:+.4f}    (|gap|>0.03 → minority dilution)')

per_class = pd.DataFrame({
    'precision': prec.round(3),
    'recall':    rec.round(3),
    'f1':        f1.round(3),
    'support':   supp.astype(int),
}, index=CLASS_NAMES)
print('\n— Per-class metrics —')
print(per_class)
per_class.to_csv(OUTPUT_DIR/'Task3_per_class_metrics.csv')
""")

md(r"""
### 💬 Task 3 Part A — Why OOB ≈ Test, and why macro vs weighted matters

* OOB 與 Test accuracy 通常都會在 0.95+，因為訓練樣本都是「純粹中心點」、
  很乾淨，幾乎沒有混合像素 → 內部評估會**樂觀偏誤**。
* 如果 |Macro F1 − Weighted F1| > 0.03，代表少數類（Cropland、Built-up）被
  多數類（Forest、Water）「稀釋」——支援數 (support) 太少的類別不太可信。
""")

# ─────────────────────────────────────────────────────────────────────────────
# Task 3b — SWCB external validation
# ─────────────────────────────────────────────────────────────────────────────
md(r"""
### Part B — External Validation with SWCB Landslide Inventory

* 資料：`20240802新生崩塌地.kml` — 農業部水土保持署用高解析衛星判釋的
  地震後新生崩塌地多邊形。
* 與我們的 "Bare/Landslide" 類別（class_id=3）比對，計算 Recall / Precision / IoU。
""")

code(r"""
import xml.etree.ElementTree as ET
import geopandas as gpd
from shapely.geometry import Polygon, box
from rasterio.features import rasterize
from rasterio.transform import from_bounds

if not SWCB_KML.exists():
    print(f'⚠️  SWCB KML not found at {SWCB_KML}. Download from:')
    print('    https://drive.google.com/file/d/1VGe6ZY7QBCswqZEPRQaFWIJBylYK0qur/view')
    print('    and place it at the path above. The notebook continues without external validation.')
    SWCB_AVAILABLE = False
else:
    tree = ET.parse(SWCB_KML)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    polygons = []
    for pm in tree.getroot().findall('.//kml:Placemark', ns):
        coords_el = pm.find('.//kml:coordinates', ns)
        if coords_el is None or not coords_el.text:
            continue
        pts = []
        for token in coords_el.text.strip().split():
            parts = token.split(',')
            if len(parts) < 2: continue
            lon, lat = float(parts[0]), float(parts[1])
            pts.append((lon, lat))
        if len(pts) >= 3:
            polygons.append(Polygon(pts))
    gdf = gpd.GeoDataFrame(geometry=polygons, crs='EPSG:4326')
    print(f'SWCB landslide polygons (national): {len(gdf):,}')
    gdf_clip = gdf[gdf.intersects(box(*BBOX))].copy()
    # Re-project to the image grid (UTM 51N) so rasterize aligns 1:1
    gdf_clip_utm = gdf_clip.to_crs(epsg=32651)
    print(f'                  clipped to BBOX : {len(gdf_clip):,}')
    SWCB_AVAILABLE = True
""")

code(r"""
if SWCB_AVAILABLE:
    # Build the exact transform of the classification grid from xs/ys (UTM 51N)
    xmin, xmax = float(xs.min()), float(xs.max())
    ymin, ymax = float(ys.min()), float(ys.max())
    pixel_x = (xmax - xmin) / (w - 1)
    pixel_y = (ymax - ymin) / (h - 1)
    # Half-pixel padding so the extent matches pixel CENTRES used by stackstac
    west, east   = xmin - pixel_x / 2, xmax + pixel_x / 2
    south, north = ymin - pixel_y / 2, ymax + pixel_y / 2
    transform = from_bounds(west, south, east, north, w, h)

    swcb_mask = rasterize(
        [(g, 1) for g in gdf_clip_utm.geometry],
        out_shape=(h, w),
        transform=transform,
        fill=0,
        dtype='uint8',
        all_touched=True,
    )
    print(f'classification grid UTM extent : '
          f'x [{xmin:.0f}, {xmax:.0f}]  y [{ymin:.0f}, {ymax:.0f}]')
    print(f'SWCB landslide pixels in study area: {swcb_mask.sum():,}')
""")

code(r"""
if SWCB_AVAILABLE:
    # Our predicted "Bare/Landslide" pixels (class_id = 3)
    rf_landslide = (class_map == 3).astype('uint8')

    inter = int(np.sum((rf_landslide == 1) & (swcb_mask == 1)))
    only_rf = int(np.sum((rf_landslide == 1) & (swcb_mask == 0)))
    only_sw = int(np.sum((rf_landslide == 0) & (swcb_mask == 1)))

    recall    = inter / swcb_mask.sum() if swcb_mask.sum() else 0.0
    precision = inter / rf_landslide.sum() if rf_landslide.sum() else 0.0
    iou       = inter / (inter + only_rf + only_sw) if (inter+only_rf+only_sw) else 0.0
    f1_landslide = 2*precision*recall/(precision+recall) if (precision+recall) else 0.0

    print(f'TP (intersect)     : {inter:>9,}')
    print(f'FN (SWCB only)     : {only_sw:>9,}')
    print(f'FP (RF only)       : {only_rf:>9,}')
    print(f'Recall   (detection): {recall:.3f}')
    print(f'Precision           : {precision:.3f}')
    print(f'IoU (Jaccard)       : {iou:.3f}')
    print(f'F1                  : {f1_landslide:.3f}')

    swcb_metrics = {
        'tp': inter, 'fn': only_sw, 'fp': only_rf,
        'recall': round(recall, 4),
        'precision': round(precision, 4),
        'iou': round(iou, 4),
        'f1': round(f1_landslide, 4),
        'swcb_polygons_in_bbox': int(len(gdf_clip)),
        'swcb_pixels': int(swcb_mask.sum()),
        'rf_landslide_pixels': int(rf_landslide.sum()),
    }
else:
    swcb_metrics = {'note': 'SWCB KML not available — Task 3 Part B skipped'}
print(swcb_metrics)
""")

code(r"""
if SWCB_AVAILABLE:
    overlay = np.zeros((h, w, 3), dtype=np.uint8)
    overlay[(rf_landslide == 1) & (swcb_mask == 1)] = [0, 200, 0]    # TP green
    overlay[(rf_landslide == 0) & (swcb_mask == 1)] = [220, 0, 0]    # FN red
    overlay[(rf_landslide == 1) & (swcb_mask == 0)] = [240, 240, 0]  # FP yellow

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    axes[0].imshow(rgb_true); axes[0].set_axis_off()
    axes[0].set_title('Reference: true-colour')

    axes[1].imshow(overlay)
    axes[1].set_title(f'RF "Bare/Landslide" vs SWCB  (IoU={swcb_metrics["iou"]:.2f})')
    axes[1].set_axis_off()
    from matplotlib.patches import Patch
    legend = [Patch(color='green',  label=f'TP (n={swcb_metrics["tp"]:,})'),
              Patch(color='red',    label=f'FN (n={swcb_metrics["fn"]:,})'),
              Patch(color='yellow', label=f'FP (n={swcb_metrics["fp"]:,})')]
    axes[1].legend(handles=legend, loc='lower right', framealpha=0.85)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/'swcb_overlay.png', dpi=150, bbox_inches='tight')
    plt.show()
""")

md(r"""
### 💬 Task 3 Part B — Why overlap is imperfect & where FN cluster

1. **時間差（temporal gap）** — SWCB 用 2024-08-02 高解析影像判釋，
   而我們的 Sentinel-2 場景可能在 4–7 月之間。崩塌可能擴張（豪雨）或被植被重新覆蓋
   （快速復育）→ 兩個時間點的「真值」本來就不一樣。
2. **空間解析度差異** — Sentinel-2 是 20 m grid，SWCB 用的可能是 2 m WorldView；
   小於 20 m 的崩塌條紋會被邊緣效應吃掉 → **FN 集中在小型崩塌邊緣**。
3. **類別定義不同** — 我們把「裸地」和「崩塌」合併（一個類別），SWCB 只標
   「**新生**崩塌地」。河床、舊崩塌、岩盤裸露會被我們算成「Bare/Landslide」
   但不在 SWCB 多邊形內 → **FP 多半是河床與舊崩塌**。
4. **比較：內部 vs 外部 acc** — Test accuracy 通常 > 0.95，但 SWCB IoU
   往往只有 0.10–0.30。差距告訴我們**內部驗證高估了模型在真實世界的表現**。
""")

# ─────────────────────────────────────────────────────────────────────────────
# Task 4
# ─────────────────────────────────────────────────────────────────────────────
md(r"""
## Task 4 — AI Classification Report (25%)
""")

code(r"""
# Class area statistics
pixel_area_m2 = RESOLUTION * RESOLUTION
total_valid = int(np.sum(~np.isnan(class_map)))

records = []
for i, name in enumerate(CLASS_NAMES):
    n_pix = int(np.sum(class_map == i))
    records.append({
        'class_id'  : i,
        'class'     : name,
        'pixels'    : n_pix,
        'area_ha'   : round(n_pix * pixel_area_m2 / 1e4, 2),
        'area_km2'  : round(n_pix * pixel_area_m2 / 1e6, 3),
        'pct_of_scene': round(n_pix / total_valid * 100, 2),
    })
stats_df = pd.DataFrame(records)
print(stats_df.to_string(index=False))

stats_df.to_csv(OUTPUT_DIR/'class_area_stats.csv', index=False)
""")

code(r"""
# Persist consolidated metrics
import json
metrics = {
    'scene_id'   : best_item.id,
    'scene_date' : str(best_item.datetime.date()),
    'cloud_cover_pct': float(best_item.properties['eo:cloud_cover']),
    'bbox'       : BBOX,
    'resolution_m': RESOLUTION,
    'rf'         : {
        'n_estimators': RF_TREES,
        'oob_score'   : float(rf.oob_score_),
        'test_acc'    : float(rf.score(X_te, y_te)),
        'macro_f1'    : float(macro_f1),
        'weighted_f1' : float(weighted_f1),
        'feature_importance': dict(zip(BANDS, rf.feature_importances_.round(4).tolist())),
    },
    'swcb'       : swcb_metrics,
    'class_stats': records,
}
with open(OUTPUT_DIR/'aria_v8_metrics.json', 'w', encoding='utf-8') as f:
    json.dump(metrics, f, ensure_ascii=False, indent=2, default=str)
print('metrics persisted → output/aria_v8_metrics.json')
""")

code(r"""
# LLM commander's briefing
import google.generativeai as genai
api_key = os.getenv('GEMINI_API_KEY')
model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

iou_str = (f"{swcb_metrics['iou']:.2f}" if SWCB_AVAILABLE else 'N/A (SWCB data unavailable)')
recall_str = (f"{swcb_metrics['recall']:.2f}" if SWCB_AVAILABLE else 'N/A')
precision_str = (f"{swcb_metrics['precision']:.2f}" if SWCB_AVAILABLE else 'N/A')

prompt = f'''
你是花蓮縣災害應變中心的 GIS 分析師。根據以下災後土地覆蓋分類結果，
撰寫一份「災後土地覆蓋分析報告」（中文，300-500 字）。

研究區：秀林鄉 / 太魯閣周邊（含蘇花公路沿線及近海區域）
災害事件：2024 年 4 月 3 日花蓮地震（M7.4）
影像：Sentinel-2 L2A {best_item.datetime.date()}，雲量 {best_item.properties['eo:cloud_cover']:.1f}%
分類方法：Random Forest（6 波段、5 類別、{RF_TREES} 棵樹）
Overall accuracy: {rf.score(X_te, y_te):.1%}
OOB accuracy:     {rf.oob_score_:.1%}
Macro F1:         {macro_f1:.3f}
SWCB landslide 比對：Recall={recall_str}, Precision={precision_str}, IoU={iou_str}

各類別面積：
{stats_df.to_string(index=False)}

報告需包含：
1. 災後土地覆蓋概況（哪一類最多、占比、空間分布）
2. 崩塌/裸地面積估計及其空間分布（蘇花、太魯閣峽谷）
3. 與 SWCB 官方判釋的比對結果 + 不確定性說明（為何 IoU 不會是 1.0）
4. 建議：這張分類圖可以如何支援後續的避難所評估或路網分析？
請使用條列段落、適合給指揮官 1 分鐘速讀。
'''

if api_key and api_key not in {'', 'YOUR_GEMINI_API_KEY'}:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    report_text = response.text
    print(report_text)
else:
    report_text = '⚠️ GEMINI_API_KEY not configured. Please set it in `.env` and re-run.'
    print(report_text)

with open(OUTPUT_DIR/'Task4_AI_Briefing.md', 'w', encoding='utf-8') as f:
    f.write('# Task 4 — AI Commander Briefing\n\n')
    f.write(f'> Generated with {model_name} on {pd.Timestamp.now():%Y-%m-%d %H:%M}\n\n')
    f.write('## Prompt\n\n```\n' + prompt.strip() + '\n```\n\n')
    f.write('## LLM Output\n\n' + report_text + '\n')
""")

md(r"""
### 💬 Task 4 — Critical evaluation of the LLM output

**事實核對：**
* 面積數字 ✅ 直接讀自 `stats_df` → 沒有 hallucination 風險。
* IoU / Recall / Precision ✅ 直接 inject 進 prompt → 不會被模型亂編。
* **要警惕的：** LLM 可能會「補述」研究區的地名、災情描述、聚落名稱——
  這些**沒有在 prompt 裡的資訊**，可能是訓練資料的舊知識，需逐項驗證
  （例如它若聲稱「秀林鄉公所所在地受損」——這不在我的資料中）。

**改進建議：**
1. 在 prompt 加入「**未在資料中的事實請標註「[需查證]」**」instruction。
2. 把 SWCB 比對 IoU 偏低的「**原因**」也餵進 prompt（時間差、解析度差異），
   否則 LLM 會幫你「猜原因」。
3. 限制 LLM 不要對「具體地點」做結論，除非我們提供 lon/lat 座標。
""")

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
md(r"""
## [S99] Final Summary — Deliverable Checklist

| Deliverable | File |
|---|---|
| K-means classification map | `output/kmeans_classification.png` |
| K-means cluster spectra plot | `output/Task1_cluster_spectra.png` |
| K-means cluster mean table | `output/Task1_cluster_means.csv` |
| Random Forest classification map | `output/rf_classification.png` |
| Training ROI overview | `output/Task2_training_rois.png` |
| Feature importance bar chart | `output/Task2_feature_importance.png` |
| Confusion matrix heatmap | `output/confusion_matrix.png` |
| Per-class metrics | `output/Task3_per_class_metrics.csv` |
| SWCB overlay (TP/FN/FP) | `output/swcb_overlay.png` |
| Area statistics per class | `output/class_area_stats.csv` |
| AI briefing | `output/Task4_AI_Briefing.md` |
| Consolidated metrics | `output/aria_v8_metrics.json` |

## ARIA v8.0 — Upgrade Reflection

> **From thresholds to classifiers.**
> v7.0 用「VV < −16 dB」一刀切，回答**二元問題**「淹水嗎」。
> v8.0 用 6 維光譜空間 + 隨機森林，回答**多類問題**「這像素是什麼地物」。
> 真正的成本：不再是調參數，而是**準備乾淨的訓練資料**。
> Garbage in = garbage out — 任何 95% accuracy 的數字，都要拿 SWCB 那樣的
> 外部證據 cross-check，否則我們只是讓模型「記住了我們挑的訓練點」而已。
""")

# ─────────────────────────────────────────────────────────────────────────────
# write
# ─────────────────────────────────────────────────────────────────────────────
nb['cells'] = cells
nb['metadata'] = {
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python', 'version': '3.11'},
}

out_path = Path(__file__).parent / 'Week12_ARIA_v80_Homework.ipynb'
nbf.write(nb, out_path)
print(f'wrote → {out_path}  ({len(cells)} cells)')
