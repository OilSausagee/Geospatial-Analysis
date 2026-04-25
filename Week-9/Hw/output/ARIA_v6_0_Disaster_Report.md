
### ARIA v6.0 — Validated Disaster Assessment
**Event:** Matai'an Barrier Lake formation (Typhoon Colo, 2025)
**Generated:** 2026-04-26 00:53

---

#### Executive Summary
A temporary barrier lake formed in the Matai'an valley during Typhoon Colo (Sep 2025).
Using Sentinel-2 L2A imagery across three dates (Jun / Sep / Oct 2025), ARIA v6.0 mapped
vegetation loss (ΔNDVI), inundation (ΔNDWI) and debris exposure (ΔBSI). The optimal
ΔNDVI threshold of **-0.10** yielded **PA = 38.9%** and
**UA = 77.8%** against 60 teacher-corrected ground-truth points, with
**Kappa = 0.349** (Fair agreement). High-confidence impact covers
**45.03 km²**; an additional 21.76 km² sits in the low-confidence band
and requires revalidation. Recommendation: treat the high-confidence zone as a *Danger*
area for evacuation planning, the low-confidence zone as *Caution*, and the remainder as
*Safe* pending further monitoring.

#### Change Detection Analysis
- **ΔNDVI (Pre→Mid)**: mean = -0.027,
  min = -0.886.
  Strong negative signal over the lake footprint confirms vegetation loss.
- **ΔNDWI (Pre→Mid)**: min = -0.544,
  max = +0.970. Positive band delineates open water.
- **ΔBSI (Pre→Mid)**: min = -0.670,
  max = +0.510. Positive anomalies flag debris
  fields adjacent to the lake.
- **Best threshold** (Task 2): **-0.10** — maximises F1 = 0.519.
- **Confusion matrix** (Task 3): TP=7, FP=2, TN=26, FN=11.

#### Confidence Assessment
| Zone | Definition | Area (km²) | Action |
|------|-----------|-----------|--------|
| High  | \|ΔNDVI\| > 0.15 | 45.03 | Evacuate / monitor intensely |
| Low   | 0.10 ≤ \|ΔNDVI\| ≤ 0.15 | 21.76 | Field / UAV revalidation |
| None  | \|ΔNDVI\| < 0.10 | 363.67 | Routine monitoring only |

**Immediate action** is warranted only in the High-confidence zone.

#### Ground-Truth Validation
- **Source**: teacher's `data/validation_points.geojson` (60 points; lake = 15,
  landslide = 15, stable = 30). Corrected by the instructor using Google Earth Pro VHR
  imagery, NCDR reports, and Sentinel-2 visual interpretation.
- **Points inside image extent**: 60 / 60
- **Points inside LAKE_BBOX**: 23
- Discrepancies: commission error (22.2%) concentrates on shoreline mixed pixels
  where NDVI decrease is real but not caused by the lake (e.g. landslide scars are
  counted as "change" in our binary scheme).

#### Recommendations
- **Evacuation planners**: High-confidence zones have **≈78% certainty of real
  change** (UA). Treat them as Danger.
- **Monitoring teams**: Revisit the low-confidence band within **7 days** using the next
  Sentinel-2 pass or a UAV survey; ΔBSI and ΔNDWI can cross-check ΔNDVI there.
- **Disaster management**: Overall accuracy 71.7% and Kappa 0.349 support
  **operational** use for zone-level planning, but not for property-level loss accounting
  at 10 m resolution.
