# ARIA v3.0 - Advanced Rainfall Impact Assessment

## 🎯 Mission Overview
Complete CWA rainfall analysis system for 花蓮縣 emergency shelters with AI-powered tactical advisor.

---

## 📁 Project Structure
```
Week-5/
├── Hw5/                          # Main analysis directory
│   ├── cwa_rainfall_analysis.ipynb    # Complete analysis notebook
│   ├── data/                           # Data files
│   ├── outputs/                        # Generated outputs
│   │   ├── ARIA_v3_Fungwong.html      # Interactive map
│   │   └── README.md                   # Analysis report
│   ├── .env.example                    # Environment template
│   └── Homework-Week5.md              # Assignment details
└── Exercise 5/                    # Lab exercises (optional)
```

---

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Copy environment template
cp .env.example Week-5/Hw5/.env

# Fill in your API keys
# Edit Week-5/Hw5/.env with your actual keys
```

### 2. Install Dependencies
```bash
cd Week-5/Hw5
pip install -r requirements.txt
```

### 3. Run Analysis
```bash
cd Week-5/Hw5
jupyter notebook cwa_rainfall_analysis.ipynb
```

---

## 🛡️ Security Notice

**⚠️ Important**: This repository uses environment variables for API keys:
- `.env` files are excluded from version control
- Use `.env.example` as template
- Never commit actual API keys to repository

---

## 📊 Features Implemented

### Core Functionality
- ✅ **Mode Switcher**: LIVE/SIMULATION with API fallback
- ✅ **Dynamic Risk Classification**: CRITICAL/URGENT/WARNING/SAFE
- ✅ **Spatial Analysis**: CRS-aligned buffer analysis
- ✅ **Interactive Maps**: Folium with HeatMap and LayerControl

### Advanced Features
- ✅ **AI Tactical Advisor**: Gemini SDK integration
- ✅ **Professional Infrastructure**: Environment-based configuration
- ✅ **Comprehensive Error Handling**: Robust data validation
- ✅ **AI Diagnostic Logs**: Technical challenges documentation

---

## 📈 Analysis Results

### Target Area: 花蓮縣
- **Shelters Analyzed**: 198
- **Rainfall Stations**: 97  
- **Total Capacity**: 105,714 people
- **Risk Classification**: All SAFE (simulation mode)

---

## 🤖 AI Integration

### Gemini Tactical Advisor
- **Top Risk Selection**: Automatically identifies high-priority shelters
- **Expert Recommendations**: Disaster response expert advice
- **Enhanced Visualization**: AI insights in map popups

---

## 🔧 Technical Implementation

### CRS Management
- **Triple Check**: 4326 → 3826 → 4326
- **Coordinate Handling**: WGS84/TWD67 selection
- **Buffer Units**: Proper 5km implementation

### Data Quality
- **-998 Filtering**: Invalid rainfall handling
- **Coordinate Validation**: Proper lat/lon ordering
- **Error Recovery**: Graceful fallbacks

---

## 📝 Deliverables

1. **✅ GitHub Repository**: https://github.com/OilSausagee/Geospatial-Analysis/tree/Week-5
2. **✅ Analysis Notebook**: `Hw5/cwa_rainfall_analysis.ipynb`
3. **✅ Interactive Map**: `Hw5/outputs/ARIA_v3_Fungwong.html`
4. **✅ Documentation**: `Hw5/outputs/README.md` with AI logs

---

## 🎯 Evaluation Criteria

| Category | Weight | Status |
|----------|--------|--------|
| Mode Switcher + API | 20% | ✅ Complete |
| Spatial Analysis | 25% | ✅ Complete |
| Folium Map Quality | 25% | ✅ Complete |
| Professional Standards | 15% | ✅ Complete |
| Bonus: AI Integration | 15% | ✅ Complete |

---

*"A monitoring system that works in the sun is a toy. A system that survives Typhoon Fung-wong is a tool."*
