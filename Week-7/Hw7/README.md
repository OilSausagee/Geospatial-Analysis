# ARIA v4.0 - Hualien Disaster Accessibility Assessment

## Project Overview

This project builds an integrated automatic disaster accessibility assessment system combining road network, rainfall, and terrain data.

## datatosource

- **Road network**: OpenStreetMap (via OSMnx)
- **Rainfall**: Week 6 Kriging Interpolation result(s)
- **terrain**: Week 4 Terrain riskparttype
- **avoiddisasterall**: Week 3 avoiddisasterallpositionsettingandriverstreamdistancedistance

## AI diagnosticbreakdaylog

### 1. OSMnx extraction
**issueissue**: Converting reachable network nodes into isochrone polygons required handling spatial geometry operations.

**Solution(s)**: Used travel time thresholds and shapely MultiPoint / polygon methods to generate isochrone service areas for accessibility analysis.

### 2. Isochrone(s)multiplepolygon
**issueissue**: Converting reachable network nodes into isochrone polygons required handling spatial geometry operations.

**Solution(s)**: Used travel time thresholds and shapely MultiPoint / polygon methods to generate isochrone service areas for accessibility analysis.

### 3. Othercourseissue
**issueissue**: Road accessibility changes dynamically during heavy rainfall and required adjusting travel time based on congestion.

**Solution(s)**: Implemented the rain_to_congestion() function to convert rainfall intensity into congestion factors and recalculated adjusted travel time for each road segment.

## corecenterissueappear

- Most fragile bottleneck: Node 649286213 (highest betweenness centrality = 0.1402)
- Maximum accessibility loss: Accessibility around Node 649286213 decreased from 10.99 km² to 0.00 km² (100% reduction) under heavy rainfall conditions.
- Build rescue priority order:
  1. Restore accessibility at critical bottleneck intersections (especially Node 649286213 and 649286214).
  2. Maintain road connectivity to evacuation shelters and major arterial roads.
  3. Deploy alternative rescue methods (helicopters or boats) for potentially isolated areas.

## Submission Checklist

- [ ] ARIA_v4.ipynb (Complete integration and analysis)
- [ ] hualien_network.graphml (Road networkcountdata)
- [ ] README.md (This file + AI diagnosticbreakdaylog)
- [ ] accessibilitybenefit-costtable (DataFrame or CSV)
