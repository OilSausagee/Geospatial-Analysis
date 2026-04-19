# ARIA v5.0 — Matai'an Three-Act Auditor

**Objective**: Upgrade ARIA from v4.0 (Network Accessibility) to v5.0 (Matai'an Three-Act Auditor) by integrating Sentinel-2 L2A optical imagery via the Microsoft Planetary Computer STAC API, producing a forensic audit of the 2025 Matai'an Creek barrier lake event.

## Event Overview

**Timeline in one sentence**: On Jul 21, 2025, Typhoon Wipha's rainfall triggered a massive landslide in upper Wanrong that dammed the Matai'an Creek and formed a ~200 m deep barrier lake; the lake existed for 64 days and breached on Sep 23, 2025 at 14:50, releasing 15.4 million m³ of water in 30 minutes and burying downstream Guangfu township. 18+ lives lost.

## Three-Act Satellite Analysis

| Act | Date window | Cloud budget | Purpose |
|-----|-------------|--------------|---------|
| **Pre** | 2025-06-01 → 2025-07-15 | < 20% | Baseline forested valley |
| **Mid** | 2025-08-01 → 2025-09-20 | < 40% (monsoon) | Lake present, pre-breach |
| **Post** | 2025-09-25 → 2025-11-15 | < 30% | Lake drained, debris in Guangfu |

## Data Sources

### Satellite imagery (STAC)
- **Endpoint**: `https://planetarycomputer.microsoft.com/api/stac/v1`
- **Collection**: `sentinel-2-l2a`
- **Bbox**: `121.28, 23.56, 121.52, 23.76`
- **Bands**: B02, B03, B04, B08, B11, B12
- **CRS**: EPSG:32651 (UTM 51N) @ 10 m

### Prior-week inputs
| Source | File | Role |
|--------|------|------|
| W3 Shelters | `data/shelters_hualien.gpkg` | 198 Hualien shelters + `river_risk` |
| W4 Terrain | `data/hualien_terrain.gpkg` | `mean_elevation`, `max_slope`, `terrain_risk` |
| W5 Rainfall | `data/wipha_202507.json` | Wipha station records |
| W6 Kriging | `data/kriging_rainfall.tif` | Interpolated rainfall surface |
| W7 Network | `data/top5_bottlenecks.gpkg`, `data/hualien_network.graphml` | Top-5 bottlenecks + road graph |
| W8 Overlay | `data/guangfu_overlay.gpkg` | 5 Guangfu critical nodes |

## Methodology

### Four change metrics (reusable `xarray` functions)
1. `nir_drop(pre, post) = pre_B08 - post_B08`
2. `swir_post(post) = post_B12`
3. `bsi_change(pre, post) = bsi(post) − bsi(pre)`, `BSI = ((B11+B04) − (B08+B02)) / ((B11+B04) + (B08+B02))`
4. `ndvi_change(pre, post) = ndvi(pre) − ndvi(post)`, `NDVI = (B08 − B04)/(B08 + B04)`

Applied to **Pre → Mid** (lake formation) and **Pre → Post** (landslide + debris flow), producing 8 PNGs under `output/`.

### Three detection masks

| Mask | Scene pair | Rule | Spatial gate |
|------|-----------|------|--------------|
| **Barrier lake** | Pre → Mid | `(pre_NIR > 0.25) & (mid_NIR < 0.18) & (mid_Blue > 0.03) & (mid_Green > mid_NIR)` | `lon < 121.33°E` (west — exclude downstream flooding) |
| **Landslide source** | Pre → Post | `(nir_drop > τ₁) & (swir_post > τ₂) & (pre_NIR > 0.25)`, τ tuned via F1 | none |
| **Debris flow** | Pre → Post | `(ndvi_change > 0.25) & (bsi_change > 0.10) & (pre_NIR > 0.20)` | `lon > 121.35°E` (east — downstream only) |

Important: the Sentinel-2 stack is in **UTM meters**, not degrees. The spatial gate converts each `lon_gate` value to UTM easting via `pyproj.Transformer` before comparison — comparing UTM easting directly against a decimal-degree number silently produces an always-true or always-false mask.

### Landslide threshold tuning (C2)
- Ground truth: 10 confirmed landslide pixels (upper Wanrong headwall) + 10 stable vegetation pixels (nearby ridges)
- 5 `(nir_drop, swir_post)` threshold pairs evaluated with confusion matrix + F1
- Best pair is selected and reused in the final mask

### Vectorization
- `rasterio.features.shapes` → polygons in EPSG:32651
- Minimum polygon area: **barrier_lake ≥ 10 000 m²**, **landslide_source ≥ 2 000 m²**, **debris_flow ≥ 5 000 m²**
- Saved as three layers in `output/mataian_detections.gpkg`: `barrier_lake`, `landslide_source`, `debris_flow`

### Eyewitness Impact Table (Part D)
Every W3 shelter, every W7 top-5 bottleneck, every W8 Guangfu overlay node is spatial-joined against the three hazard layers. A **hit** is:
- **Barrier lake / debris flow**: asset within polygon
- **Landslide**: asset within 200 m of polygon (buffered `sjoin`)

Sorted by (Debris Flow Hit → Landslide Hit → Barrier Lake Hit → W4 terrain risk). Exported to `output/impact_table.csv`.

## Selected STAC Scene IDs

| Act | Item ID | Date | Tile cloud |
|-----|---------|------|-----------|
| **PRE** | `S2A_MSIL2A_20250615T023141_R046_T51QUG_20250615T070417` | 2025-06-15 | ~8.5% |
| **MID** | `S2C_MSIL2A_20250911T022551_R046_T51QUG_20250911T055914` | 2025-09-11 | ~13.5% |
| **POST** | `S2B_MSIL2A_20251016T022559_R046_T51QUG_20251016T042804` | 2025-10-16 | ~2.5% |

All three were confirmed via TCI Quick-QA to have a cloud-free Matai'an valley (not just low tile-level cloud cover).

## AI Diagnostic Log

### Problem 1 — Mid-event STAC window buried in monsoon cloud
**Issue**: Aug–Sep 2025 tile-level cloud cover was consistently > 40%, and even the candidates that passed the filter had cloud patches right over the barrier lake site.
**Solution**: `robust_search()` does client-side filtering with exponential backoff (server-side `query` was unreliable); `preview_tci()` renders side-by-side JPEG thumbnails so localised cloud over the Matai'an valley can be visually rejected before committing to a scene ID.
**Lesson**: Tile-level `eo:cloud_cover` is insufficient for sub-tile hazard analysis.

### Problem 2 — `fill_value` / `dtype` incompatibility in stackstac
**Issue**: `stackstac.stack(..., dtype="float32", fill_value=0)` raised `ValueError: fill_value 0 is incompatible with float32`. Using `fill_value=np.nan` then failed the same safe-cast check because `np.nan` is Python `float` (= float64).
**Solution**: Use `fill_value=np.float32(np.nan)`. NaN is the correct sentinel for missing optical reflectance (0 would be a valid measurement and pollute downstream NDVI/BSI math).

### Problem 3 — Length-1 `time` dim caused silent "empty array" bug
**Issue**: `pre - post` produced an array with `time` dimension of length 0, making `.values` shape `(0, H, W)` and triggering "No numeric data to plot" or `IndexError: index N out of bounds for axis 0 with size 0` downstream. Cause: xarray arithmetic aligns on shared dims with inner-join; pre/post have different time coord values so inner-join of time is empty.
**Solution**: `stack.squeeze("time", drop=True)` right after `compute()` inside `load_sentinel2_bands`, and again defensively at the top of any cell that does pre/post arithmetic.

### Problem 4 — Spatial gate silently disabled by CRS mismatch (two layers)
**Issue A**: C1 barrier lake returned 0 pixels after gating; C3 debris flow returned the full bbox after gating.
**Cause A**: `mid_stack.x` / `post_stack.x` are UTM easting in **meters** (~3.3 × 10⁵), but `lon_gate` is **decimal degrees** (~121.3). `UTM_x < 121.33` is always False; `UTM_x > 121.35` is always True — the gate becomes a no-op or a kill-all.
**Fix A**: Convert `lon_gate` to UTM easting via `pyproj.Transformer("EPSG:4326" → TARGET_EPSG)` before comparison.

**Issue B**: After Fix A, `x_gate` printed as `inf` — C1 still a no-op, C3 still killed everything.
**Cause B**: The forward Transformer's input signature is `(lon, lat)` with `always_xy=True`. I passed `lat_c = float(stack.y.mean())` — but the stack is already in UTM, so `stack.y` is **northing in meters** (~2.6 × 10⁶), not latitude. pyproj received `lat=2618000°`, which is geodetically impossible, and returned `inf`.
**Fix B**: Back-transform the stack's center `(x, y)` from UTM to EPSG:4326 first to recover the real latitude, then use that latitude in the forward transform for `lon_gate`.
**Lesson**: Every coordinate scalar carries an invisible CRS tag. A `.y` attribute on a UTM-backed xarray is *not* latitude, even though the name suggests it.

### Problem 5 — `dir()` scope inside functions and generators
**Issue**: `all(v in dir() and eval(v) is not None for v in [...])` always returned False; `if "shelters_gdf" in dir():` inside a function body also failed, producing "No asset layers loaded — impact table empty."
**Cause**: Generator expressions have their own scope, and `dir()` inside a function returns the function's locals — neither sees module globals.
**Solution**: Replace `dir()` with `globals()` in both the generator-expression guard and the in-function guards in `create_eyewitness_impact_table()`.

## Deliverables

| File | Content |
|------|---------|
| `ARIA_v5_mataian_fixed.ipynb` | Full executed notebook with Captain's Log markdown cells |
| `output/mataian_detections.gpkg` | Three layers: `barrier_lake`, `landslide_source`, `debris_flow` |
| `output/impact_table.csv` | Eyewitness Impact Table (W3 + W7 + W8 assets × 3 hazard columns) |
| `output/tci_qa_*.png` | Three-act TCI quick-QA panels |
| `output/{nir_drop,swir_post,bsi_change,ndvi_change}_{pre_to_mid,pre_to_post}.png` | 8 change-metric maps |
| `output/{barrier_lake,landslide,debris_flow}_mask.png` | 3 detection-mask visualisations |

## Environment Variables (`.env`)

```
STAC_ENDPOINT=https://planetarycomputer.microsoft.com/api/stac/v1
S2_COLLECTION=sentinel-2-l2a
MATAIAN_BBOX=121.28,23.56,121.52,23.76
TARGET_EPSG=32651
S2_BANDS=B02,B03,B04,B08,B11,B12
PRE_EVENT_START=2025-06-01
PRE_EVENT_END=2025-07-15
MID_EVENT_START=2025-08-01
MID_EVENT_END=2025-09-20
POST_EVENT_START=2025-09-25
POST_EVENT_END=2025-11-15
```

## Coverage Gap Discussion

The Impact Table exposes ARIA v4.0's **geographic blind spot**: W3 shelters and W7 top-5 bottlenecks are anchored in Hualien City + Suhua Highway, but the Matai'an watershed and Guangfu township are ~40 km south. W3/W7 hits from this event are therefore near zero, while W8 overlay nodes take direct hits.

**Implication**: a risk/network model trained on urban-core assets cannot surface watershed-scale threats. ARIA v5.0 closes this loop by adding satellite-derived hazard polygons that are independent of pre-registered asset geography — the 64-day lake was visible throughout that window to any Sentinel-2 scene over the Matai'an valley.

**Recommended extension**:
1. Permanently add watershed-based monitoring polygons (slope > 30° within 20 km of downstream settlements) as first-class assets in W3+
2. Trigger barrier-lake early-warning automation on any `nir_drop > τ` detection upstream of a settled floodplain
3. Expand W3 shelter/W7 network coverage to Guangfu and Fuyuan corridors

## Technical Notes

- **CRS**: Sentinel-2 native = EPSG:32651 (UTM 51N). W3/W4/W7/W8 vectors = EPSG:3826 (TWD97). Always reproject *vectors to raster CRS* when sampling pixel values.
- **Memory**: `stackstac.stack(bounds_latlon=BBOX)` keeps the cube under 200 MB; without it, OOM.
- **Token refresh**: Always `planetary_computer.sign(item)` before reading band assets — SAS tokens expire after ~1 hour.
- **Turbid-water NIR**: Matai'an barrier lake NIR is 0.10–0.18 (sediment-laden), **not** < 0.05 like clear water. Using a clear-water threshold returns zero pixels.

## Submission Checklist

- [x] Three-act STAC scene selection + TCI Quick-QA + reproducible item IDs
- [x] Four change-metric functions implemented and applied to Pre→Mid + Pre→Post
- [x] Three detection masks with tuned thresholds + F1 reporting for C2
- [x] Vectorization to multi-layer GeoPackage (`barrier_lake`, `landslide_source`, `debris_flow`)
- [x] Eyewitness Impact Table + coverage-gap markdown analysis
- [x] Professional standards: `.env`, Captain's Log cells, AI diagnostic log (5 entries)
- [x] Output folder populated with TCI panels, 8 change maps, 3 mask visualisations
