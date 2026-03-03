# Hw2 Exercise 2: 氣象站API座標系統比較分析

## 專案概述
本專案分析氣象站API中每個測站的兩組座標，將其都視為WGS84座標系統，在同一張地圖上視覺化並統計座標差距。

## 目標
1. 取得氣象站API資料
2. 提取每個測站的兩組座標
3. 將座標視覺化在同一張地圖上
4. 統計分析兩組座標的差距
5. 評估座標系統差異影響

## 檔案結構
```
ex2/
├── README.md                    # 本檔案
├── weather_station_analysis.py  # 主要分析程式
├── coordinate_comparison.py     # 座標比較模組
├── visualization.py             # 視覺化模組
├── data/                        # 資料目錄
│   ├── weather_stations.json    # 原始API資料
│   ├── processed_data.csv       # 處理後的資料
│   └── coordinate_stats.csv     # 座標統計結果
├── output/                      # 輸出目錄
│   ├── station_map.html         # 互動式地圖
│   ├── coordinate_comparison.png # 座標比較圖
│   └── statistics_report.html   # 統計報告
└── requirements.txt             # Python套件需求
```

## 分析方法

### 1. 資料取得
- 使用氣象站API取得所有測站資訊
- 提取每個測站的兩組座標（通常為TWD97和WGS84）

### 2. 座標處理
- 將所有座標都視為WGS84處理
- 計算兩組座標間的距離和方向
- 統計座標差距分佈

### 3. 視覺化
- 使用Folium建立互動式地圖
- 不同顏色標示兩組座標
- 連線顯示座標差距

### 4. 統計分析
- 計算平均距離差距
- 分析最大/最小差距
- 評估系統性偏移

## 預期結果
- 互動式地圖顯示所有測站座標
- 座標差距統計報告
- 座標系統轉換建議

## 技術棧
- Python 3.x
- Requests (API呼叫)
- Pandas (資料處理)
- Folium (地圖視覺化)
- Matplotlib/Seaborn (統計圖表)
- Geopy (地理計算)

## 使用方法
```bash
# 安裝需求套件
pip install -r requirements.txt

# 執行分析
python weather_station_analysis.py

# 查看結果
open output/station_map.html
```

---
*分支：crs_compare*  
*建立日期：2026年3月3日*
