# Week 8 Pre-lab: STAC API & Sentinel-2 Cloud-Native Workflow

> Please complete the following steps **before class** to ensure your environment is ready.
> Estimated time: 20–30 minutes
> Goal: Enter Week 8 with the ability to **search, preview, and stream** Sentinel-2 imagery — no bulk downloads — and witness the 2025 **Matai'an Creek barrier lake event（馬太鞍溪堰塞湖事件）** through your own code.

---

## Why This Matters (Captain's Intuition)

From Week 3 to Week 7, ARIA only knew what the **models** predicted.
Starting Week 8, ARIA gains **eyes in the sky** — satellite imagery that *witnesses* what actually happened on the ground.

Our case study this week is the most consequential 2025 disaster in Hualien County: the **Matai'an Creek barrier lake（馬太鞍溪堰塞湖）**. The timeline reads like a three-act drama, and every act leaves a fingerprint that **visible-light imagery can show you at a glance**:

| Act | Date | Event | What you will see in TCI |
|---|---|---|---|
| **Pre** | Jun 2025 | Typhoon Wipha has not yet struck. Original mountain forest. | Dense green forested valley |
| **Mid** | Aug 2025 | Typhoon Wipha's heavy rainfall (Jul 21) triggers a massive landslide in upper Wanrong. Debris blocks the Matai'an River and forms a **~200 m deep barrier lake**. | A brand new turquoise water body sitting in what used to be a forest |
| **Post** | Oct 2025 | On Sep 23, 14:50, the lake overtops and releases **15.4 million m³ in 30 minutes**. The Matai'an River bridge on Highway 9 collapses; downstream Guangfu township is buried in mud. 18+ fatalities. | The lake is gone. Guangfu town shows fresh sediment deposits and structural damage. |

The beauty of this case for remote sensing: **you do not need a single band math equation to see the story.** Just load the True Color Image for each of the three dates and your eyes do the work. Band math then *quantifies* what your eyes already know.

But there is a catch: a single Sentinel-2 tile is 600–800 MB, and each of our three scenes is covered by 2 tiles. Downloading a full time series would melt your laptop.

The modern workflow is **cloud-native**:
- Query a **STAC (SpatioTemporal Asset Catalog)** to find scenes
- Preview with the built-in **TCI (True Color Image)** thumbnail
- Stream only the bands and pixels you need via `stackstac` + `rioxarray`

This is what the remote-sensing industry calls the "**glass-box protocol**" — you never hold the whole asset, you just look through it.

---

## Step 1: Install New Packages

```bash
# Activate your virtual environment first
# macOS / Linux:
source gis-env/bin/activate
# Windows:
gis-env\Scripts\activate

# Core STAC + cloud-native raster stack
pip install pystac-client planetary-computer stackstac rioxarray

# Optional but recommended for interactive preview
pip install leafmap odc-stac
```

Verify installation:

```python
import pystac_client
import planetary_computer
import stackstac
import rioxarray
import xarray as xr
print(f"pystac-client: {pystac_client.__version__}")
print(f"stackstac:      {stackstac.__version__}")
print(f"rioxarray:      {rioxarray.__version__}")
print("✅ All Week 8 packages ready!")
```

> **Note**: `stackstac` depends on `dask` and `xarray`. If you installed `geopandas` cleanly in Week 6, the dependency chain should resolve in one pass. Windows users sometimes need `pip install --upgrade pip` first.

---

## Step 2: What is STAC? (The Glass-Box Protocol)

**STAC (SpatioTemporal Asset Catalog)** is a JSON-based standard for describing geospatial data. Every STAC item has:

- **Geometry** — the footprint of the scene
- **Datetime** — when it was captured
- **Properties** — cloud cover (`eo:cloud_cover`), platform, etc.
- **Assets** — URLs to individual bands (B02, B03, B04, B08, B11, B12, ...) and the built-in TCI preview

The magic: these URLs are **Cloud-Optimized GeoTIFFs (COG)**. You can read a single 256×256 tile from a 10,000×10,000 image without downloading the whole thing.

---

## Step 3: First STAC Query — Find the Pre-Event Baseline Scene

Our area of interest this week is the **upper Matai'an catchment + Guangfu township（馬太鞍溪上游至光復鄉）**, about 30 km south of Hualien City. This one bbox will cover all three acts of the story.

```python
import pystac_client
import planetary_computer as pc

# Connect to Microsoft Planetary Computer STAC
catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=pc.sign_inplace,
)

# Matai'an catchment bbox (lon_min, lat_min, lon_max, lat_max)
# Covers upper Wanrong barrier lake site → downstream Guangfu township
mataian_bbox = [121.28, 23.56, 121.52, 23.76]

# ACT 1: Pre-event baseline — before Typhoon Wipha (Jul 21, 2025)
search_pre = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=mataian_bbox,
    datetime="2025-06-01/2025-07-15",
    query={"eo:cloud_cover": {"lt": 20}},
)

items_pre = search_pre.item_collection()
print(f"Pre-event (Jun–early Jul 2025): {len(items_pre)} clean scenes")
for item in items_pre[:5]:
    print(f"  {item.id} | clouds={item.properties['eo:cloud_cover']:.1f}%")
```

Expected output: 2–6 items, each with cloud cover < 20%. June is one of the clearest windows in Hualien's pre-monsoon season — you should have no trouble finding a clean baseline.

> **Troubleshooting**:
> - If you get `SSL: CERTIFICATE_VERIFY_FAILED`, upgrade `certifi`: `pip install --upgrade certifi`
> - If `items_pre` is empty, widen the window to `"2025-05-15/2025-07-20"` — pre-monsoon Hualien is usually clear

Now try the Mid-event window (lake has formed but not yet breached):

```python
# ACT 2: Mid-event — lake is present, NOT yet breached (pre Sep 23)
search_mid = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=mataian_bbox,
    datetime="2025-08-01/2025-09-20",
    query={"eo:cloud_cover": {"lt": 40}},   # Aug/Sep is monsoon — relax clouds
)
items_mid = search_mid.item_collection()
print(f"Mid-event (Aug–mid Sep 2025): {len(items_mid)} usable scenes")
```

And the Post-event window (after the Sep 23 breach):

```python
# ACT 3: Post-event — lake gone, Guangfu buried
search_post = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=mataian_bbox,
    datetime="2025-09-25/2025-11-15",
    query={"eo:cloud_cover": {"lt": 30}},
)
items_post = search_post.item_collection()
print(f"Post-event (late Sep–Nov 2025): {len(items_post)} usable scenes")
```

> **Reality check**: August–September is Taiwan's monsoon and typhoon season. You may need to relax `eo:cloud_cover` to `{"lt": 50}` for the Mid-event window. That is completely normal and is exactly why **TCI Quick-QA (Step 4)** exists.

---

## Step 4: TCI Quick QA — Preview Before You Commit

Sentinel-2 L2A products ship with a built-in **TCI (True Color Image)** asset. This is a pre-computed RGB thumbnail that loads in under 2 seconds. Use it as a **visual firewall**: if the TCI shows a cloud wall over the Matai'an valley, skip the scene before wasting compute on band math.

```python
import rioxarray as rxr
import matplotlib.pyplot as plt

# Pick the least-cloudy Pre-event item as our baseline
best_pre = min(items_pre, key=lambda i: i.properties["eo:cloud_cover"])
print(f"Baseline scene: {best_pre.id} ({best_pre.properties['eo:cloud_cover']:.1f}% clouds)")

# Stream the TCI asset (True Color preview)
tci_href = best_pre.assets["visual"].href   # 'visual' == TCI on Planetary Computer
tci = rxr.open_rasterio(tci_href, overview_level=3)   # overview = low-res preview
print(f"TCI shape: {tci.shape}, CRS: {tci.rio.crs}")

# Plot
fig, ax = plt.subplots(figsize=(8, 8))
tci.plot.imshow(ax=ax)
ax.set_title(f"TCI Preview — {best_pre.id[:25]} (Pre-event)")
plt.show()
```

If the preview looks usable (Matai'an valley visible, not 100% cloud), proceed to Step 5. The Mid-event and Post-event scenes are what you will be comparing this baseline against during Lab 2.

> **Captain's Rule**: **Always TCI-preview before band math.** 80% of failed lab exercises come from picking a cloudy scene and then wondering why every NDVI is NaN. With the Matai'an case this rule matters even more — the event window is right in the middle of typhoon season.

---

## Step 5: Test Band Streaming (stackstac)

```python
import stackstac

# Stream only the bands we need (not the whole 12-band cube)
wanted_bands = ["B02", "B03", "B04", "B08", "B11", "B12"]

cube = stackstac.stack(
    [best_pre],
    assets=wanted_bands,
    epsg=32651,             # UTM 51N — Taiwan east coast
    resolution=10,          # upsample 20m SWIR to 10m for uniform grid
    bounds_latlon=mataian_bbox,
    chunksize=2048,
)

print(f"Cube dims: {dict(cube.sizes)}")
print(f"Bands: {list(cube.band.values)}")
print("✅ STAC streaming works — ready for Week 8")
```

You should see a lazy `xarray.DataArray` with shape `(1, 6, H, W)` (time × band × row × col). No data has been downloaded yet — that only happens when you call `.compute()` or plot a sub-region.

---

## Step 6: Update Your `.env` File

Add Week 8 settings to your project's `.env`:

```
# Week 8 additions — Remote Sensing (STAC + Sentinel-2)
STAC_ENDPOINT=https://planetarycomputer.microsoft.com/api/stac/v1
S2_COLLECTION=sentinel-2-l2a
S2_CLOUD_MAX=20
S2_BANDS=B02,B03,B04,B08,B11,B12

# Matai'an catchment focus area (lon_min, lat_min, lon_max, lat_max)
MATAIAN_BBOX=121.28,23.56,121.52,23.76
TARGET_EPSG=32651

# Matai'an barrier lake three-act window
PRE_EVENT_START=2025-06-01
PRE_EVENT_END=2025-07-15
MID_EVENT_START=2025-08-01
MID_EVENT_END=2025-09-20
POST_EVENT_START=2025-09-25
POST_EVENT_END=2025-11-15

# AI Advisor (Week 8 Cell [20], optional)
AI_API_KEY=your-api-key-here   # ChatGPT / Gemini / Claude — pick any

# Keep previous settings
CWA_API_KEY=CWA-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
APP_MODE=SIMULATION
SIMULATION_DATA=data/scenarios/mataian_202509.json
PROJECT_CRS=3826
TARGET_COUNTY=花蓮縣
```

> **Note on CRS**: Week 7 used EPSG:3826 (TWD97 meters) for road networks. Week 8 introduces EPSG:32651 (UTM 51N) for Sentinel-2 — this matches the native Sentinel-2 grid over Taiwan and avoids resampling artifacts. We will reproject to 3826 only when overlaying W3/W7 vectors.

---

## Step 7: Prepare Week 3 & 7 Outputs (+ Build Your Own Guangfu Overlay)

Week 8 will cross-reference satellite findings with your earlier ARIA layers **and** a new Guangfu township layer that you will build yourself as part of this pre-lab.

**Existing files to have ready (from previous weeks)**:

- **`shelters_hualien.gpkg`** (W3) — Hualien City shelter locations with `river_risk` / `terrain_risk`
- **`hualien_network.graphml`** (W7) — Hualien City road network
- **`top5_bottlenecks.gpkg`** (W7 Assignment) — your Top-5 high-centrality nodes

Make sure these three files are accessible in your working directory. **W8 extends the ARIA system southward** — you keep your Hualien City work untouched, and now add a Guangfu township layer on top. This is exactly how real-world DRR systems grow: you never throw away old coverage, you just extend.

> **If you did not finish the W7 assignment**: The teacher will provide a reference `top5_bottlenecks.gpkg` — you can still complete W8 Lab 2. But you will get more insight if you use your own results.

---

### 🛠️ Step 7b: Build `guangfu_overlay.gpkg` Yourself (Required)

This is a **required pre-lab deliverable**. W3/W7 covered Hualien City, but the Matai'an breach buried **Guangfu township**, ~30 km to the south. The existing ARIA vector layers simply do not have any nodes down there. Rather than have the teacher hand you a pre-built file, you are going to build the minimal `guangfu_overlay.gpkg` yourself — this is a 5-minute exercise that mirrors what a real DRR engineer does when their SOP layers don't match a new disaster zone.

**Why build it yourself?**
In Lab 2 you will see that spatial joining satellite findings with `shelters_hualien.gpkg` returns essentially zero hits. That's not a bug — it's the whole teaching point: **your SOP vector layers and your eyes in the sky are reporting different geographies, and when that happens, you trust the eyes and extend the layers**. Building this overlay is the "extending" half of that lesson.

**Required schema** (5 columns, 5 points minimum):

| column | type | description |
|---|---|---|
| `name` | str | English identifier, e.g. `Guangfu_Station` |
| `cn_name` | str | Chinese name, e.g. `光復火車站` |
| `node_type` | str | one of `shelter`, `critical_infra`, `bridge` |
| `priority` | int | 1 = highest (life-safety), 5 = lowest |
| `geometry` | Point | EPSG:4326 input, save as EPSG:3826 |

**Required nodes** (these are the five the Demo notebook expects):

| name | cn_name | node_type | priority | lon | lat |
|---|---|---|---|---|---|
| `Guangfu_Station` | 光復火車站 | critical_infra | 2 | 121.4235 | 23.6719 |
| `Guangfu_Elementary` | 光復國小 | shelter | 1 | 121.4240 | 23.6688 |
| `Guangfu_Township_Office` | 光復鄉公所 | shelter | 1 | 121.4210 | 23.6684 |
| `Mataian_Hwy9_Bridge` | 台9線馬太鞍溪橋 | bridge | 1 | 121.4100 | 23.6380 |
| `Foxu_Debris_Zone` | 佛祖街沉積區中心 | critical_infra | 3 | 121.4260 | 23.6640 |

**Starter code** (complete the `# TODO` lines yourself):

```python
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path

# --- 1. Build the in-memory GeoDataFrame ---
rows = [
    {"name": "Guangfu_Station",        "cn_name": "光復火車站",        "node_type": "critical_infra", "priority": 2, "lon": 121.4235, "lat": 23.6719},
    {"name": "Guangfu_Elementary",     "cn_name": "光復國小",          "node_type": "shelter",        "priority": 1, "lon": 121.4240, "lat": 23.6688},
    {"name": "Guangfu_Township_Office","cn_name": "光復鄉公所",        "node_type": "shelter",        "priority": 1, "lon": 121.4210, "lat": 23.6684},
    {"name": "Mataian_Hwy9_Bridge",    "cn_name": "台9線馬太鞍溪橋",   "node_type": "bridge",         "priority": 1, "lon": 121.4100, "lat": 23.6380},
    {"name": "Foxu_Debris_Zone",       "cn_name": "佛祖街沉積區中心",  "node_type": "critical_infra", "priority": 3, "lon": 121.4260, "lat": 23.6640},
]

# TODO 1: Convert `rows` into a GeoDataFrame.
#   - geometry column should be built with Point(lon, lat)
#   - initial CRS is EPSG:4326 (WGS84 lon/lat)

gdf = gpd.GeoDataFrame(
    rows,
    geometry=[Point(r["lon"], r["lat"]) for r in rows],
    crs="EPSG:4326",
).drop(columns=["lon", "lat"])

# TODO 2: Reproject to EPSG:3826 (TWD97 / TM2 — Taiwan official)
gdf_3826 = gdf.to_crs("EPSG:3826")

# TODO 3: Ensure the output folder exists
out_path = Path("data/guangfu_overlay.gpkg")
out_path.parent.mkdir(parents=True, exist_ok=True)

# TODO 4: Save as GeoPackage, driver="GPKG", layer="guangfu"
gdf_3826.to_file(out_path, driver="GPKG", layer="guangfu")

print(f"✅ Saved {len(gdf_3826)} nodes → {out_path}")
print(gdf_3826[["name", "cn_name", "node_type", "priority"]])
```

**Verification** (run after the script above):

```python
# Verify the file is readable and the schema is correct
check = gpd.read_file("data/guangfu_overlay.gpkg", layer="guangfu")
assert len(check) == 5,               f"Expected 5 rows, got {len(check)}"
assert check.crs.to_epsg() == 3826,   f"Expected EPSG:3826, got {check.crs}"
assert set(check["node_type"]) == {"shelter", "critical_infra", "bridge"}, \
       "node_type must include all three categories"
print("✅ guangfu_overlay.gpkg passes all schema checks")
```

Expected output:

```
✅ Saved 5 nodes → data/guangfu_overlay.gpkg
                    name          cn_name       node_type  priority
0        Guangfu_Station      光復火車站  critical_infra         2
1    Guangfu_Elementary          光復國小         shelter         1
2 Guangfu_Township_Office        光復鄉公所         shelter         1
3    Mataian_Hwy9_Bridge  台9線馬太鞍溪橋          bridge         1
4       Foxu_Debris_Zone   佛祖街沉積區中心  critical_infra         3
✅ guangfu_overlay.gpkg passes all schema checks
```

> **Safety net**: The Demo notebook's Cell [17] has a `try/except` that will still run even if `guangfu_overlay.gpkg` is missing — it will generate synthetic fallback nodes automatically. That's there so a single misplaced file can't brick the entire Lab 2. But **if you want full credit on Homework Part D, you must have your own real `guangfu_overlay.gpkg`** — the fallback is for robustness, not for skipping the exercise.

> **Optional bonus**: Add 2–3 more nodes of your own choosing (e.g., 光復國中, 光復醫院, 大富火車站). Just make sure they fall inside `MATAIAN_BBOX`. Document them in your Pre-lab submission notebook.

---

## Step 8 (Optional): Review Key Concepts

Make sure you are comfortable with:

- **Electromagnetic spectrum（電磁頻譜）**: Visible, NIR, SWIR — and why each band sees a different physical property
- **Spectral signature（光譜指紋）**: Water, vegetation, bare soil, burned area — each has a unique curve
- **Digital Number vs. Reflectance**: Why Sentinel-2 L2A is already atmospherically corrected (0.0–1.0 surface reflectance)
- **Cloud-Optimized GeoTIFF (COG)**: How overview pyramids let you stream sub-regions
- **xarray DataArray**: The labeled N-D array that drives modern raster workflows
- **W3–W7 ARIA outputs**: Shelters, terrain risk, rainfall, road bottlenecks — all will meet their "ground truth" this week

---

## Troubleshooting

**Q: `pystac_client` import fails with "No module named 'pystac_client'"?**
A: Reactivate your virtual environment and run `pip install --upgrade pystac-client`. Note the **underscore** in the package name.

**Q: STAC search returns 0 items even for wide date ranges?**
A: Check your bbox order — it must be `(lon_min, lat_min, lon_max, lat_max)`. A common mistake is swapping lat/lon.

**Q: `planetary_computer.sign_inplace` raises a 403?**
A: Planetary Computer is free but rate-limited. If you get 403 errors, wait 30 seconds and retry. No API key is needed.

**Q: `stackstac.stack()` is extremely slow?**
A: You probably forgot `bounds_latlon=` and are computing the full Sentinel-2 tile (10,980×10,980). Always pass a bbox to restrict the region.

**Q: `rioxarray.open_rasterio()` returns all NaN?**
A: The scene is probably 100% cloud. Revisit the TCI preview — if it looks white, pick a different item.

**Q: The Mid-event window (Aug–Sep 2025) returns 0 clean scenes?**
A: This is expected — it is peak monsoon and typhoon season. Relax `eo:cloud_cover` to `{"lt": 50}` and then use the TCI Quick-QA to hand-pick the least cloudy scene over the Matai'an catchment specifically. Sometimes the cloud cover is concentrated elsewhere in the tile and our small bbox is actually clear.

**Q: My laptop only has 8 GB RAM — will stackstac crash?**
A: No, as long as you pass `bounds_latlon=mataian_bbox` and don't call `.compute()` on the full cube. Only small spatial windows materialize in memory.

**Q: Can I use Google Earth Engine instead of Planetary Computer?**
A: Yes, but GEE requires a separate authentication flow and is better suited for Week 14's long-term trend analysis. For Week 8 we standardize on Planetary Computer to keep the entry barrier low.

**Q: What is "TCI" exactly?**
A: TCI = True Color Image. Sentinel-2 L2A products ship with a pre-computed 8-bit RGB JPEG-compressed overview (B4-B3-B2, stretched). On Planetary Computer it lives under `item.assets["visual"]`. It's the fastest way to eyeball cloud conditions.

---

*"A STAC catalog is a library card — you don't carry the books home, you read them on the shelf."*
*"In the Matai'an case, the library happens to have photos of a lake that existed for only 64 days."*
