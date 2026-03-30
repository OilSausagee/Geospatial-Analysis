# Week 5 Assignment: ARIA v3.0 - 全自動區域受災衝擊評估系統

## 專案概述

ARIA v3.0 是一個動態風險監測系統，整合了 Week 3-4 的避難所風險資料與即時雨量監測，能在鳳凰颱風等極端天氣事件中提供即時的災害風險評估。

## 系統架構

### 核心功能
- **模式切換器**: 支援 LIVE (CWA API) 與 SIMULATION (歷史資料) 模式
- **動態風險分級**: CRITICAL/URGENT/WARNING/SAFE 四級分類
- **空間疊合分析**: 5km 雨量影響範圍與避難所空間關聯
- **互動地圖**: Folium 視覺化與 HeatMap 雨量分佈

### 資料來源
- **向量資料**: W3 避難所河川距離、W4 地形坡度風險
- **雨量資料**: CWA O-A0002-001 API 或 CoLife 歷史資料庫
- **測試情境**: 2025年鳳凰颱風 (fungwong_202511.json)

## AI 診斷日誌

### 🔧 問題解決記錄

#### 1. Folium 地圖經緯度填反問題

**問題描述**: 
初始版本中 Folium Marker 使用錯誤的座標順序 `[longitude, latitude]`，導致地圖上所有點位都顯示在錯誤位置。

**診斷過程**:
1. 發現避難所標記點全部集中在非洲西部，明顯不是台灣
2. 檢查 Folium 文件確認座標順序應為 `[latitude, longitude]`
3. 追蹤程式碼發現 Point 建立使用 `(lon, lat)` 但 Folium 需要 `(lat, lon)`

**解決方案**:
```python
# 錯誤寫法
folium.Marker(location=[lon, lat])  # 會跑到非洲

# 正確寫法  
lat = shelter.geometry.y
lon = shelter.geometry.x
folium.Marker(location=[lat, lon])  # 正確顯示在台灣
```

**學習重點**: 
- GeoDataFrame 使用 (x, y) = (lon, lat)
- Folium 需要 [lat, lon] 順序
- 需要特別注意不同函式庫的座標慣例

#### 2. CWA API -998 無資料值處理

**問題描述**:
CWA API 使用 `-998` 表示無效資料，若未過濾會導致地圖顏色異常（極大雨量假象）。

**診斷過程**:
1. 發現地圖上某些雨量站顯示為極大紅色圓圈
2. 檢查原始資料發現這些站點的雨量值為 `-998`
3. 查詢 CWA API 文件確認 `-998` 為無資料標記

**解決方案**:
```python
# 在 normalize_cwa_json() 中加入過濾
rainfall_data = {
    'Past1hr': float(rainfall_element.get('Past1hr', {}).get('Precipitation', 0)),
    'Past24hr': float(rainfall_element.get('Past24hr', {}).get('Precipitation', 0))
}

# 過濾 -998 無資料值
if rainfall_data['Past1hr'] == -998 or rainfall_data['Past24hr'] == -998:
    continue  # 跳過此站點
```

**學習重點**:
- API 資料品質檢查的重要性
- 無效資料的標準化處理流程
- 資料清洗對視覺化的影響

#### 3. CRS 未對齊導致 sjoin 結果為空

**問題描述**:
執行 spatial join 時結果為空，發現是雨量站與避難所的座標系統不一致。

**診斷過程**:
1. `gpd.sjoin()` 回傳空的 GeoDataFrame
2. 檢查 CRS 發現雨量站為 EPSG:4326，避難所為 EPSG:3826
3. 確認 buffer 分析需要投影座標系統

**解決方案**:
```python
# 統一轉換到 EPSG:3826 進行分析
rainfall_gdf_3826 = rainfall_gdf.to_crs('EPSG:3826')
shelters_gdf_3826 = shelters_gdf.to_crs('EPSG:3826')

# CRS 一致性檢查
assert str(shelters_gdf_3826.crs) == str(buffer_gdf.crs), "CRS MISMATCH!"

# 執行 spatial join
shelters_in_rainfall = gpd.sjoin(shelters_gdf_3826, buffer_gdf, 
                                how='inner', predicate='intersects')
```

**學習重點**:
- 空間分析前必須檢查 CRS 一致性
- 投影座標系統 (EPSG:3826) 適合距離計算
- 地理座標系統 (EPSG:4326) 適合視覺化

## 使用說明

### 環境設定
1. 複製 `.env.example` 為 `.env`
2. 設定必要的環境變數
3. 安裝所需套件：`pip install -r requirements.txt`

### 執行分析
```bash
jupyter notebook ARIA_v3.ipynb
```

### 輸出檔案
- `outputs/ARIA_v3_Fungwong.html`: 互動式風險地圖
- 分析結果會顯示在 notebook 輸出中

## 技術規格

- **座標系統**: EPSG:3826 (分析) / EPSG:4326 (視覺化)
- **緩衝距離**: 5km (可透過環境變數調整)
- **風險閾值**: Critical 80mm/hr, Urgent 40mm/hr
- **支援縣市**: 花蓮縣、宜蘭縣

## 系統限制

- CWA API 可能會超時，系統會自動切換到模擬資料
- HeatMap 在山區可能因測站分佈不均有盲區
- 地形風險資料依賴 W4 的分析結果

## 未來改進

- 整合更多即時資料來源
- 加入預警通知機制
- 優化 HeatMap 插值演算法
- 支援更多縣市的分析

---

*"A monitoring system that works in the sun is a toy. A system that survives Typhoon Fung-wong is a tool."*
