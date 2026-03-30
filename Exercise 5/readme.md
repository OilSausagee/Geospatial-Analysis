# Week 5 Exercise: ARIA v3.0

## 📋 Exercise Overview

This exercise guides you through building a dynamic risk monitoring system that integrates shelter data with real-time rainfall monitoring.

## 🎯 Learning Objectives

- Implement mode switching between LIVE API and SIMULATION data
- Normalize JSON data from different sources (CWA API vs CoLife)
- Apply dynamic risk classification using multiple factors
- Create professional interactive maps with Folium
- Understand spatial analysis concepts (buffers, spatial joins)

## 📁 File Structure

```
Exercise 5/
├── Week5-Student.ipynb     # Main exercise notebook
├── data/
│   └── scenarios/
│       └── fungwong_202511.json  # Typhoon simulation data
├── output/                  # Generated maps and results
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
└── readme.md              # This file
```

## 🚀 Getting Started

1. **Setup Environment**:
   ```bash
   pip install -r requirements.txt
   cp .env.example .env  # Edit with your API keys
   ```

2. **Run the Exercise**:
   ```bash
   jupyter notebook Week5-Student.ipynb
   ```

3. **Complete TODO Sections**:
   - Read each section carefully
   - Fill in the missing code
   - Test your implementation
   - Generate the interactive map

## 📊 Data Sources

- **Shelter Data**: Week 3 CSV file with shelter locations
- **Terrain Risk**: Week 4 JSON analysis results
- **Rainfall Data**: Typhoon Fung-wong simulation (2025/11/11)

## 🔧 Technical Requirements

- Python 3.8+
- Required packages (see requirements.txt)
- CWA API key (for LIVE mode)
- Internet connection (for LIVE mode)

## 🎯 Success Criteria

✅ All TODO sections completed  
✅ Interactive map generated  
✅ Dynamic risk classification working  
✅ No runtime errors  
✅ Professional visualization  

## 🆘 Troubleshooting

### Common Issues:

1. **API Key Errors**:
   - Ensure `.env` file is properly configured
   - Check API key validity
   - Use SIMULATION mode if API fails

2. **CRS Errors**:
   - Verify coordinate system consistency
   - Check buffer analysis parameters
   - Ensure proper CRS transformations

3. **Data Loading Issues**:
   - Verify file paths in `.env`
   - Check data file integrity
   - Ensure proper JSON format

## 💡 Tips

- Start with SIMULATION mode to test your code
- Use print statements to debug data flow
- Check the solution notebook if stuck
- Experiment with different parameters

## 🏆 Bonus Challenges

- Implement Gemini AI integration
- Add custom map layers
- Create animated rainfall visualization
- Develop alert notification system

---

**Good luck building your ARIA v3.0 system! 🌟**
