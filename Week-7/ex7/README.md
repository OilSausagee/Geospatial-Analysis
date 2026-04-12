# ARIA v4.0 - Hualien Disaster Accessibility Assessment

## Project Overview

This project develops an integrated disaster accessibility assessment system by combining road network data, rainfall information, and terrain risk analysis.
The system evaluates how extreme rainfall under the Typhoon Fung-wong scenario affects transportation accessibility and emergency response efficiency in Hualien.

---

## Data Sources

- **Road Network**: OpenStreetMap (via OSMnx)
- **Rainfall Data**: CWA rainfall station JSON (fungwong_202511.json)
- **Terrain Risk**: Week 4 terrain risk analysis (optional)
- **Shelter & Distance Analysis**: Week 3 shelter locations and river distance analysis (optional)

---

## AI Diagnostic Log

### 1. OSMnx extraction timeout or incomplete road network
**Issue**: Downloading the road network from OSMnx was slow and sometimes unstable.  
**Solution**: I saved the extracted road network as a `.graphml` file and reused it later to avoid repeated downloads.

### 2. Isochrone polygon shape anomaly
**Issue**: Isochrone polygons may show irregular boundaries or holes.  
**Solution**: I adjusted the alpha parameter and ensured the analysis used the projected CRS EPSG:3826.

### 3. Kriging raster sampling returns nodata at road segment midpoints
**Issue**: Raster-based rainfall sampling may return nodata values at some road segment midpoints.  
**Solution**: In this implementation, rainfall is derived from station-based JSON data instead of raster sampling.

### 4. Road disconnection and NetworkXNoPath
**Issue**: Under severe rainfall congestion, some routes may become disconnected and shortest path analysis may fail with `NetworkXNoPath`.  
**Solution**: I interpreted these disconnected areas as isolated zones and considered them as candidates for alternative rescue strategies.

### 5. Missing road speed attributes
**Issue**: Some road edges did not contain valid `speed_kph` values.  
**Solution**: I assigned a default speed value of 40 km/h to maintain stable travel-time calculation.

---

## Key Findings

- **Most Critical Bottleneck Nodes**: Node 649286213 (0.1402), Node 649286214 (0.1394), Node 1061487893 (0.1253), Node 929963021 (0.1235), Node 1074772659 (0.1157)
- **Maximum Accessibility Loss**: The most critical bottleneck nodes showed about 99.6%–100.0% short-distance contraction and 99.7%–100.0% long-distance contraction under the simulated scenario.
- **Emergency Response Priority**: Areas with high terrain risk and reduced road accessibility should be prioritized for emergency rescue and resource allocation.

---

## Submission Checklist

- [x] ARIA_v4.ipynb (Complete workflow)
- [x] hualien_network.graphml (Saved road network)
- [x] README.md (This file)
- [x] accessibility_table.csv (Generated)

