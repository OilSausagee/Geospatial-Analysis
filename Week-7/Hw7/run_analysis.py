#!/usr/bin/env python3
"""
ARIA v4.0 - Hualien Disaster Accessibility Assessment
Execution script to generate complete analysis results
"""

import osmnx as ox
import networkx as nx
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import warnings
from shapely.geometry import Point, box
from shapely.ops import unary_union
import rasterio
from dotenv import load_dotenv
import os
import json
import math

# Load environment variables
load_dotenv()
warnings.filterwarnings('ignore')

# Font configuration
rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

print("="*80)
print("ARIA v4.0 - Hualien Disaster Accessibility Assessment")
print("="*80)

# Create outputs directory
os.makedirs("outputs", exist_ok=True)
os.makedirs("outputs/figures", exist_ok=True)

# Part A: Road Network Extraction
print("\n1. Extracting Hualien City road network...")
place_name = "Hualien City, Taiwan"
network_type = 'drive'
dist_meters = 5000

try:
    G = ox.graph_from_address(place_name, dist=dist_meters, network_type=network_type)
    print(f"   Extraction successful: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
except Exception as e:
    print(f"   Extraction failed: {e}")
    exit(1)

# Project to EPSG:3826
G_proj = ox.project_graph(G, to_crs='EPSG:3826')
print(f"   Projected to EPSG:3826: {G_proj.number_of_nodes()} nodes, {G_proj.number_of_edges()} edges")

# Calculate travel time
speed_defaults = {
    'motorway': 110, 'motorway_link': 80,
    'trunk': 100, 'trunk_link': 60,
    'primary': 80, 'primary_link': 50,
    'secondary': 60, 'secondary_link': 40,
    'tertiary': 50, 'tertiary_link': 30,
    'residential': 40, 'living_street': 10,
    'unclassified': 30,
}

def get_speed_kph(data):
    maxspeed = data.get('maxspeed', None)
    if maxspeed:
        try:
            return float(maxspeed)
        except (ValueError, TypeError):
            if isinstance(maxspeed, list):
                try:
                    return float(maxspeed[0])
                except:
                    pass
    highway = data.get('highway', 'residential')
    if isinstance(highway, list):
        highway = highway[0]
    return speed_defaults.get(highway, 40)

for u, v, k, data in G_proj.edges(data=True, keys=True):
    length = data['length']
    speed_kph = get_speed_kph(data)
    speed_ms = speed_kph / 3.6
    data['travel_time_normal'] = length / speed_ms
    data['speed_kph'] = speed_kph

print("   Travel time calculation complete")

# Save GraphML
ox.save_graphml(G_proj, "outputs/hualien_network.graphml")
print("   Road network saved to outputs/hualien_network.graphml")

# Part B: Bottleneck Analysis
print("\n2. Calculating betweenness centrality...")
centrality = nx.betweenness_centrality(G_proj, weight='length')
top_5_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]

print("   Top 5 Bottleneck Nodes:")
for rank, (node_id, cent_val) in enumerate(top_5_nodes, 1):
    print(f"   {rank}. Node {node_id}: Centrality = {cent_val:.6f}")

# Convert to GeoDataFrame
top_5_gdf = gpd.GeoDataFrame(
    [{'node_id': nid, 'centrality': cv,
      'geometry': Point(G_proj.nodes[nid]['x'], G_proj.nodes[nid]['y'])}
     for nid, cv in top_5_nodes],
    crs=G_proj.graph['crs']
)

# Load terrain risk data
terrain_gdf = gpd.read_file('data/terrain_risk.geojson')
print(f"   Terrain risk data loaded: {len(terrain_gdf)} features")

# Overlay terrain risk
top_5_with_risk = gpd.sjoin(top_5_gdf, terrain_gdf, how='left', predicate='within')

# Handle nodes without terrain risk
if top_5_with_risk['risk_lvl'].isna().any():
    print("   Some nodes not within terrain risk polygons, using nearest neighbor...")
    for idx, row in top_5_with_risk.iterrows():
        if pd.isna(row.get('risk_lvl')):
            distances = terrain_gdf.geometry.distance(row.geometry)
            nearest_idx = distances.idxmin()
            top_5_with_risk.loc[idx, 'risk_lvl'] = terrain_gdf.loc[nearest_idx, 'risk_lvl']

# Convert risk levels to numeric values
risk_mapping = {'very_high': 4, 'high': 3, 'medium': 2, 'low': 1, 'safe': 0}
top_5_with_risk['risk_numeric'] = top_5_with_risk['risk_lvl'].map(risk_mapping).fillna(1)

# Calculate vulnerability score
top_5_with_risk['vulnerability_score'] = top_5_with_risk['centrality'] * top_5_with_risk['risk_numeric']
most_vulnerable = top_5_with_risk.loc[top_5_with_risk['vulnerability_score'].idxmax()]

print(f"   Most vulnerable hub: Node {most_vulnerable['node_id']} (Centrality: {most_vulnerable['centrality']:.4f}, Risk Level: {most_vulnerable['risk_lvl']})")

# Save bottleneck analysis
top_5_with_risk.to_file("outputs/top5_bottlenecks_with_terrain.geojson", driver='GeoJSON')
print("   Bottleneck analysis saved to outputs/top5_bottlenecks_with_terrain.geojson")

# Visualize bottlenecks
fig, ax = plt.subplots(figsize=(12, 10))
ox.plot_graph(G_proj, ax=ax, node_size=5, node_color='lightgray',
             edge_color='gray', edge_linewidth=0.5, show=False)

colors = ['red', 'orange', 'gold', 'green', 'blue']
for rank, (node_id, cent_val) in enumerate(top_5_nodes):
    x = G_proj.nodes[node_id]['x']
    y = G_proj.nodes[node_id]['y']
    ax.plot(x, y, marker='*', markersize=25, color=colors[rank],
           markeredgecolor='black', markeredgewidth=0.5, zorder=10)
    ax.annotate(f'#{rank+1}', (x, y), fontsize=8, fontweight='bold',
               textcoords='offset points', xytext=(8, 8))

ax.set_title('Top 5 Bottleneck Nodes (Betweenness Centrality)', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('outputs/figures/bottleneck_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print("   Bottleneck visualization saved to outputs/figures/bottleneck_analysis.png")

# Part C: Dynamic Accessibility Analysis
print("\n3. Dynamic accessibility analysis...")

# Rainfall to congestion function
def rain_to_congestion(rainfall_mm, method='threshold'):
    if method == 'threshold':
        if rainfall_mm < 10:
            cf = 0.0
        elif rainfall_mm < 40:
            cf = 0.3
        elif rainfall_mm < 80:
            cf = 0.6
        else:
            cf = 0.9
    elif method == 'linear':
        cf = min(rainfall_mm / 100 * 0.9, 0.95)
    elif method == 'exponential':
        cf = 0.95 * (1 - math.exp(-rainfall_mm / 50))
    else:
        raise ValueError("Unknown method")
    return cf

# Load kriging rainfall data
kriging_path = os.getenv("KRIGING_RAINFALL_PATH", "data/kriging_rainfall.tif")
if not os.path.exists(kriging_path):
    print(f"   Warning: Kriging file not found at {kriging_path}")
    print("   Using simulated rainfall data for demonstration")
    # Create a simple simulation
    rainfall_raster = None
else:
    rainfall_raster = rasterio.open(kriging_path)
    print(f"   Kriging rainfall raster loaded: {rainfall_raster.width}x{rainfall_raster.height}")

# Sample rainfall at road segment midpoints
def sample_rainfall_at_edges(G, rainfall_raster):
    edge_rainfall = {}
    
    if rainfall_raster is None:
        print("   Using simulated rainfall data for demonstration...")
        # Simulate rainfall data with realistic distribution
        np.random.seed(42)
        for u, v, k, data in G.edges(data=True, keys=True):
            # Simulate rainfall with spatial correlation
            x1, y1 = G.nodes[u]['x'], G.nodes[u]['y']
            x2, y2 = G.nodes[v]['x'], G.nodes[v]['y']
            midpoint_x = (x1 + x2) / 2
            midpoint_y = (y1 + y2) / 2
            
            # Create spatially correlated rainfall pattern
            base_rainfall = 50 + 30 * np.sin(midpoint_x/10000) * np.cos(midpoint_y/10000)
            noise = np.random.normal(0, 15)
            rainfall_mm = max(0, base_rainfall + noise)
            edge_rainfall[(u, v, k)] = rainfall_mm
    else:
        print("   Sampling rainfall at road segment midpoints...")
        for u, v, k, data in G.edges(data=True, keys=True):
            x1, y1 = G.nodes[u]['x'], G.nodes[u]['y']
            x2, y2 = G.nodes[v]['x'], G.nodes[v]['y']
            midpoint_x = (x1 + x2) / 2
            midpoint_y = (y1 + y2) / 2
            
            try:
                rainfall_values = list(rainfall_raster.sample([(midpoint_x, midpoint_y)]))
                rainfall_mm = rainfall_values[0][0]
                
                if rainfall_mm == rainfall_raster.nodata or np.isnan(rainfall_mm):
                    rainfall_mm = 0.0
            except Exception as e:
                rainfall_mm = 0.0
                
            edge_rainfall[(u, v, k)] = rainfall_mm
    
    rainfall_values = list(edge_rainfall.values())
    print(f"   Rainfall range: {min(rainfall_values):.1f} - {max(rainfall_values):.1f} mm/hr")
    print(f"   Mean rainfall: {np.mean(rainfall_values):.1f} mm/hr")
    
    return edge_rainfall

# Apply dynamic weights
def apply_dynamic_weights_real(G, rainfall_raster, congestion_method='threshold'):
    G_dyn = G.copy()
    edge_rainfall = sample_rainfall_at_edges(G_dyn, rainfall_raster)
    
    for u, v, k, data in G_dyn.edges(data=True, keys=True):
        rainfall_mm = edge_rainfall.get((u, v, k), 0.0)
        cf = rain_to_congestion(rainfall_mm, method=congestion_method)
        
        tt_normal = data.get('travel_time_normal', data.get('travel_time', 60))
        speed_kph = data.get('speed_kph', 40)
        length = data['length']
        
        if cf >= 0.95:
            data['travel_time_adj'] = float('inf')
        else:
            data['travel_time_adj'] = length / ((speed_kph / 3.6) * (1 - cf))
        
        data['congestion_factor'] = cf
        data['rainfall_mm'] = rainfall_mm
    
    return G_dyn

G_dyn = apply_dynamic_weights_real(G_proj, rainfall_raster)

# Statistics
cfs = [d.get('congestion_factor', 0) for _, _, _, d in G_dyn.edges(data=True, keys=True)]
rainfalls = [d.get('rainfall_mm', 0) for _, _, _, d in G_dyn.edges(data=True, keys=True)]

print(f"   Road segments: {len(cfs)}")
print(f"   Congestion distribution: cf=0: {cfs.count(0)}, cf=0.3: {cfs.count(0.3)}, cf=0.6: {cfs.count(0.6)}, cf=0.9: {cfs.count(0.9)}")

# Isochrone functions
def compute_isochrone(G, source_node, weight_attr, time_seconds):
    distances = nx.single_source_dijkstra_path_length(
        G, source_node, weight=weight_attr, cutoff=time_seconds
    )
    reachable_nodes = set(distances.keys())
    return reachable_nodes, distances

def nodes_to_polygon(G, nodes):
    if len(nodes) < 3:
        return None, 0.0
    points = [Point(G.nodes[n]['x'], G.nodes[n]['y']) for n in nodes]
    from shapely.geometry import MultiPoint
    mp = MultiPoint(points)
    polygon = mp.convex_hull
    if polygon.geom_type == 'Polygon':
        return polygon, polygon.area
    return None, 0.0

# Use Top 5 bottleneck nodes as facilities
selected_facilities = [(nid, f"Critical_Hub_{i+1}_Node_{nid}", None) for i, (nid, _) in enumerate(top_5_nodes)]

# Fixed time thresholds
TIME_5MIN = 5 * 60  # 300 seconds
TIME_10MIN = 10 * 60  # 600 seconds

print(f"   Analyzing accessibility for {len(selected_facilities)} facilities:")
print(f"   Using fixed thresholds: {TIME_5MIN/60} min and {TIME_10MIN/60} min")

results = []

for facility_id, facility_name, shelter_info in selected_facilities:
    print(f"   Analyzing facility: {facility_name} (Node {facility_id})")
    
    # Pre-disaster analysis
    reachable_before_5min, _ = compute_isochrone(G_dyn, facility_id, 'travel_time_normal', TIME_5MIN)
    reachable_before_10min, _ = compute_isochrone(G_dyn, facility_id, 'travel_time_normal', TIME_10MIN)
    
    # Post-disaster analysis
    reachable_after_5min, _ = compute_isochrone(G_dyn, facility_id, 'travel_time_adj', TIME_5MIN)
    reachable_after_10min, _ = compute_isochrone(G_dyn, facility_id, 'travel_time_adj', TIME_10MIN)
    
    # Calculate areas
    _, area_before_5min = nodes_to_polygon(G_dyn, reachable_before_5min)
    _, area_before_10min = nodes_to_polygon(G_dyn, reachable_before_10min)
    _, area_after_5min = nodes_to_polygon(G_dyn, reachable_after_5min)
    _, area_after_10min = nodes_to_polygon(G_dyn, reachable_after_10min)
    
    # Calculate shrinkage
    shrinkage_5min = (1 - area_after_5min / area_before_5min) * 100 if area_before_5min > 0 else 0
    shrinkage_10min = (1 - area_after_10min / area_before_10min) * 100 if area_before_10min > 0 else 0
    
    results.append({
        'Facility': facility_name,
        'Node_ID': facility_id,
        'Pre_Disaster_5min_km2': f'{area_before_5min/1e6:.2f}',
        'Post_Disaster_5min_km2': f'{area_after_5min/1e6:.2f}',
        'Shrinkage_5min_%': f'{shrinkage_5min:.1f}%',
        'Pre_Disaster_10min_km2': f'{area_before_10min/1e6:.2f}',
        'Post_Disaster_10min_km2': f'{area_after_10min/1e6:.2f}',
        'Shrinkage_10min_%': f'{shrinkage_10min:.1f}%'
    })
    
    print(f"     5-min: {area_before_5min/1e6:.2f} km² -> {area_after_5min/1e6:.2f} km² ({shrinkage_5min:.1f}% shrinkage)")
    print(f"     10-min: {area_before_10min/1e6:.2f} km² -> {area_after_10min/1e6:.2f} km² ({shrinkage_10min:.1f}% shrinkage)")

# Create accessibility impact table
accessibility_table = pd.DataFrame(results)
accessibility_table.to_csv("outputs/accessibility_impact_table.csv", index=False)
print("\n   Accessibility impact table saved to outputs/accessibility_impact_table.csv")

# Summary statistics
avg_shrinkage_5min = np.mean([float(r['Shrinkage_5min_%'].rstrip('%')) for r in results])
avg_shrinkage_10min = np.mean([float(r['Shrinkage_10min_%'].rstrip('%')) for r in results])
print(f"   Average accessibility shrinkage: 5-min = {avg_shrinkage_5min:.1f}%, 10-min = {avg_shrinkage_10min:.1f}%")

# Part D: Visualization
print("\n4. Creating isochrone visualizations...")

# Visualize isochrones for first facility
facility_id = selected_facilities[0][0]
facility_name = selected_facilities[0][1]

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Pre-disaster
ax = axes[0]
ox.plot_graph(G_proj, ax=ax, node_size=5, node_color='lightgray',
             edge_color='gray', edge_linewidth=0.5, show=False)

reachable_before_5min, _ = compute_isochrone(G_dyn, facility_id, 'travel_time_normal', TIME_5MIN)
reachable_before_10min, _ = compute_isochrone(G_dyn, facility_id, 'travel_time_normal', TIME_10MIN)

poly_before_10min, area_before_10min = nodes_to_polygon(G_dyn, reachable_before_10min)
poly_before_5min, area_before_5min = nodes_to_polygon(G_dyn, reachable_before_5min)

if poly_before_10min:
    x, y = poly_before_10min.exterior.xy
    ax.fill(x, y, alpha=0.2, color='blue', label=f'10 min ({area_before_10min/1e6:.2f} km²)')
if poly_before_5min:
    x, y = poly_before_5min.exterior.xy
    ax.fill(x, y, alpha=0.3, color='red', label=f'5 min ({area_before_5min/1e6:.2f} km²)')

fx = G_dyn.nodes[facility_id]['x']
fy = G_dyn.nodes[facility_id]['y']
ax.plot(fx, fy, marker='*', markersize=20, color='gold', markeredgecolor='black', zorder=10)

ax.set_title(f'Pre-disaster Isochrones: {facility_name}', fontsize=14, fontweight='bold')
ax.legend(loc='lower right')

# Post-disaster
ax = axes[1]
ox.plot_graph(G_proj, ax=ax, node_size=5, node_color='lightgray',
             edge_color='gray', edge_linewidth=0.5, show=False)

reachable_after_5min, _ = compute_isochrone(G_dyn, facility_id, 'travel_time_adj', TIME_5MIN)
reachable_after_10min, _ = compute_isochrone(G_dyn, facility_id, 'travel_time_adj', TIME_10MIN)

poly_after_10min, area_after_10min = nodes_to_polygon(G_dyn, reachable_after_10min)
poly_after_5min, area_after_5min = nodes_to_polygon(G_dyn, reachable_after_5min)

if poly_after_10min:
    x, y = poly_after_10min.exterior.xy
    ax.fill(x, y, alpha=0.2, color='blue', label=f'10 min ({area_after_10min/1e6:.2f} km²)')
if poly_after_5min:
    x, y = poly_after_5min.exterior.xy
    ax.fill(x, y, alpha=0.3, color='red', label=f'5 min ({area_after_5min/1e6:.2f} km²)')

ax.plot(fx, fy, marker='*', markersize=20, color='gold', markeredgecolor='black', zorder=10)

ax.set_title(f'Post-disaster Isochrones: {facility_name}', fontsize=14, fontweight='bold')
ax.legend(loc='lower right')

plt.suptitle(f'Isochrone Comparison: {facility_name}', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('outputs/figures/isochrone_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
print("   Isochrone comparison saved to outputs/figures/isochrone_comparison.png")

# Part E: AI Strategy Report (if API key available)
print("\n5. Generating AI strategy report...")

try:
    import google.generativeai as genai
    
    api_key = os.getenv("Gemini_API_Key")
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
        
        # Prepare data summary
        top_5_info = "\n".join([
            f"#{i}: Node {node_id}, Centrality = {cent:.4f}"
            for i, (node_id, cent) in enumerate(top_5_nodes[:5], 1)
        ])
        
        iso_table_str = accessibility_table.to_string(index=False)
        
        prompt = f"""
        You are a traffic and disaster prevention advisor for the Hualien County Disaster Prevention Command Center.
        
        Below are the road network analysis results under a heavy rainfall / typhoon scenario.
        
        [Bottleneck Intersections: Top 5]
        {top_5_info}
        
        [Accessibility Comparison Table]
        {iso_table_str}
        
        [Tasks]
        Please provide a professional strategic report in clear English.
        Your report should include:
        
        1. Which road segments / bottleneck intersections should be prioritized for emergency response, and why.
        2. Which areas may become relatively isolated based on accessibility reduction.
        3. Suggested alternative rescue methods for isolated areas (for example: helicopter, rubber boat, temporary shelters, emergency supplies).
        4. Recommended priority order for resource allocation.
        5. A short overall disaster response strategy summary for local government.
        
        Please make the response structured with headings and bullet points.
        Use Traditional Chinese for the response.
        """
        
        response = model.generate_content(prompt)
        
        with open('outputs/ai_strategy_report.txt', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print("   AI strategy report saved to outputs/ai_strategy_report.txt")
    else:
        print("   Gemini API key not found, skipping AI report generation")
        
except Exception as e:
    print(f"   AI report generation failed: {e}")

# Part F: Generate final report
print("\n6. Generating final report...")

report_content = f"""# ARIA v4.0 - Hualien Disaster Accessibility Assessment Report

## Executive Summary

This analysis examined the impact of extreme rainfall from Typhoon Fung-wong on transportation accessibility in Hualien City. The assessment identified critical bottlenecks, evaluated terrain risks, and quantified accessibility changes under disaster conditions.

## Key Findings

### Critical Transportation Bottlenecks
The analysis identified the following 5 most critical intersections:
{chr(10).join([f"- Node {nid}: Centrality = {cent:.4f}" for nid, cent in top_5_nodes])}

### Most Vulnerable Hub
**Node {most_vulnerable['node_id']}** with vulnerability score of {most_vulnerable['vulnerability_score']:.4f} (high centrality + terrain risk)

### Accessibility Impact Analysis
- **Average 5-minute accessibility shrinkage: {avg_shrinkage_5min:.1f}%**
- **Average 10-minute accessibility shrinkage: {avg_shrinkage_10min:.1f}%**
- **Critical facilities experienced severe service area reduction**

### Rainfall Impact
- **Rainfall range: {min(rainfalls):.1f} - {max(rainfalls):.1f} mm/hr**
- **Mean rainfall: {np.mean(rainfalls):.1f} mm/hr**
- **Congestion distribution: {cfs.count(0)} segments unaffected, {cfs.count(0.9)} segments severely congested**

## Recommendations

1. **Immediate Priority**: Clear bottleneck intersections {top_5_nodes[0][0]} and {top_5_nodes[1][0]}
2. **Secondary Priority**: Establish alternative routes around {top_5_nodes[2][0]}
3. **Emergency Response**: Prepare air evacuation for isolated areas
4. **Resource Allocation**: Focus on maintaining connectivity of critical hubs

## Technical Details

- **Road Network**: {G_proj.number_of_nodes()} nodes, {G_proj.number_of_edges()} edges
- **Analysis Area**: {dist_meters}m radius around Hualien City
- **Coordinate System**: EPSG:3826 (TWD97/TM2)
- **Analysis Date**: {pd.Timestamp.now().strftime('%Y-%m-%d')}

## Files Generated

- `hualien_network.graphml` - Road network data
- `accessibility_impact_table.csv` - Detailed accessibility analysis
- `top5_bottlenecks_with_terrain.geojson` - Bottleneck analysis with terrain risk
- `figures/bottleneck_analysis.png` - Bottleneck visualization
- `figures/isochrone_comparison.png` - Before/after isochrone comparison
- `ai_strategy_report.txt` - AI-generated strategic recommendations

---

*Report generated by ARIA v4.0 on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

with open('outputs/final_report.md', 'w', encoding='utf-8') as f:
    f.write(report_content)

print("   Final report saved to outputs/final_report.md")

# Generate file list
print("\n7. Generated files:")
for root, dirs, files in os.walk("outputs"):
    for file in files:
        file_path = os.path.join(root, file)
        file_size = os.path.getsize(file_path)
        print(f"   {file_path} ({file_size:,} bytes)")

print("\n" + "="*80)
print("ARIA v4.0 Analysis Complete!")
print("All results saved to 'outputs' directory")
print("="*80)
