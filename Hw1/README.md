# AQI Analysis Project

即時空氣品質指標（AQI）分析與視覺化專案

## 功能特色

- 🌍 **即時 AQI 數據獲取**：串接環境部 API 獲取全台測站即時數據
- 📍 **互動式地圖視覺化**：使用 Folium 生成地圖，根據 AQI 等級分色顯示
- 📊 **距離計算**：計算各測站到台北車站的距離
- 📈 **資料匯出**：將測站資料匯出為 CSV 檔案
- 🚀 **雲端備份**：自動備份到 GitHub

## AQI 分色系統

- 🟢 **0-50**：綠色（良好）
- 🟡 **51-100**：黃色（普通）
- 🔴 **101+**：紅色（不健康）

## 檔案結構

```
├── aqi_mapper.py      # 主程式
├── requirements.txt   # Python 套件需求
├── setup.py          # 環境設定腳本
├── .env              # 環境變數（API Key）
├── .gitignore        # Git 忽略檔案
├── README.md         # 專案說明
└── outputs/          # 輸出檔案目錄
    ├── aqi_map.html      # 互動式 AQI 地圖
    └── aqi_stations.csv  # 測站資料 CSV
```

## 安裝與使用

### 1. 環境設定

```bash
# 執行環境設定腳本
python3 setup.py
```

### 2. 設定 API Key

在 `.env` 檔案中設定您的環境部 API Key：

```bash
# 從 https://data.moenv.gov.tw/api_term 申請
EPA_API_KEY=your_api_key_here
```

### 3. 執行程式

```bash
# 執行主程式
python3 aqi_mapper.py
```

### 4. 查看結果

- 開啟 `outputs/aqi_map.html` 查看互動式地圖
- 查看 `outputs/aqi_stations.csv` 分析測站資料

## 輸出檔案

### AQI 地圖 (`outputs/aqi_map.html`)
- 顯示全台 84 個測站的即時 AQI 數據
- 點擊測站可查看詳細資訊（站名、所在地、AQI 數值、等級）
- 根據 AQI 等級使用不同顏色標示

### 測站資料 (`outputs/aqi_stations.csv`)
包含以下欄位：
- 測站名稱
- 縣市
- AQI 數值
- 等級
- 緯度、經度
- 距離台北車站（公里）

## 技術棧

- **Python 3.9+**
- **Requests**：API 串接
- **Folium**：地圖視覺化
- **Pandas**：資料處理
- **Python-dotenv**：環境變數管理

## API 資料來源

環境部環境資料開放平台：https://data.moenv.gov.tw/

## 授權

MIT License

## 作者

AQI Analysis Project
