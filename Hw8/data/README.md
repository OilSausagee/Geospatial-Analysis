# Week 8 Homework Data Directory

This directory contains all the required data files for ARIA v5.0 - Matai'an Three-Act Auditor assignment.

## Data Files

### From Previous Weeks
- **shelters_hualien.gpkg** - Week 3 shelters GeoDataFrame with river_risk attribute
- **top5_bottlenecks.gpkg** - Week 7 top-5 bottlenecks for network analysis
- **kriging_rainfall.tif** - Week 6 kriging rainfall output (recommended for validation)
- **hualien_network.graphml** - Week 7 road network graph

### Week 8 Specific
- **guangfu_overlay.gpkg** - Guangfu township critical nodes (5 required + optional nodes)
  - Required nodes: 
    - Guangfu Railway Station ( Guangfu Railway Station)
    - Guangfu Elementary School ( Guangfu Elementary School)
    - Guangfu Township Office ( Guangfu Township Office)
    - Taiwan Route 9 Matai'an Creek Bridge ( Taiwan Route 9 Matai'an Creek Bridge)
    - Foju Street Deposition Center ( Foju Street Deposition Center)
  - Schema: name / cn_name / node_type / priority / geometry
  - CRS: EPSG:3826 (TWD97)

## All Required Data Files Now Available

### Week 4 - Terrain Risk
- **hualien_terrain.gpkg** - Contains mean_elevation, max_slope, terrain_risk attributes
- *Status: Copied from HW4 outputs*

### Week 5 - Rainfall Scenarios
- **wipha_202507.json** - Typhoon Wipha rainfall simulation data (template created)
- **fungwong_202511.json** - Alternative rainfall scenario data (also available)
- *Status: Template created with realistic Wipha typhoon data for Hualien area*

## Configuration
- **../.env** - Environment variables for STAC API, bounding box, date windows, and CRS settings

## Data Sources
- Sentinel-2 L2A imagery will be downloaded via Microsoft Planetary Computer STAC API
- Reference data from NCDR (National Center for Disaster Reduction)
- Administrative boundaries and infrastructure from official government sources

## Coordinate Reference Systems
- Raster data (Sentinel-2): EPSG:32651 (UTM 51N)
- Vector data (local): EPSG:3826 (TWD97)
- Always reproject vectors to raster CRS when sampling pixel values

## Notes
- All vector files should be validated for proper schema and CRS before use
- The guangfu_overlay.gpkg is critical for Part D - Multi-Layer Audit
- Missing terrain risk and Wipha data need to be addressed before full analysis
