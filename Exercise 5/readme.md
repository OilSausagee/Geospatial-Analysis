# Week 5: Dynamic Mapping & Time-Machine Simulation

## 📋 Overview

This project demonstrates real-time rainfall monitoring and typhoon simulation using CWA (Central Weather Administration) data, interactive mapping with Folium, and spatial analysis for emergency shelter risk assessment.

### 🎯 Learning Objectives

1. **API Integration**: Call CWA real-time rainfall API
2. **Data Parsing**: Parse nested JSON into GeoDataFrame
3. **Interactive Mapping**: Build Folium maps with conditional styling
4. **Time-Machine Simulation**: Replay Typhoon Fung-wong (2025) as stress test
5. **Spatial Analysis**: Overlay dynamic rainfall with shelter risk data

## 🛠️ Technical Stack

- **Python 3.x**
- **Geopandas**: Spatial data analysis
- **Folium**: Interactive mapping
- **Requests**: HTTP API calls
- **python-dotenv**: Environment variable management
- **branca**: Color scales for maps

## 📁 Project Structure

```
Exercise 5/
├── Week5-Student.ipynb          # Main Jupyter notebook
├── run_notebook.py              # Python execution script
├── .env                         # Environment configuration
├── data/
│   └── scenarios/
│       └── fungwong_202511.json # Typhoon simulation data
├── output/                      # Generated outputs
│   ├── rainfall_map_week5.html
│   ├── typhoon_fungwong_risk_map.html
│   ├── execution_summary.md
│   ├── shelters.geojson
│   ├── rainfall_stations.geojson
│   └── shelter_risk_assessment.geojson
└── README.md                    # This file
```

## 🚀 Quick Start

### Prerequisites

```bash
pip install geopandas folium requests python-dotenv branca jupyter
```

### Setup

1. **Clone/Download** the project files
2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your CWA API key
   ```
3. **Run the Notebook**:
   ```bash
   jupyter notebook Week5-Student.ipynb
   ```
   Or execute directly:
   ```bash
   python run_notebook.py
   ```

## 📊 Key Features

### 1. **Dual Mode Operation**

- **LIVE Mode**: Fetches real-time data from CWA API
- **SIMULATION Mode**: Uses typhoon scenario data for testing

### 2. **Interactive Maps**

- **Color-coded rainfall stations** (Green → Gold → Orange → Red)
- **Dynamic circle sizing** based on rainfall intensity
- **HeatMap overlay** for rainfall density visualization
- **Layer controls** for toggling different data layers

### 3. **Risk Assessment**

- **Spatial analysis** with 5km buffer zones
- **Dynamic risk levels**: CRITICAL, URGENT, WARNING
- **Terrain-based risk evaluation**
- **Evacuation priority ranking**

### 4. **Data Processing**

- **Multi-format JSON parsing** (CWA API, converted CSV, XML)
- **Coordinate system handling** (WGS84, TWD67, TWD97)
- **Data quality filtering** (-998 sentinel values)

## 🗺️ Map Visualizations

### Main Rainfall Map
- **File**: `output/rainfall_map_week5.html`
- **Features**: Real-time rainfall stations, shelter locations, HeatMap
- **Interactivity**: Popups, tooltips, layer controls

### Typhoon Risk Map
- **File**: `output/typhoon_fungwong_risk_map.html`
- **Features**: Enhanced typhoon visualization, risk-highlighted shelters
- **Purpose**: Emergency response planning

## 📈 Analysis Results

### Typhoon Fung-wong Simulation (2025-11-11)

**Rainfall Statistics:**
- **Maximum**: 130.5 mm/hr (蘇澳)
- **Mean**: 66.0 mm/hr
- **Heavy Rain Stations (>30mm/hr)**: 9/10 stations
- **Very Heavy Rain (>40mm/hr)**: 8/10 stations

**Shelter Risk Assessment:**
- **Total Shelters**: 13 locations
- **At-Risk Shelters**: 9 (60.0%)
- **Critical Priority**: 秀林鄉太魯閣避難所 (95.8 mm/hr)

### Risk Classification Matrix

| Rainfall (mm/hr) | Terrain Risk | Dynamic Risk | Action |
|------------------|--------------|--------------|--------|
| >80 | ANY | CRITICAL | Immediate evacuation |
| >40 | HIGH | URGENT | Priority evacuation |
| >40 | LOW/MEDIUM | WARNING | Monitor closely |
| <40 | ANY | Standard | Normal operation |

## 🔧 Technical Implementation

### Core Functions

```python
# API Integration
def fetch_cwa_api(api_key):
    """Fetch real-time rainfall data from CWA API"""

# Data Parsing
def parse_rainfall_json(data):
    """Parse multi-format JSON into GeoDataFrame"""

# Visualization
def rain_color(rain_mm):
    """Return color based on rainfall intensity"""

# Spatial Analysis
def get_dynamic_risk(row):
    """Calculate dynamic risk based on rainfall and terrain"""
```

### Key Insights

1. **Mode Switching**: Only 1-2 lines needed to switch between LIVE/SIMULATION
2. **CRS Importance**: Critical to convert coordinate systems before spatial operations
3. **Data Quality**: -998 sentinel values require special handling
4. **Buffer Analysis**: 5km radius appropriate for rainfall impact zones

## 🎯 Learning Outcomes

### Technical Skills
- **API Integration**: RESTful API calls with error handling
- **Spatial Analysis**: Buffer operations, spatial joins
- **Data Visualization**: Interactive mapping with Folium
- **Data Cleaning**: Multi-format parsing, coordinate system conversion

### Analytical Skills
- **Risk Assessment**: Multi-factor risk evaluation
- **Emergency Planning**: Evacuation priority determination
- **Data Interpretation**: Weather pattern analysis
- **Spatial Reasoning**: Geographic impact assessment

## 🤔 Reflections & Learnings

### Challenges Overcome

1. **JSON Format Variations**
   - Problem: Different data sources had different structures
   - Solution: Created normalization functions

2. **Coordinate System Confusion**
   - Problem: Multiple coordinate systems in same dataset
   - Solution: Implemented coordinate system detection and conversion

3. **Spatial Analysis Accuracy**
   - Problem: Incorrect buffer calculations due to wrong CRS
   - Solution: Ensured proper CRS conversion before operations

### Key Takeaways

1. **Data Quality is Critical**: Real-world data is messy and requires robust cleaning
2. **Coordinate Systems Matter**: CRS conversion is essential for accurate spatial analysis
3. **Mode Flexibility**: Designing for both real-time and simulation scenarios improves robustness
4. **Visualization Impact**: Interactive maps significantly improve data comprehension

## 📝 My Reflection Answers

### 1. Code Changes Between Modes
**Only 1-2 lines** needed to switch between LIVE and SIMULATION mode. The elegant design uses the same parsing function for both data sources.

### 2. CRS Conversion Importance
Forgetting CRS conversion causes **spatial analysis failure** - either complete errors or incorrect results. 5km buffer becomes 5° (≈555km) without proper conversion.

### 3. CWA's -998 Sentinel Value
CWA uses -998 instead of NaN for **legacy compatibility**, **data quality control**, and **cross-system compatibility** in meteorological monitoring.

### 4. Priority Evacuation Shelter
**秀林鄉太魯閣避難所** - CRITICAL risk with 95.8 mm/hr rainfall, high terrain risk, and mountainous location prone to landslides.

### 5. Challenges & Solutions
- **JSON variations** → Normalization functions
- **Coordinate confusion** → CRS detection/conversion
- **Data types** → Type checking and conversion
- **Spatial accuracy** → Proper CRS before operations

## 🔮 Future Enhancements

1. **Real-time Alerts**: SMS/email notifications for critical risk levels
2. **Historical Analysis**: Compare multiple typhoon scenarios
3. **Machine Learning**: Predict risk based on weather patterns
4. **Mobile Integration**: Responsive maps for field operations
5. **Multi-source Data**: Integrate satellite imagery and radar data

## 📞 Contact & Support

For questions or issues:
- **Jupyter Notebook**: `Week5-Student.ipynb`
- **Execution Script**: `run_notebook.py`
- **Output Directory**: `output/` for all generated files

---

**Generated**: 2026-03-24  
**Version**: Week 5 Complete Implementation  
**Status**: ✅ Fully Functional with All Labs Completed