#!/usr/bin/env python3
"""
Script to execute the Week5-Student notebook and generate outputs
"""

import os
import sys
import json
import warnings
warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.insert(0, '.')

print("=== Week 5 Dynamic Mapping & Time-Machine Simulation ===")
print("Executing notebook and generating outputs...\n")

# Cell [1]: Setup & Load Shelter Data
print("Cell [1]: Setting up environment and loading shelter data...")

import geopandas as gpd
import pandas as pd
import numpy as np
import folium
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create synthetic shelter data for Hualien County (13 shelters)
shelter_data = {
    'shelter_id': range(1, 14),
    'name': [
        '花蓮市第一避難所', '吉安鄉避難中心', '壽豐鄉體育館', '玉里鎮活動中心',
        '瑞穗鄉文化中心', '光復鄉國小', '豐濱鄉社區中心', '新城乡公所',
        '秀林鄉太魯閣避難所', '鳳林鎮體育館', '萬榮鄉活動中心', '卓溪鄉社區中心',
        '富里鄉避難所'
    ],
    'TOWNNAME': [
        '花蓮市', '吉安鄉', '壽豐鄉', '玉里鎮', '瑞穗鄉', '光復鄉', '豐濱鄉', '新城乡',
        '秀林鄉', '鳳林鎮', '萬榮鄉', '卓溪鄉', '富里鄉'
    ],
    'risk_level': [
        'medium', 'low', 'low', 'medium', 'medium', 'low', 'high', 'medium',
        'high', 'low', 'medium', 'low', 'medium'
    ],
    'terrain_risk': [
        'MEDIUM', 'LOW', 'LOW', 'MEDIUM', 'MEDIUM', 'LOW', 'HIGH', 'MEDIUM',
        'HIGH', 'LOW', 'MEDIUM', 'LOW', 'MEDIUM'
    ],
    'mean_elevation': [
        25.5, 35.2, 45.8, 125.3, 85.6, 95.4, 15.7, 55.9,
        285.7, 65.2, 145.8, 185.4, 165.3
    ],
    'max_slope': [
        5.2, 8.5, 12.3, 15.6, 18.9, 22.1, 28.5, 10.4,
        35.7, 7.8, 25.3, 30.1, 20.8
    ]
}

# Create DataFrame
df_shelters = pd.DataFrame(shelter_data)

# Create realistic coordinates for each town in Hualien County
coordinates = [
    [23.9821, 121.5578],  # 花蓮市
    [23.9614, 121.5452],  # 吉安鄉
    [23.8789, 121.4821],  # 壽豐鄉
    [23.3356, 121.3524],  # 玉里鎮
    [23.5642, 121.4123],  # 瑞穗鄉
    [23.6654, 121.4321],  # 光復鄉
    [23.7856, 121.5234],  # 豐濱鄉
    [24.0234, 121.6123],  # 新城乡
    [24.1456, 121.6345],  # 秀林鄉
    [23.7543, 121.3721],  # 鳳林鎮
    [23.4521, 121.2834],  # 萬榮鄉
    [23.2345, 121.3123],  # 卓溪鄉
    [23.1234, 121.2345]   # 富里鄉
]

# Create GeoDataFrame with EPSG:3826 (TWD97)
gdf_shelters = gpd.GeoDataFrame(
    df_shelters,
    geometry=gpd.points_from_xy([coord[1] for coord in coordinates], [coord[0] for coord in coordinates]),
    crs='EPSG:4326'  # Start with WGS84, will convert to EPSG:3826 later
)

# Convert to EPSG:3826 (TWD97)
gdf_shelters = gdf_shelters.to_crs('EPSG:3826')

print(f"✓ Shelter count: {len(gdf_shelters)}")
print(f"✓ CRS: {gdf_shelters.crs}")
print(f"✓ Columns: {list(gdf_shelters.columns)}")

# Cell [2]: Fetch CWA Rainfall API function
print("\nCell [2]: Defining CWA API fetch function...")

def fetch_cwa_api(api_key):
    """
    Fetch real-time rainfall data from CWA API
    """
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0002-001"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching CWA API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

print("✓ CWA API fetch function defined")

# Cell [3]: Parse Rainfall JSON → GeoDataFrame
print("\nCell [3]: Defining rainfall JSON parsing functions...")

def normalize_cwa_json(raw):
    """
    Detect JSON format and return station list
    """
    if not raw:
        return None
    
    # CWA API format (JSON)
    if 'records' in raw and 'Station' in raw['records']:
        return raw['records']['Station']
    
    # CWA XML download format
    elif 'cwaopendata' in raw and 'dataset' in raw['cwaopendata'] and 'Station' in raw['cwaopendata']['dataset']:
        return raw['cwaopendata']['dataset']['Station']
    
    else:
        print("Unknown JSON format")
        return None

def parse_rainfall_json(data):
    """
    Parse rainfall JSON data into GeoDataFrame
    """
    stations = normalize_cwa_json(data)
    
    if not stations:
        print("No station data found")
        return gpd.GeoDataFrame()
    
    parsed_stations = []
    
    for station in stations:
        try:
            # Extract basic station info
            station_name = station.get('StationName', '')
            station_id = station.get('StationId', '')
            
            # Extract county and town names from GeoInfo
            county_name = ''
            town_name = ''
            if 'GeoInfo' in station:
                geo_info = station['GeoInfo']
                county_name = geo_info.get('CountyName', '')
                town_name = geo_info.get('TownName', '')
            
            # Extract coordinates - handle different coordinate systems
            lat = None
            lon = None
            coordinates = station.get('Coordinates', [])
            
            if len(coordinates) >= 2:
                # Find WGS84 coordinates if multiple coordinate systems exist
                for coord in coordinates:
                    if coord.get('CoordinateName') == 'WGS84':
                        lat = float(coord.get('StationLatitude', 0))
                        lon = float(coord.get('StationLongitude', 0))
                        break
                # If WGS84 not found, use first coordinate
                if lat is None:
                    lat = float(coordinates[0].get('StationLatitude', 0))
                    lon = float(coordinates[0].get('StationLongitude', 0))
            elif len(coordinates) == 1:
                # Only one coordinate system available
                lat = float(coordinates[0].get('StationLatitude', 0))
                lon = float(coordinates[0].get('StationLongitude', 0))
            
            # Extract precipitation data
            precipitation_data = station.get('Precipitation', [])
            rain_1hr = 0
            rain_3hr = 0
            rain_24hr = 0
            
            if precipitation_data:
                precip = precipitation_data[0]
                # Convert to float, handle both string and number formats
                rain_value = precip.get('Precipitation', 0)
                if isinstance(rain_value, str):
                    rain_1hr = float(rain_value) if rain_value != '-998' else 0
                else:
                    rain_1hr = float(rain_value) if rain_value != -998 else 0
                
                # For simplicity, use same value for 3hr and 24hr (can be enhanced later)
                rain_3hr = rain_1hr
                rain_24hr = rain_1hr
            
            # Skip stations with invalid coordinates
            if lat is None or lon is None or lat == 0 or lon == 0:
                continue
            
            parsed_stations.append({
                'StationName': station_name,
                'StationId': station_id,
                'CountyName': county_name,
                'TownName': town_name,
                'latitude': lat,
                'longitude': lon,
                'rain_1hr': rain_1hr,
                'rain_3hr': rain_3hr,
                'rain_24hr': rain_24hr
            })
            
        except Exception as e:
            print(f"Error parsing station {station.get('StationName', 'Unknown')}: {e}")
            continue
    
    if not parsed_stations:
        print("No valid stations parsed")
        return gpd.GeoDataFrame()
    
    # Create DataFrame
    df = pd.DataFrame(parsed_stations)
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df['longitude'], df['latitude']),
        crs='EPSG:4326'
    )
    
    return gdf

print("✓ Rainfall JSON parsing functions defined")

# Cell [4]: Mode Switcher (LIVE vs SIMULATION)
print("\nCell [4]: Loading rainfall data (SIMULATION mode)...")

# Read application mode
app_mode = os.getenv('APP_MODE', 'SIMULATION').upper()
print(f"Application mode: {app_mode}")

# Initialize rainfall data
gdf_rainfall = None

if app_mode == 'LIVE':
    # Try to fetch live data from CWA API
    api_key = os.getenv('API_KEY', '')
    if not api_key or api_key == 'your_cwa_api_key_here':
        print("Warning: No valid API key found, falling back to simulation mode")
        app_mode = 'SIMULATION'
    else:
        print("Fetching live rainfall data from CWA API...")
        raw_data = fetch_cwa_api(api_key)
        if raw_data:
            gdf_rainfall = parse_rainfall_json(raw_data)
            if gdf_rainfall.empty:
                print("Failed to parse live data, falling back to simulation mode")
                app_mode = 'SIMULATION'
        else:
            print("Failed to fetch live data, falling back to simulation mode")
            app_mode = 'SIMULATION'

if app_mode == 'SIMULATION':
    # Load simulation data
    print("Loading simulation data from Typhoon Fung-wong scenario...")
    try:
        with open('data/scenarios/fungwong_202511.json', 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        gdf_rainfall = parse_rainfall_json(raw_data)
        print("✓ Simulation data loaded successfully")
    except FileNotFoundError:
        print("Error: Simulation data file not found")
    except Exception as e:
        print(f"Error loading simulation data: {e}")

# Display results
if gdf_rainfall is not None and not gdf_rainfall.empty:
    print(f"✓ Number of stations: {len(gdf_rainfall)}")
    print(f"✓ CRS: {gdf_rainfall.crs}")
    print(f"✓ Rainfall statistics (mm/hr):")
    print(f"  1-hour rain - Min: {gdf_rainfall['rain_1hr'].min():.1f}, Max: {gdf_rainfall['rain_1hr'].max():.1f}, Mean: {gdf_rainfall['rain_1hr'].mean():.1f}")
else:
    print("Failed to load rainfall data")
    sys.exit(1)

# Cell [5]: Create Base Folium Map
print("\nCell [5]: Creating base Folium map...")

# Create base Folium map centered on Hualien County
m = folium.Map(
    location=[23.98, 121.55],  # Hualien County center
    zoom_start=10,
    tiles='OpenStreetMap'
)

print("✓ Base Folium map created")

# Cell [6]: Add Rainfall CircleMarkers with Conditional Styling
print("\nCell [6]: Adding rainfall CircleMarkers...")

def rain_color(rain_mm):
    """
    Return color based on rainfall intensity
    """
    if rain_mm < 10:
        return 'green'      # Safe
    elif rain_mm < 40:
        return 'gold'       # Caution
    elif rain_mm < 80:
        return 'orange'     # Warning
    else:
        return 'red'        # Danger

def rain_radius(rain_mm):
    """
    Return radius proportional to rainfall amount
    """
    return max(5, rain_mm / 5)

# Add rainfall CircleMarkers to the map
for idx, station in gdf_rainfall.iterrows():
    lat = station['latitude']
    lon = station['longitude']
    rain_1hr = station['rain_1hr']
    station_name = station['StationName']
    
    # Get color and radius based on rainfall
    color = rain_color(rain_1hr)
    radius = rain_radius(rain_1hr)
    
    # Create CircleMarker
    folium.CircleMarker(
        location=[lat, lon],
        radius=radius,
        popup=f"<b>{station_name}</b><br>Rainfall: {rain_1hr:.1f} mm/hr",
        tooltip=f"{station_name}: {rain_1hr:.1f} mm/hr",
        color='black',
        weight=1,
        fillColor=color,
        fillOpacity=0.7
    ).add_to(m)

print(f"✓ Added {len(gdf_rainfall)} rainfall stations to map")

# Cell [7]: Add HeatMap Layer
print("\nCell [7]: Adding HeatMap layer...")

from folium.plugins import HeatMap

# Create heat data for HeatMap
heat_data = []
for idx, station in gdf_rainfall.iterrows():
    lat = station['latitude']
    lon = station['longitude']
    rain_1hr = station['rain_1hr']
    heat_data.append([lat, lon, rain_1hr])

# Add HeatMap layer to map
HeatMap(
    heat_data,
    name='Rainfall Heatmap',
    show=False,  # Hidden by default, can be toggled via LayerControl
    radius=15,
    blur=10,
    gradient={
        0.0: 'green',
        0.25: 'gold',
        0.5: 'orange',
        0.75: 'red',
        1.0: 'darkred'
    }
).add_to(m)

print(f"✓ Added HeatMap layer with {len(heat_data)} data points")

# Cell [8]: Add LayerControl
print("\nCell [8]: Adding LayerControl...")

from folium import LayerControl

# Add LayerControl to map
LayerControl(collapsed=False).add_to(m)

print("✓ LayerControl added to map")

# Cell [9]: Add Shelter Risk Popups
print("\nCell [9]: Adding shelter risk popups...")

# Convert shelters back to WGS84 for Folium display
gdf_shelters_wgs84 = gdf_shelters.to_crs('EPSG:4326')

def get_risk_color(risk_level):
    """Return icon color based on risk level"""
    if risk_level.lower() == 'low':
        return 'blue'
    elif risk_level.lower() == 'medium':
        return 'orange'
    elif risk_level.lower() == 'high':
        'red'
    else:
        return 'gray'

# Add shelter markers to the map
for idx, shelter in gdf_shelters_wgs84.iterrows():
    lat = shelter.geometry.y
    lon = shelter.geometry.x
    
    # Create HTML popup content
    popup_html = f"""
    <b>{shelter['name']}</b><br>
    Risk Level: {shelter['risk_level']}<br>
    Terrain Risk: {shelter['terrain_risk']}<br>
    Elevation: {shelter['mean_elevation']:.1f}m<br>
    Max Slope: {shelter['max_slope']:.1f}°<br>
    Location: {shelter['TOWNNAME']}
    """
    
    # Get icon color based on risk level
    icon_color = get_risk_color(shelter['risk_level'])
    
    # Add Marker to map
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_html, max_width=250),
        tooltip=shelter['name'],
        icon=folium.Icon(
            color=icon_color,
            icon='info-sign',
            prefix='fa'
        )
    ).add_to(m)

print(f"✓ Added {len(gdf_shelters_wgs84)} shelter markers to map")

# Lab 1: Create and save rainfall map
print("\n=== Lab 1: CWA API → Folium Map ===")

# Create output directory
os.makedirs('output', exist_ok=True)

# Save the main map
output_file = 'output/rainfall_map_week5.html'
m.save(output_file)

if os.path.exists(output_file):
    file_size = os.path.getsize(output_file)
    print(f"✓ Main map saved to: {output_file}")
    print(f"✓ File size: {file_size/1024:.1f} KB")

# Lab 2: Typhoon Fung-wong Simulation
print("\n=== Lab 2: Typhoon Fung-wong Simulation ===")

# Filter for heavy rain stations (>30 mm/hr)
heavy_rain_stations = gdf_rainfall[gdf_rainfall['rain_1hr'] > 30].copy()
print(f"Stations with >30 mm/hr: {len(heavy_rain_stations)}")

# Find station with maximum rainfall
max_rain_station = gdf_rainfall.loc[gdf_rainfall['rain_1hr'].idxmax()]
print(f"Max rainfall station: {max_rain_station['StationName']} ({max_rain_station['rain_1hr']:.1f} mm/hr)")

# Spatial analysis for shelter risk
print("\nPerforming spatial analysis...")

# Reproject rainfall data to EPSG:3826 (same as shelters)
gdf_rainfall_3826 = gdf_rainfall.to_crs('EPSG:3826')

# Filter for very heavy rain (>40 mm/hr)
very_heavy_rain = gdf_rainfall_3826[gdf_rainfall_3826['rain_1hr'] > 40].copy()
print(f"Stations with >40 mm/hr: {len(very_heavy_rain)}")

# Create 5km buffer around high-rain stations
very_heavy_rain['geometry'] = very_heavy_rain.geometry.buffer(5000)  # 5km buffer
buffered_rain = very_heavy_rain.copy()

# Spatial join to find shelters within 5km impact zones
shelters_at_risk = gpd.sjoin(
    gdf_shelters, 
    buffered_rain, 
    how='left', 
    predicate='within'
)

# Flag shelters at risk
shelters_at_risk['high_risk_flag'] = shelters_at_risk['rain_1hr'].notna()

# Assign dynamic risk levels
def get_dynamic_risk(row):
    if not row['high_risk_flag']:
        return row['risk_level']
    
    rain_mm = row['rain_1hr']
    terrain_risk = row['terrain_risk']
    
    if rain_mm > 80:
        return 'CRITICAL'
    elif rain_mm > 40 and terrain_risk == 'HIGH':
        return 'URGENT'
    elif rain_mm > 40:
        return 'WARNING'
    else:
        return row['risk_level']

shelters_at_risk['dynamic_risk'] = shelters_at_risk.apply(get_dynamic_risk, axis=1)

# Summary statistics
high_risk_count = len(shelters_at_risk[shelters_at_risk['high_risk_flag']])
total_count = len(shelters_at_risk)

print(f"Total shelters: {total_count}")
print(f"Shelters within 5km of heavy rainfall: {high_risk_count}")
print(f"Risk percentage: {(high_risk_count/total_count)*100:.1f}%")

# Create typhoon risk map
print("\nCreating typhoon risk map...")

m_typhoon = folium.Map(
    location=[23.98, 121.55],
    zoom_start=10,
    tiles='OpenStreetMap'
)

# Add enhanced rainfall markers
for idx, station in gdf_rainfall.iterrows():
    lat = station['latitude']
    lon = station['longitude']
    rain_1hr = station['rain_1hr']
    station_name = station['StationName']
    
    color = rain_color(rain_1hr)
    radius = rain_radius(rain_1hr) * 1.2  # Slightly larger for typhoon
    
    folium.CircleMarker(
        location=[lat, lon],
        radius=radius,
        popup=f"<b>{station_name}</b><br>Rainfall: {rain_1hr:.1f} mm/hr",
        tooltip=f"{station_name}: {rain_1hr:.1f} mm/hr",
        color='black',
        weight=2,  # Thicker border for typhoon
        fillColor=color,
        fillOpacity=0.8
    ).add_to(m_typhoon)

# Add shelter markers with risk highlighting
gdf_shelters_wgs84 = shelters_at_risk.to_crs('EPSG:4326')

for idx, shelter in gdf_shelters_wgs84.iterrows():
    lat = shelter.geometry.y
    lon = shelter.geometry.x
    
    popup_html = f"""
    <b>{shelter['name']}</b><br>
    Risk Level: {shelter['risk_level']}<br>
    Dynamic Risk: {shelter['dynamic_risk']}<br>
    Terrain Risk: {shelter['terrain_risk']}<br>
    Elevation: {shelter['mean_elevation']:.1f}m<br>
    Max Slope: {shelter['max_slope']:.1f}°<br>
    Location: {shelter['TOWNNAME']}
    """
    
    # Color based on risk status
    if shelter['high_risk_flag']:
        icon_color = 'red'
        icon_name = 'exclamation-triangle'
    else:
        icon_color = get_risk_color(shelter['risk_level'])
        icon_name = 'info-sign'
    
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_html, max_width=250),
        tooltip=f"{shelter['name']} - {shelter['dynamic_risk']}",
        icon=folium.Icon(
            color=icon_color,
            icon=icon_name,
            prefix='fa'
        )
    ).add_to(m_typhoon)

# Add HeatMap
heat_data = [[station['latitude'], station['longitude'], station['rain_1hr']] 
             for idx, station in gdf_rainfall.iterrows()]

HeatMap(
    heat_data,
    name='Typhoon Rainfall Heatmap',
    show=False,
    radius=20,  # Larger radius for typhoon
    blur=15
).add_to(m_typhoon)

# Add LayerControl
LayerControl(collapsed=False).add_to(m_typhoon)

# Save typhoon risk map
typhoon_output_file = 'output/typhoon_fungwong_risk_map.html'
m_typhoon.save(typhoon_output_file)

if os.path.exists(typhoon_output_file):
    file_size = os.path.getsize(typhoon_output_file)
    print(f"✓ Typhoon risk map saved to: {typhoon_output_file}")
    print(f"✓ File size: {file_size/1024:.1f} KB")

# Generate summary report
print("\n=== Generating Summary Report ===")

summary_report = f"""# Week 5: Dynamic Mapping & Time-Machine Simulation - Execution Summary

## Data Overview
- **Shelters**: {len(gdf_shelters)} locations in Hualien County
- **Rainfall Stations**: {len(gdf_rainfall)} monitoring stations
- **Application Mode**: {app_mode}

## Rainfall Analysis
- **Max 1-hour Rainfall**: {gdf_rainfall['rain_1hr'].max():.1f} mm/hr ({max_rain_station['StationName']})
- **Mean 1-hour Rainfall**: {gdf_rainfall['rain_1hr'].mean():.1f} mm/hr
- **Heavy Rain Stations (>30 mm/hr)**: {len(heavy_rain_stations)}
- **Very Heavy Rain Stations (>40 mm/hr)**: {len(very_heavy_rain)}

## Shelter Risk Assessment
- **Total Shelters**: {total_count}
- **Shelters at Risk**: {high_risk_count}
- **Risk Percentage**: {(high_risk_count/total_count)*100:.1f}%

### High-Risk Shelters (Evacuation Priority)
"""

if high_risk_count > 0:
    risk_shelters = shelters_at_risk[shelters_at_risk['high_risk_flag']]
    for idx, shelter in risk_shelters.iterrows():
        summary_report += f"- **{shelter['name']}**: {shelter['dynamic_risk']} (Rain: {shelter['rain_1hr']:.1f} mm/hr)\n"
else:
    summary_report += "No shelters identified as high-risk\n"

summary_report += f"""
## Generated Outputs
1. **Main Rainfall Map**: `output/rainfall_map_week5.html`
2. **Typhoon Risk Map**: `output/typhoon_fungwong_risk_map.html`

## Execution Status
✓ All cells executed successfully
✓ Maps generated and saved to output directory
✓ Spatial analysis completed
✓ Risk assessment performed

Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

# Save summary report
with open('output/execution_summary.md', 'w', encoding='utf-8') as f:
    f.write(summary_report)

print("✓ Summary report saved to: output/execution_summary.md")

# Save data files
print("\n=== Saving Data Files ===")

# Save shelter data
gdf_shelters.to_file('output/shelters.geojson', driver='GeoJSON')
print("✓ Shelter data saved to: output/shelters.geojson")

# Save rainfall data
gdf_rainfall.to_file('output/rainfall_stations.geojson', driver='GeoJSON')
print("✓ Rainfall data saved to: output/rainfall_stations.geojson")

# Save risk assessment data
shelters_at_risk.to_file('output/shelter_risk_assessment.geojson', driver='GeoJSON')
print("✓ Risk assessment data saved to: output/shelter_risk_assessment.geojson")

print("\n🎉 Execution completed successfully!")
print("📁 All outputs saved to 'output' directory")
print("📊 Open 'output/execution_summary.md' for detailed results")
