#!/usr/bin/env python3
"""
即時 AQI 地圖視覺化程式
串接環境部 API 獲取全台即時 AQI 數據，並使用 folium 在地圖上標示測站位置
"""

import os
import requests
import folium
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import json
import urllib3
import math

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 載入環境變數
load_dotenv()

class AQIMapper:
    def __init__(self):
        self.api_key = os.getenv('EPA_API_KEY')
        if not self.api_key:
            raise ValueError("請在 .env 檔案中設定 EPA_API_KEY")
        
        self.api_url = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
        self.data = None
        # 台北車站坐標
        self.taipei_station = {
            'lat': 25.0478,
            'lon': 121.5170,
            'name': '台北車站'
        }
        
    def fetch_aqi_data(self):
        """獲取即時 AQI 數據"""
        try:
            params = {
                'api_key': self.api_key,
                'format': 'json'
            }
            
            print("正在獲取 AQI 數據...")
            response = requests.get(self.api_url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            
            data = response.json()
            
            # 檢查 API 回應格式
            if isinstance(data, list):
                # 如果直接回傳列表
                self.data = data
            elif isinstance(data, dict):
                # 如果回傳字典格式
                if data.get('success') == 'true':
                    self.data = data.get('records', [])
                else:
                    # 嘗試其他可能的欄位名稱
                    self.data = data.get('data', data.get('records', []))
            else:
                raise ValueError("未知的 API 回應格式")
                
            print(f"成功獲取 {len(self.data)} 筆測站數據")
            
            return self.data
            
        except requests.exceptions.RequestException as e:
            print(f"網路請求錯誤: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON 解析錯誤: {e}")
            return None
        except Exception as e:
            print(f"獲取數據時發生錯誤: {e}")
            return None
    
    def get_aqi_color(self, aqi_value):
        """根據 AQI 數值回傳對應顏色（3階段分色）"""
        try:
            aqi = int(aqi_value)
        except (ValueError, TypeError):
            return '#808080'  # 灰色表示無效數值
        
        if aqi <= 50:
            return '#00E400'  # 綠色
        elif aqi <= 100:
            return '#FFFF00'  # 黃色
        else:
            return '#FF0000'  # 紅色
    
    def get_aqi_level(self, aqi_value):
        """根據 AQI 數值回傳等級描述（3階段）"""
        try:
            aqi = int(aqi_value)
        except (ValueError, TypeError):
            return '資料異常'
        
        if aqi <= 50:
            return '良好'
        elif aqi <= 100:
            return '普通'
        else:
            return '不健康'
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """使用 Haversine 公式計算兩點間的距離（公里）"""
        # 將經緯度轉換為弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine 公式
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # 地球半徑（公里）
        r = 6371
        
        distance = r * c
        return round(distance, 2)
    
    def export_to_csv(self, filename='outputs/aqi_stations.csv'):
        """將測站資料匯出為 CSV 檔案"""
        if not self.data:
            print("沒有數據可以匯出")
            return False
        
        try:
            # 準備匯出資料
            export_data = []
            
            for station in self.data:
                try:
                    # 解析坐標
                    lat = float(station.get('latitude', 0))
                    lon = float(station.get('longitude', 0))
                    
                    if lat == 0 or lon == 0:
                        continue
                    
                    # 計算到台北車站的距離
                    distance = self.calculate_distance(
                        lat, lon,
                        self.taipei_station['lat'], self.taipei_station['lon']
                    )
                    
                    # 準備資料列
                    row = {
                        '測站名稱': station.get('sitename', '未知測站'),
                        '縣市': station.get('county', '未知縣市'),
                        'AQI': station.get('aqi', 'N/A'),
                        '等級': self.get_aqi_level(station.get('aqi', 'N/A')),
                        '緯度': lat,
                        '經度': lon,
                        '距離台北車站(km)': distance
                    }
                    
                    export_data.append(row)
                    
                except (ValueError, KeyError) as e:
                    print(f"處理測站資料時發生錯誤: {e}")
                    continue
            
            # 建立 DataFrame 並匯出
            df = pd.DataFrame(export_data)
            
            # 確保 outputs 目錄存在
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # 匯出 CSV
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"資料已匯出至: {filename}")
            print(f"共匯出 {len(export_data)} 筆測站資料")
            
            return True
            
        except Exception as e:
            print(f"匯出 CSV 時發生錯誤: {e}")
            return False
    
    def create_map(self):
        """建立 AQI 地圖"""
        if not self.data:
            print("沒有數據可以建立地圖")
            return None
        
        # 以台灣中心為初始地圖位置
        taiwan_center = [23.8, 120.9]
        
        # 建立地圖
        m = folium.Map(
            location=taiwan_center,
            zoom_start=7,
            tiles='OpenStreetMap'
        )
        
        # 添加 AQI 圖例（3階段）
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 200px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>AQI 等級圖例</h4>
        <p><i class="fa fa-circle" style="color:#00E400"></i> 0-50 良好</p>
        <p><i class="fa fa-circle" style="color:#FFFF00"></i> 51-100 普通</p>
        <p><i class="fa fa-circle" style="color:#FF0000"></i> 101+ 不健康</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 為每個測站添加標記
        for station in self.data:
            try:
                # 解析坐標
                lat = float(station.get('latitude', 0))
                lon = float(station.get('longitude', 0))
                
                if lat == 0 or lon == 0:
                    continue
                
                # 獲取 AQI 相關資訊
                aqi = station.get('aqi', 'N/A')
                site_name = station.get('sitename', '未知測站')
                county = station.get('county', '未知縣市')
                
                # 獲取顏色和等級
                color = self.get_aqi_color(aqi)
                level = self.get_aqi_level(aqi)
                
                # 建立簡化的彈出視窗內容
                popup_content = f"""
                <b>{site_name}</b><br>
                所在地: {county}<br>
                AQI: {aqi}<br>
                等級: {level}
                """
                
                # 建立標記
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=8,
                    popup=folium.Popup(popup_content, max_width=300),
                    color='black',
                    weight=1,
                    fillColor=color,
                    fillOpacity=0.8
                ).add_to(m)
                
            except (ValueError, KeyError) as e:
                print(f"處理測站資料時發生錯誤: {e}")
                continue
        
        return m
    
    def save_map(self, map_obj, filename='outputs/aqi_map.html'):
        """儲存地圖檔案"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            map_obj.save(filename)
            print(f"地圖已儲存至: {filename}")
            return True
        except Exception as e:
            print(f"儲存地圖時發生錯誤: {e}")
            return False
    
    def run(self):
        """執行主要流程"""
        print("=== 即時 AQI 地圖視覺化程式 ===")
        
        # 獲取數據
        if not self.fetch_aqi_data():
            print("無法獲取 AQI 數據，程式終止")
            return False
        
        # 匯出 CSV 資料
        if not self.export_to_csv():
            print("無法匯出 CSV 資料")
        
        # 建立地圖
        map_obj = self.create_map()
        if not map_obj:
            print("無法建立地圖，程式終止")
            return False
        
        # 儲存地圖
        if self.save_map(map_obj):
            print("=== 程式執行完成 ===")
            return True
        else:
            print("=== 程式執行失敗 ===")
            return False

def main():
    """主程式入口"""
    try:
        mapper = AQIMapper()
        success = mapper.run()
        
        if success:
            print("請開啟 outputs/aqi_map.html 查看結果")
        else:
            print("程式執行失敗，請檢查錯誤訊息")
            
    except Exception as e:
        print(f"程式執行時發生未預期的錯誤: {e}")

if __name__ == "__main__":
    main()
