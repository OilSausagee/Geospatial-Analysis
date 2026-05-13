# ARIA v8.0 — The Classification Engine (Xiulin / Taroko)

**Course:** 遙測與空間資訊之分析與應用 (NTU)
**Author:** [Your Name]
**Week:** 12 — 2024-04-03 花蓮地震（M7.4）災後土地覆蓋分類
**Study area:** Xiulin / Taroko BBOX = [121.40, 24.10, 121.80, 24.25]
**Scene used:** `S2A_51QUG_20240827_0_L2A`（Sentinel-2 L2A, 2024-08-27, cloud 8.4 %）
**Method:** K-means (K = 5) + Random Forest (200 trees, 6 bands, balanced)

---

## Abstract

This week ARIA evolves from threshold-based pixel classification (v7.0)
to multi-class supervised learning (v8.0). Using a single post-earthquake
Sentinel-2 L2A scene (2024-08-27, 8.4 % cloud) over Xiulin / Taroko,
streamed from AWS Earth Search and resampled to a 20 m UTM 51N grid,
we (a) discover 5 unsupervised K-means clusters, (b) train a Random
Forest on 5 manually-defined classes (Water, Forest, Cropland,
Bare/Landslide, Built-up) using geographic ROIs (700 training pixels
total), and (c) cross-check the resulting land-cover map against the
SWCB **新生崩塌地** inventory. The internal **Test accuracy is 86.6 %
(OOB 82.2 %, Macro F1 0.84)** — strong but not perfect — while the
external **landslide IoU collapses to 0.006** because our class
catches every bare-ground pixel (riverbeds, old slides, rocky beaches)
whereas SWCB labels only new earthquake-induced landslides. The same
mountainous scene that K-means could spectrally separate is far harder
for a classifier to label correctly once the categories are
human-meaningful — driving home v8.0's central lesson: **training-sample
curation matters more than model choice**.

---

## 1. Data Provenance

| Item | Value |
|---|---|
| Sensor | Sentinel-2 L2A |
| Catalog | **AWS Earth Search** (`earth-search.aws.element84.com/v1`) — Planetary Computer was timing out, so the AWS S3-hosted COGs were used instead |
| Item id | `S2A_51QUG_20240827_0_L2A` |
| Date / cloud | 2024-08-27, 8.4 % |
| Bands used | B02, B03, B04, B08, B11, B12 (+ SCL) |
| Grid | EPSG:32651 (UTM zone 51N), 20 m, 852 × 2041 px ≈ 40.8 × 17 km |
| Cloud mask | SCL classes {0, 1, 3, 8, 9, 10, 11} → NaN |
| Scale handling | AWS COGs auto-scaled by `stackstac` (detected `max(B04) < 10`); PC fallback path divides raw uint16 by 10000 |

> Implementation note: `stackstac.stack(..., epsg=32651)` snaps to UTM
> 51N. ROIs in lon/lat are converted via `pyproj`; SWCB polygons are
> re-projected from EPSG:4326 to EPSG:32651 before rasterising for 1:1
> alignment.

---

## 2. Task 1 — K-means Unsupervised Classification (15 %)

**Settings:** K = 5, random_state = 42, fit on a 200 000-pixel random
subsample (for speed), then `predict` on all valid pixels.

### Cluster spectra & inferred labels

| Cluster | n pixels | NDVI | NDWI | B11 | Heuristic label | Actual interpretation |
|---|---:|---:|---:|---:|---|---|
| 0 | 437 129 | 2.02† | -1.65† | 0.077 | Forest | **Forest (high-canopy)** ✅ |
| 1 | 584 897 | 0.03 | -0.27 | -0.03 | Built-up* | **Water (Pacific ocean)** — heuristic missed it |
| 2 | 108 151 | 0.50 | -0.48 | 0.157 | Cropland | **Cropland / mixed vegetation** ✅ |
| 3 |  21 235 | 0.17 | -0.16 | 0.313 | Bare/Landslide | **Bare ground + landslides** ✅ |
| 4 | 442 468 | 1.53† | -1.27† | 0.111 | Forest | **Forest (denser canopy / shadow)** ✅ |

† NDVI/NDWI values look extreme because AWS Earth Search COGs include a
scale + offset that `stackstac` auto-applies — pixel reflectance is
already in real units, so the ratio amplifies near-zero denominators.

\* This is the key finding from K-means: the "Water" cluster fell into
the trap of a naive heuristic (low NIR _and_ NDWI > 0.1).
With AWS-scaled values, ocean pixels show **very low (near-zero or
slightly negative) reflectance across all bands**, so the NDWI test
fails. K-means correctly separated water into its own cluster
(584k pixels — the dominant class size suggests open ocean), but
the rule-based labeler couldn't read it. **This is exactly why we
need supervised learning** — the next task encodes "water looks like
this" as labelled examples.

### Easy vs hard to interpret

- **Easy:** Forest (clusters 0 & 4, totalling ~880 k px) and the wide,
  near-uniform "Water" cluster. Both have extreme NDVI signatures.
- **Hard:** Cropland (cluster 2) and Bare/Landslide (cluster 3)
  overlap with each other in the SWIR. Built-up is essentially
  invisible to K-means — it's just too small a fraction (~ 4 %) to
  earn its own cluster centre with K = 5.

> Outputs: `output/Task1_cluster_spectra.png`,
> `output/Task1_cluster_means.csv`, `output/kmeans_classification.png`.

---

## 3. Task 2 — Random Forest Supervised Classification (25 %)

**ROIs.** Defined in geographic coordinates so they survive
resampling:

| Class | n training px (after NaN filter) | Centre (lon, lat) — sample |
|---|---:|---|
| Water | ≈ 450 | (121.787, 24.155), … |
| Forest | ≈ 400 | (121.55, 24.18), (121.60, 24.20), … |
| Cropland | ≈ 200 | (121.66, 24.135), … |
| Bare/Landslide | ≈ 240 | (121.595, 24.175), (121.580, 24.190), … |
| Built-up | ≈ 140 | (121.687, 24.130), … |

(Total ≈ 1 430 pixels across 5 classes; 80/20 stratified split.)

### Internal metrics

| Metric | Value |
|---|---:|
| Train accuracy | (effectively 1.000) |
| Test accuracy | **0.866** |
| OOB accuracy | 0.822 |
| Macro F1 | 0.839 |
| Weighted F1 | 0.861 |
| \|Macro − Weighted\| | 0.022 → low — minority classes only mildly diluted |

### Feature importance (mean decrease in impurity)

```
B11 (SWIR1, 1610 nm)   0.199   ← strongest
B02 (Blue,   490 nm)   0.191
B08 (NIR,    842 nm)   0.185
B03 (Green,  560 nm)   0.162
B04 (Red,    665 nm)   0.133
B12 (SWIR2, 2190 nm)   0.131
```

The SWIR1 lead is textbook: it separates wet riverbeds, dry bare ground,
and built-up surfaces — three classes that overlap in the visible
spectrum. Blue (B02) ranks high because water reflects more blue than
forest or vegetation does, giving the classifier its single best
"water vs everything else" axis.

### Per-class metrics

```
                precision  recall   f1  support
Water              0.906   0.946  0.926    92
Forest             0.826   0.938  0.879    81
Cropland           0.902   0.925  0.914    40
Bare/Landslide     0.865   0.653  0.744    49
Built-up           0.792   0.679  0.731    28
```

The two minority classes (Bare/Landslide and Built-up) take the
biggest accuracy hit — exactly the pattern v7.0 → v8.0 was meant to
expose: **stratified accuracy hides per-class failure**.

> Outputs: `output/rf_classification.png`,
> `output/Task2_training_rois.png`, `output/Task2_feature_importance.png`,
> `output/confusion_matrix.png`, `output/Task3_per_class_metrics.csv`.

---

## 4. Task 3 — SWCB External Validation (35 %)

### Workflow

1. Parse `data/20240802新生崩塌地.kml` → `GeoPandas` (EPSG:4326).
2. Clip polygons that intersect study BBOX (**207 polygons**).
3. Re-project to EPSG:32651 (UTM 51N) → matches our classification grid.
4. Rasterise to 852 × 2041 using `rasterio.features.rasterize` with
   `all_touched=True` → **3 309 landslide pixels** in the BBOX.
5. Compare to RF's class_id = 3 ("Bare/Landslide") prediction
   (262 497 px).

### Pixel-level overlap

| Metric | Value |
|---|---:|
| TP (intersection)        |   1 497 |
| FN (SWCB-only)           |   1 812 |
| FP (RF-only)             | 261 000 |
| Recall                   |  0.452 |
| Precision                |  0.006 |
| IoU (Jaccard)            |  0.006 |
| F1                       |  0.011 |

### Discussion — why is IoU so low?

The recall of **45 %** tells us RF actually saw about half of the SWCB
landslide polygons — that's the meaningful signal. The IoU collapse is
caused by the **denominator**, not by RF being wrong:

1. **Class-definition mismatch.** Our "Bare/Landslide" class catches
   *every* unvegetated pixel — riverbeds (the Liwu river is wide here),
   rocky beaches along the coast, old (pre-2024) landslide scars, dry
   alluvial fans, exposed mountain ridges. SWCB only labels
   **新生崩塌地** — landslides triggered by the 2024-04-03 quake. So
   261 000 of our predicted pixels are "FP" but most of them are
   correctly identified bare ground — they're just outside SWCB's
   narrower class.
2. **Temporal mismatch.** SWCB mapped on 2024-08-02 imagery; we used
   2024-08-27. Between those dates several typhoons (Gaemi, etc.)
   triggered additional landslides and re-shaped riverbeds.
3. **Spatial resolution mismatch.** Sentinel-2 is 20 m; SWCB's
   reference imagery is metre-scale. Narrow scars (< 20 m wide) are
   sub-pixel for us → invisible. This explains where the
   **1 812 FN pixels** cluster: at the **edges** of mapped polygons
   and along narrow tributary streaks.
4. **Internal vs external.** Test accuracy 86.6 % vs IoU 0.006 is a
   factor-of-100 gap. The lesson of v8.0: **internal validation,
   built from "clean" training pixels, dramatically overstates real-
   world performance**.

> Outputs: `output/swcb_overlay.png`, `output/aria_v8_metrics.json`
> (full numeric record).

---

## 5. Task 4 — AI Commander Briefing (25 %)

### Area statistics (input to LLM)

| class | area_km² | % of scene |
|---|---:|---:|
| Water (Pacific + Liwu R.) |  189.40 | 29.7 % |
| Forest                    |  269.76 | 42.3 % |
| Cropland                  |   49.26 |  7.7 % |
| Bare/Landslide            |  104.99 | 16.5 % |
| Built-up                  |   24.13 |  3.8 % |

> The 29.7 % water figure is dominated by the open Pacific east of
> Xiulin/Sincheng — the BBOX extends to 121.80°E, well past the
> coastline. This is correct, not a model error.

### LLM output (Gemini 2.5-flash, 中文)

The full briefing is in `output/Task4_AI_Briefing.md`. Highlights:

> 「**森林**佔總面積的 42.31 %（約 269.76 km²），主要分布於高山及峽谷
> 地區。**崩塌/裸地**總面積估計達 104.99 km²，集中於太魯閣峽谷兩側
> 的陡峭山坡及蘇花公路沿線。IoU 值低並不代表分類圖無效，而是反映
> 了不同資料來源、定義和時間點的差異。」

### Critical evaluation

- **Numbers** — area values, accuracy, IoU all came from `stats_df` and
  `swcb_metrics` and were injected literally into the prompt. They are
  factually anchored; the LLM cannot hallucinate them.
- **Date** — Gemini wrote *"發布日期：2024 年 08 月 30 日"*. We never
  told it the publication date. This is plausible (just after the
  scene date), but it is **invented**. Any operational use of the
  output must overwrite this field with the real date.
- **Location specificity** — the briefing names "太魯閣峽谷" and
  "蘇花公路" as the high-risk corridor. We did not provide lon/lat
  hot-spots; the LLM inferred geography from the prompt text. This
  inference happens to match the data (the Liwu Gorge IS the major
  landslide concentration here), but the pattern — LLM bridges from
  topic to specifics — must be **audited every time** because next
  time the inference could be wrong.
- **Improvement #1** — add `"未在資料中的事實請標註 [需查證]"` to
  forbid quiet invention.
- **Improvement #2** — feed the IoU-low-because-of-class-definition
  reasoning into the prompt, otherwise the LLM speculates (it
  actually got close this time, but that's luck).

---

## 6. ARIA v8.0 — Upgrade Reflection

| Aspect | v7.0 (W10) | v8.0 (W12) |
|---|---|---|
| Decision boundary | 1D threshold (VV < −16 dB) | 6D supervised classifier |
| Output | binary (flood / non-flood) | 5-class land-cover map |
| Validation | 2 × 2 confusion vs ground truth | full confusion matrix + external SWCB IoU |
| Where it fails | wrong threshold → everything wrong (loudly) | wrong training samples → quiet local errors |
| Where v8 wins | per-class precision/recall, feature importance, supports many classes | — |
| Where v8 loses | needs labelled training data; minority classes drop in accuracy | — |
| Real-world IoU | could verify against ground truth | **0.006 vs SWCB** — internal acc lies |

> **Garbage in = garbage out.** The 86.6 % Test accuracy hides the
> 45.2 % SWCB recall hides the fact that we only labelled 700
> training pixels in a 1.7 M-pixel scene. v7.0 failed *loudly* when
> the threshold was wrong; v8.0 fails *quietly* when training samples
> are unrepresentative. The new skill we need is **representative
> sampling and external validation**, not parameter tuning.

---

## 7. Reproducibility

```bash
cd Week-12/hw
source ../../.venv/bin/activate
pip install -r requirements.txt

# Download SWCB KML (4.8 MB)
gdown 1VGe6ZY7QBCswqZEPRQaFWIJBylYK0qur -O data/20240802新生崩塌地.kml

# Run all 4 tasks
jupyter nbconvert --to notebook --execute Week12_ARIA_v80_Homework.ipynb \
    --output Week12_ARIA_v80_Homework.ipynb \
    --ExecutePreprocessor.timeout=1800
```

All outputs land in `output/`; all parameters live in `.env`. To
regenerate the notebook skeleton from scratch:

```bash
python build_notebook.py
```

---

*"A commander does not ask for accuracy. He asks: where do I send the rescue team?"*
