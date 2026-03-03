#!/usr/bin/env python3
"""
氣象站API座標系統比較分析
取得氣象站資料，比較兩組座標，視覺化差距
"""

import requests
import pandas as pd
import json
import numpy as np
from datetime import datetime
import os

class WeatherStationAnalyzer:
    def __init__(self):
        self.base_url = "https://opendata.cwb.gov.tw/api/v1/rest/datastore"
        self.api_key = "your_api_key_here"  # 需要申請CWB API key
        self.stations_data = []
        self.processed_data = None
        
    def fetch_weather_stations(self):
        """取得氣象站資料"""
        # 這裡使用模擬資料，實際應用需要替換為真實的CWB API
        print("正在取得氣象站資料...")
        
        # 模擬氣象站資料結構
        mock_data = {
            "records": {
                "Station": [
                    {
                        "StationName": "台北",
                        "StationId": "466920",
                        "GeoInfo": {
                            "County": "臺北市",
                            "Town": "中正區"
                        },
                        "GeoInfoCoordinates": [
                            {
                                "CoordinateName": "WGS84",
                                "Latitude": 25.0375,
                                "Longitude": 121.5625
                            },
                            {
                                "CoordinateName": "TWD97", 
                                "Latitude": 2769940.45,
                                "Longitude": 307785.67
                            }
                        ]
                    },
                    {
                        "StationName": "台中",
                        "StationId": "467490",
                        "GeoInfo": {
                            "County": "臺中市",
                            "Town": "西區"
                        },
                        "GeoInfoCoordinates": [
                            {
                                "CoordinateName": "WGS84",
                                "Latitude": 24.1477,
                                "Longitude": 120.6736
                            },
                            {
                                "CoordinateName": "TWD97",
                                "Latitude": 2674053.78,
                                "Longitude": 231409.43
                            }
                        ]
                    },
                    {
                        "StationName": "高雄",
                        "StationId": "467440",
                        "GeoInfo": {
                            "County": "高雄市",
                            "Town": "前金區"
                        },
                        "GeoInfoCoordinates": [
                            {
                                "CoordinateName": "WGS84",
                                "Latitude": 22.6273,
                                "Longitude": 120.3014
                            },
                            {
                                "CoordinateName": "TWD97",
                                "Latitude": 2508463.12,
                                "Longitude": 138179.78
                            }
                        ]
                    }
                ]
            }
        }
        
        self.stations_data = mock_data["records"]["Station"]
        print(f"取得 {len(self.stations_data)} 個氣象站資料")
        
        # 保存原始資料
        self.save_raw_data()
        
    def save_raw_data(self):
        """保存原始API資料"""
        os.makedirs('data', exist_ok=True)
        with open('data/weather_stations.json', 'w', encoding='utf-8') as f:
            json.dump({"records": {"Station": self.stations_data}}, f, 
                     ensure_ascii=False, indent=2)
        print("原始資料已保存到 data/weather_stations.json")
    
    def twd97_to_wgs84(self, x, y):
        """TWD97座標轉換為WGS84（簡化版本）"""
        # 這裡使用簡化的轉換公式，實際應用需要更精確的轉換
        # TWD97轉WGS84的近似轉換
        lat = y / 111320 - 0.016  # 簡化轉換
        lon = x / (111320 * np.cos(np.radians(lat))) + 121.0  # 簡化轉換
        return lat, lon
    
    def process_coordinates(self):
        """處理座標資料"""
        print("正在處理座標資料...")
        
        processed_records = []
        
        for station in self.stations_data:
            station_name = station["StationName"]
            station_id = station["StationId"]
            coordinates = station["GeoInfoCoordinates"]
            
            # 提取兩組座標
            coord1 = coord2 = None
            for coord in coordinates:
                if coord["CoordinateName"] == "WGS84":
                    coord1 = {
                        "system": "WGS84",
                        "lat": coord["Latitude"],
                        "lon": coord["Longitude"]
                    }
                elif coord["CoordinateName"] == "TWD97":
                    # 將TWD97轉換為WGS84（模擬）
                    converted_lat, converted_lon = self.twd97_to_wgs84(
                        coord["Longitude"], coord["Latitude"]
                    )
                    coord2 = {
                        "system": "TWD97_converted",
                        "lat": converted_lat,
                        "lon": converted_lon,
                        "original_lat": coord["Latitude"],
                        "original_lon": coord["Longitude"]
                    }
            
            if coord1 and coord2:
                # 計算距離差距
                distance = self.calculate_distance(
                    coord1["lat"], coord1["lon"],
                    coord2["lat"], coord2["lon"]
                )
                
                record = {
                    "station_name": station_name,
                    "station_id": station_id,
                    "coord1_system": coord1["system"],
                    "coord1_lat": coord1["lat"],
                    "coord1_lon": coord1["lon"],
                    "coord2_system": coord2["system"],
                    "coord2_lat": coord2["lat"],
                    "coord2_lon": coord2["lon"],
                    "distance_m": distance,
                    "lat_diff": abs(coord1["lat"] - coord2["lat"]),
                    "lon_diff": abs(coord1["lon"] - coord2["lon"])
                }
                processed_records.append(record)
        
        self.processed_data = pd.DataFrame(processed_records)
        
        # 保存處理後的資料
        os.makedirs('data', exist_ok=True)
        self.processed_data.to_csv('data/processed_data.csv', 
                                  index=False, encoding='utf-8')
        print(f"處理完成，共 {len(self.processed_data)} 個測站")
        
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """計算兩點間距離（米）"""
        from geopy.distance import geodesic
        return geodesic((lat1, lon1), (lat2, lon2)).meters
    
    def generate_statistics(self):
        """生成統計報告"""
        if self.processed_data is None:
            print("請先處理座標資料")
            return
        
        stats = {
            "total_stations": len(self.processed_data),
            "mean_distance": self.processed_data["distance_m"].mean(),
            "max_distance": self.processed_data["distance_m"].max(),
            "min_distance": self.processed_data["distance_m"].min(),
            "std_distance": self.processed_data["distance_m"].std(),
            "mean_lat_diff": self.processed_data["lat_diff"].mean(),
            "mean_lon_diff": self.processed_data["lon_diff"].mean()
        }
        
        # 保存統計結果
        stats_df = pd.DataFrame([stats])
        stats_df.to_csv('data/coordinate_stats.csv', index=False)
        
        print("\n=== 座標差距統計 ===")
        print(f"測站總數: {stats['total_stations']}")
        print(f"平均距離差距: {stats['mean_distance']:.2f} 公尺")
        print(f"最大距離差距: {stats['max_distance']:.2f} 公尺")
        print(f"最小距離差距: {stats['min_distance']:.2f} 公尺")
        print(f"距離標準差: {stats['std_distance']:.2f} 公尺")
        print(f"平均緯度差距: {stats['mean_lat_diff']:.8f} 度")
        print(f"平均經度差距: {stats['mean_lon_diff']:.8f} 度")
        
        return stats
    
    def run_analysis(self):
        """執行完整分析"""
        print("開始氣象站座標系統分析...")
        print("=" * 50)
        
        # 1. 取得資料
        self.fetch_weather_stations()
        
        # 2. 處理座標
        self.process_coordinates()
        
        # 3. 生成統計
        stats = self.generate_statistics()
        
        # 4. 生成視覺化
        print("\n正在生成視覺化圖表...")
        self.create_visualization()
        
        print("\n分析完成！")
        print("結果檔案:")
        print("- data/weather_stations.json (原始資料)")
        print("- data/processed_data.csv (處理後資料)")
        print("- data/coordinate_stats.csv (統計結果)")
        print("- output/station_map.html (互動式地圖)")
        print("- output/coordinate_comparison.png (比較圖表)")
    
    def create_visualization(self):
        """創建視覺化圖表"""
        try:
            import folium
            import matplotlib.pyplot as plt
            
            os.makedirs('output', exist_ok=True)
            
            # 1. 建立互動式地圖
            self.create_interactive_map()
            
            # 2. 建立統計圖表
            self.create_statistical_plots()
            
        except ImportError as e:
            print(f"視覺化模組未安裝: {e}")
            print("請執行: pip install folium matplotlib seaborn")
    
    def create_interactive_map(self):
        """建立互動式地圖"""
        import folium
        
        # 計算地圖中心點
        center_lat = self.processed_data[["coord1_lat", "coord2_lat"]].mean().mean()
        center_lon = self.processed_data[["coord1_lon", "coord2_lon"]].mean().mean()
        
        # 建立地圖
        m = folium.Map(location=[center_lat, center_lon], zoom_start=7)
        
        # 添加測站座標
        for _, row in self.processed_data.iterrows():
            # 第一組座標（藍色）
            folium.CircleMarker(
                location=[row["coord1_lat"], row["coord1_lon"]],
                radius=6,
                popup=f"{row['station_name']} ({row['coord1_system']})",
                color='blue',
                fill=True,
                fillColor='blue'
            ).add_to(m)
            
            # 第二組座標（紅色）
            folium.CircleMarker(
                location=[row["coord2_lat"], row["coord2_lon"]],
                radius=6,
                popup=f"{row['station_name']} ({row['coord2_system']})",
                color='red',
                fill=True,
                fillColor='red'
            ).add_to(m)
            
            # 連線
            folium.PolyLine(
                locations=[
                    [row["coord1_lat"], row["coord1_lon"]],
                    [row["coord2_lat"], row["coord2_lon"]]
                ],
                color='green',
                weight=2,
                popup=f"距離: {row['distance_m']:.2f}公尺"
            ).add_to(m)
        
        # 添加圖例
        legend_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 150px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>座標系統</h4>
        <p><i class="fa fa-circle" style="color:blue"></i> WGS84</p>
        <p><i class="fa fa-circle" style="color:red"></i> TWD97轉換</p>
        <p><i class="fa fa-minus" style="color:green"></i> 距離連線</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 保存地圖
        m.save('output/station_map.html')
        print("互動式地圖已保存到 output/station_map.html")
    
    def create_statistical_plots(self):
        """建立統計圖表"""
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. 距離差距分佈
        axes[0, 0].hist(self.processed_data["distance_m"], bins=20, alpha=0.7)
        axes[0, 0].set_title('座標距離差距分佈')
        axes[0, 0].set_xlabel('距離 (公尺)')
        axes[0, 0].set_ylabel('測站數量')
        
        # 2. 緯度差距分佈
        axes[0, 1].hist(self.processed_data["lat_diff"] * 111000, bins=20, alpha=0.7, color='orange')
        axes[0, 1].set_title('緯度差距分佈')
        axes[0, 1].set_xlabel('緯度差距 (公尺)')
        axes[0, 1].set_ylabel('測站數量')
        
        # 3. 經度差距分佈
        axes[1, 0].hist(self.processed_data["lon_diff"] * 111000, bins=20, alpha=0.7, color='green')
        axes[1, 0].set_title('經度差距分佈')
        axes[1, 0].set_xlabel('經度差距 (公尺)')
        axes[1, 0].set_ylabel('測站數量')
        
        # 4. 散點圖比較
        axes[1, 1].scatter(self.processed_data["coord1_lon"], self.processed_data["coord1_lat"], 
                          alpha=0.7, label='WGS84', color='blue')
        axes[1, 1].scatter(self.processed_data["coord2_lon"], self.processed_data["coord2_lat"], 
                          alpha=0.7, label='TWD97轉換', color='red')
        axes[1, 1].set_title('座標分佈比較')
        axes[1, 1].set_xlabel('經度')
        axes[1, 1].set_ylabel('緯度')
        axes[1, 1].legend()
        
        plt.tight_layout()
        plt.savefig('output/coordinate_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("統計圖表已保存到 output/coordinate_comparison.png")

if __name__ == "__main__":
    analyzer = WeatherStationAnalyzer()
    analyzer.run_analysis()
