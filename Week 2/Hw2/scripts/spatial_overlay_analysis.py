#!/usr/bin/env python3
"""
空間疊圖分析工具
將 AQI 測站和避難收容處所結合在同一張 Folium 地圖上
"""

import pandas as pd
import folium
from folium import plugins
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from typing import Dict, List, Tuple
import math

class SpatialOverlayAnalysis:
    def __init__(self, aqi_file: str, shelter_file: str):
        self.aqi_file = aqi_file
        self.shelter_file = shelter_file
        self.aqi_data = None
        self.shelter_data = None
        self.map = None
        
        # AQI 等級顏色定義
        self.aqi_colors = {
            '良好': '#00E400',      # 綠色
            '普通': '#FFFF00',      # 黃色
            '對敏感族群不健康': '#FF7E00',  # 橙色
            '對所有族群不健康': '#FF0000',  # 紅色
            '非常不健康': '#8F3F97',  # 紫色
            '危害': '#7E0023'       # 褐色
        }
        
        # 避難所圖標定義
        self.shelter_icons = {
            'indoor': '🏢',  # 室內
            'outdoor': '🌳'  # 室外
        }
    
    def load_data(self) -> bool:
        """載入 AQI 和避難所資料"""
        print("📊 載入資料...")
        
        # 載入 AQI 資料
        try:
            self.aqi_data = pd.read_csv(self.aqi_file, encoding='utf-8')
            print(f"✅ 成功載入 {len(self.aqi_data)} 筆 AQI 測站資料")
        except Exception as e:
            print(f"❌ 載入 AQI 資料失敗: {e}")
            return False
        
        # 載入避難所資料
        try:
            self.shelter_data = pd.read_csv(self.shelter_file, encoding='utf-8')
            print(f"✅ 成功載入 {len(self.shelter_data)} 筆避難所資料")
        except Exception as e:
            print(f"❌ 載入避難所資料失敗: {e}")
            return False
        
        return True
    
    def validate_coordinates(self) -> Dict:
        """驗證座標合理性"""
        print("\n🔍 驗證座標合理性...")
        
        # 台灣邊界 (WGS84)
        taiwan_bounds = {
            'min_lat': 21.5, 'max_lat': 25.5,
            'min_lon': 119.0, 'max_lon': 122.5
        }
        
        validation_results = {
            'aqi_stations': {'valid': 0, 'invalid': 0, 'invalid_list': []},
            'shelters': {'valid': 0, 'invalid': 0, 'invalid_list': []}
        }
        
        # 驗證 AQI 測站
        for idx, row in self.aqi_data.iterrows():
            lat, lon = row['緯度'], row['經度']
            if (taiwan_bounds['min_lat'] <= lat <= taiwan_bounds['max_lat'] and
                taiwan_bounds['min_lon'] <= lon <= taiwan_bounds['max_lon']):
                validation_results['aqi_stations']['valid'] += 1
            else:
                validation_results['aqi_stations']['invalid'] += 1
                validation_results['aqi_stations']['invalid_list'].append({
                    'name': row['測站名稱'],
                    'coordinates': (lat, lon)
                })
        
        # 驗證避難所
        for idx, row in self.shelter_data.iterrows():
            if pd.isna(row['經度']) or pd.isna(row['緯度']):
                validation_results['shelters']['invalid'] += 1
                validation_results['shelters']['invalid_list'].append({
                    'name': row['避難收容處所名稱'],
                    'coordinates': 'missing'
                })
                continue
            
            lat, lon = row['緯度'], row['經度']
            if (taiwan_bounds['min_lat'] <= lat <= taiwan_bounds['max_lat'] and
                taiwan_bounds['min_lon'] <= lon <= taiwan_bounds['max_lon']):
                validation_results['shelters']['valid'] += 1
            else:
                validation_results['shelters']['invalid'] += 1
                validation_results['shelters']['invalid_list'].append({
                    'name': row['避難收容處所名稱'],
                    'coordinates': (lat, lon)
                })
        
        print(f"📍 AQI 測站: {validation_results['aqi_stations']['valid']} 有效, {validation_results['aqi_stations']['invalid']} 無效")
        print(f"🏠 避難所: {validation_results['shelters']['valid']} 有效, {validation_results['shelters']['invalid']} 無效")
        
        # 檢查是否有避難所在海中
        ocean_shelters = []
        for item in validation_results['shelters']['invalid_list']:
            if item['coordinates'] != 'missing':
                lat, lon = item['coordinates']
                if lat < 22.0 or lat > 25.3:  # 海洋邊界檢查
                    ocean_shelters.append(item)
        
        if ocean_shelters:
            print("🚨 警告: 發現可能位在海中的避難所!")
            for shelter in ocean_shelters[:5]:  # 只顯示前5個
                print(f"  - {shelter['name']}: {shelter['coordinates']}")
        
        return validation_results
    
    def create_overlay_map(self) -> str:
        """建立空間疊圖"""
        print("\n🗺️ 建立空間疊圖...")
        
        # 計算地圖中心點
        all_lats = []
        all_lons = []
        
        # AQI 測站座標
        for _, row in self.aqi_data.iterrows():
            all_lats.append(row['緯度'])
            all_lons.append(row['經度'])
        
        # 避難所座標 (過濾有效座標)
        valid_shelters = self.shelter_data.dropna(subset=['經度', '緯度'])
        for _, row in valid_shelters.iterrows():
            all_lats.append(row['緯度'])
            all_lons.append(row['經度'])
        
        center_lat = sum(all_lats) / len(all_lats)
        center_lon = sum(all_lons) / len(all_lons)
        
        # 建立地圖
        self.map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=8,
            tiles='OpenStreetMap'
        )
        
        # 添加圖層控制
        feature_groups = {
            'aqi': folium.FeatureGroup(name='AQI 測站'),
            'indoor_shelters': folium.FeatureGroup(name='室內避難所'),
            'outdoor_shelters': folium.FeatureGroup(name='室外避難所')
        }
        
        # 添加 AQI 測站圖層
        print("📍 添加 AQI 測站...")
        for idx, row in self.aqi_data.iterrows():
            lat, lon = row['緯度'], row['經度']
            aqi = row['AQI']
            level = row['等級']
            color = self.aqi_colors.get(level, '#808080')
            
            # 建立 AQI 測標記
            popup_content = f"""
            <div style="font-family: Arial, sans-serif; width: 200px;">
                <h4 style="margin: 0 0 5px 0; color: #333;">{row['測站名稱']}</h4>
                <p style="margin: 2px 0;"><strong>縣市:</strong> {row['縣市']}</p>
                <p style="margin: 2px 0;"><strong>AQI:</strong> <span style="font-size: 16px; font-weight: bold; color: {color};">{aqi}</span></p>
                <p style="margin: 2px 0;"><strong>等級:</strong> {level}</p>
                <p style="margin: 2px 0;"><strong>座標:</strong> ({lat:.6f}, {lon:.6f})</p>
                <p style="margin: 2px 0;"><strong>距離台北:</strong> {row['距離台北車站(km)']} km</p>
            </div>
            """
            
            marker = folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=folium.Popup(popup_content, max_width=250),
                color='black',
                weight=2,
                fillColor=color,
                fillOpacity=0.8
            )
            
            feature_groups['aqi'].add_child(marker)
        
        # 添加避難所圖層
        print("🏠 添加避難所...")
        for idx, row in valid_shelters.iterrows():
            lat, lon = row['緯度'], row['經度']
            name = row['避難收容處所名稱']
            location = row['縣市及鄉鎮市區']
            is_indoor = row.get('is_indoor', True)
            capacity = row.get('預計收容人數', 'N/A')
            
            # 決定圖標類型
            icon_type = 'indoor' if is_indoor else 'outdoor'
            icon_symbol = '🏢' if is_indoor else '🌳'
            icon_color = 'blue' if is_indoor else 'green'
            
            # 建立避難所彈出視窗
            popup_content = f"""
            <div style="font-family: Arial, sans-serif; width: 250px;">
                <h4 style="margin: 0 0 5px 0; color: #333;">{icon_symbol} {name}</h4>
                <p style="margin: 2px 0;"><strong>位置:</strong> {location}</p>
                <p style="margin: 2px 0;"><strong>類型:</strong> <span style="color: {icon_color}; font-weight: bold;">{'室內' if is_indoor else '室外'}</span></p>
                <p style="margin: 2px 0;"><strong>收容人數:</strong> {capacity}</p>
                <p style="margin: 2px 0;"><strong>座標:</strong> ({lat:.6f}, {lon:.6f})</p>
                <p style="margin: 2px 0;"><strong>地址:</strong> {row.get('避難收容處所地址', 'N/A')}</p>
            </div>
            """
            
            # 建立避難所標記
            if is_indoor:
                # 室內避難所 - 圓形
                marker = folium.CircleMarker(
                    location=[lat, lon],
                    radius=6,
                    popup=folium.Popup(popup_content, max_width=300),
                    color='darkblue',
                    weight=2,
                    fillColor='lightblue',
                    fillOpacity=0.8
                )
                feature_groups['indoor_shelters'].add_child(marker)
            else:
                # 室外避難所 - 方形
                marker = folium.RegularPolygonMarker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_content, max_width=300),
                    color='darkgreen',
                    weight=2,
                    fillColor='lightgreen',
                    fillOpacity=0.8,
                    number_of_sides=4,
                    radius=6
                )
                feature_groups['outdoor_shelters'].add_child(marker)
        
        # 添加圖層到地圖
        for fg in feature_groups.values():
            fg.add_to(self.map)
        
        # 添加圖層控制
        folium.LayerControl().add_to(self.map)
        
        # 添加圖例
        self.add_map_legend()
        
        # 添加統計資訊
        self.add_statistics_panel()
        
        print("✅ 空間疊圖建立完成")
        return "Map created successfully"
    
    def add_map_legend(self):
        """添加地圖圖例"""
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 280px; height: 320px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4 style="margin: 0 0 10px 0;">圖例</h4>
        
        <h5 style="margin: 5px 0; color: #333;">AQI 等級</h5>
        <p style="margin: 2px 0;"><span style="color: #00E400;">●</span> 良好 (0-50)</p>
        <p style="margin: 2px 0;"><span style="color: #FFFF00;">●</span> 普通 (51-100)</p>
        <p style="margin: 2px 0;"><span style="color: #FF7E00;">●</span> 對敏感族群不健康 (101-150)</p>
        <p style="margin: 2px 0;"><span style="color: #FF0000;">●</span> 對所有族群不健康 (151-200)</p>
        <p style="margin: 2px 0;"><span style="color: #8F3F97;">●</span> 非常不健康 (201-300)</p>
        <p style="margin: 2px 0;"><span style="color: #7E0023;">●</span> 危害 (301+)</p>
        
        <h5 style="margin: 10px 0 5px 0; color: #333;">避難所類型</h5>
        <p style="margin: 2px 0;"><span style="color: darkblue;">●</span> 室內避難所</p>
        <p style="margin: 2px 0;"><span style="color: darkgreen;">■</span> 室外避難所</p>
        </div>
        '''
        
        self.map.get_root().html.add_child(folium.Element(legend_html))
    
    def add_statistics_panel(self):
        """添加統計資訊面板"""
        # 計算統計資料
        aqi_stats = self.aqi_data['等級'].value_counts()
        shelter_stats = self.shelter_data['is_indoor'].value_counts()
        
        stats_html = f'''
        <div style="position: fixed; 
                    top: 50px; right: 50px; width: 250px; height: 200px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px">
        <h4 style="margin: 0 0 10px 0;">統計資訊</h4>
        
        <h5 style="margin: 5px 0;">AQI 測站 ({len(self.aqi_data)})</h5>
        '''
        
        for level, count in aqi_stats.items():
            color = self.aqi_colors.get(level, '#808080')
            stats_html += f'<p style="margin: 2px 0;"><span style="color: {color};">●</span> {level}: {count}</p>'
        
        stats_html += f'''
        <h5 style="margin: 10px 0 5px 0;">避難所 ({len(self.shelter_data)})</h5>
        <p style="margin: 2px 0;"><span style="color: darkblue;">●</span> 室內: {shelter_stats.get(True, 0)}</p>
        <p style="margin: 2px 0;"><span style="color: darkgreen;">■</span> 室外: {shelter_stats.get(False, 0)}</p>
        </div>
        '''
        
        self.map.get_root().html.add_child(folium.Element(stats_html))
    
    def create_proximity_analysis(self) -> Dict:
        """建立鄰近性分析"""
        print("\n📏 進行鄰近性分析...")
        
        # 過濾有效座標
        valid_shelters = self.shelter_data.dropna(subset=['經度', '緯度'])
        
        proximity_results = []
        
        # 為每個 AQI 測站找最近的避難所
        for _, aqi_row in self.aqi_data.iterrows():
            aqi_lat, aqi_lon = aqi_row['緯度'], aqi_row['經度']
            aqi_name = aqi_row['測站名稱']
            aqi_level = aqi_row['等級']
            
            min_distance = float('inf')
            nearest_shelter = None
            
            # 找最近的避難所
            for _, shelter_row in valid_shelters.iterrows():
                shelter_lat, shelter_lon = shelter_row['緯度'], shelter_row['經度']
                
                # 計算距離 (Haversine)
                distance = self.haversine_distance(aqi_lat, aqi_lon, shelter_lat, shelter_lon)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_shelter = {
                        'name': shelter_row['避難收容處所名稱'],
                        'location': shelter_row['縣市及鄉鎮市區'],
                        'is_indoor': shelter_row.get('is_indoor', True),
                        'capacity': shelter_row.get('預計收容人數', 0)
                    }
            
            proximity_results.append({
                'aqi_station': aqi_name,
                'aqi_level': aqi_level,
                'nearest_shelter': nearest_shelter['name'],
                'shelter_location': nearest_shelter['location'],
                'shelter_type': '室內' if nearest_shelter['is_indoor'] else '室外',
                'shelter_capacity': nearest_shelter['capacity'],
                'distance_m': min_distance
            })
        
        # 轉換為 DataFrame 進行統計分析
        proximity_df = pd.DataFrame(proximity_results)
        
        # 統計分析
        stats = {
            'total_analyses': len(proximity_results),
            'avg_distance': proximity_df['distance_m'].mean(),
            'median_distance': proximity_df['distance_m'].median(),
            'min_distance': proximity_df['distance_m'].min(),
            'max_distance': proximity_df['distance_m'].max(),
            'shelters_within_1km': len(proximity_df[proximity_df['distance_m'] <= 1000]),
            'shelters_within_5km': len(proximity_df[proximity_df['distance_m'] <= 5000])
        }
        
        print(f"📊 鄰近性分析統計:")
        print(f"  - 平均距離: {stats['avg_distance']:.2f} 公尺")
        print(f"  - 中位數距離: {stats['median_distance']:.2f} 公尺")
        print(f"  - 最短距離: {stats['min_distance']:.2f} 公尺")
        print(f"  - 最長距離: {stats['max_distance']:.2f} 公尺")
        print(f"  - 1公里內避難所: {stats['shelters_within_1km']} 個")
        print(f"  - 5公里內避難所: {stats['shelters_within_5km']} 個")
        
        return {'results': proximity_results, 'statistics': stats}
    
    def haversine_distance(self, lat1, lon1, lat2, lon2) -> float:
        """計算兩點間的距離（米）"""
        R = 6371000  # 地球半徑（米）
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def save_map(self, output_file: str = None) -> str:
        """儲存地圖"""
        if output_file is None:
            output_file = Path(self.shelter_file).parent / "spatial_overlay_map.html"
        
        if self.map:
            self.map.save(output_file)
            print(f"🗺️ 空間疊圖已儲存: {output_file}")
            return str(output_file)
        else:
            print("❌ 地圖尚未建立")
            return None
    
    def generate_report(self, validation_results: Dict, proximity_analysis: Dict) -> str:
        """生成分析報告"""
        print("\n📝 生成分析報告...")
        
        # 生成 HTML 報告
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>空間疊圖分析報告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .section {{ margin-bottom: 30px; }}
                .summary {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .warning {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .error {{ background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                .status-good {{ color: #28a745; font-weight: bold; }}
                .status-warning {{ color: #ffc107; font-weight: bold; }}
                .status-error {{ color: #dc3545; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🗺️ 空間疊圖分析報告</h1>
                <p>AQI 測站與避難收容處所空間關係分析</p>
                <p>分析時間: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>📊 資料概覽</h2>
                <div class="summary">
                    <p><strong>AQI 測站數量:</strong> {len(self.aqi_data)}</p>
                    <p><strong>避難所數量:</strong> {len(self.shelter_data)}</p>
                    <p><strong>有效座標避難所:</strong> {validation_results['shelters']['valid']}</p>
                    <p><strong>無效座標避難所:</strong> {validation_results['shelters']['invalid']}</p>
                </div>
            </div>
            
            <div class="section">
                <h2>🔍 座標驗證結果</h2>
                <div class="{'summary' if validation_results['shelters']['invalid'] == 0 else 'warning'}">
                    <h3>AQI 測站</h3>
                    <p><strong>有效座標:</strong> {validation_results['aqi_stations']['valid']}</p>
                    <p><strong>無效座標:</strong> {validation_results['aqi_stations']['invalid']}</p>
                    
                    <h3>避難收容處所</h3>
                    <p><strong>有效座標:</strong> {validation_results['shelters']['valid']}</p>
                    <p><strong>無效座標:</strong> {validation_results['shelters']['invalid']}</p>
                    
                    {f'<div class="error"><p><strong>⚠️ 警告:</strong> 發現 {validation_results["shelters"]["invalid"]} 個座標異常的避難所</p></div>' if validation_results['shelters']['invalid'] > 0 else ''}
                </div>
            </div>
            
            <div class="section">
                <h2>📏 鄰近性分析</h2>
                <div class="summary">
                    <p><strong>分析總數:</strong> {proximity_analysis['statistics']['total_analyses']}</p>
                    <p><strong>平均距離:</strong> {proximity_analysis['statistics']['avg_distance']:.2f} 公尺</p>
                    <p><strong>中位數距離:</strong> {proximity_analysis['statistics']['median_distance']:.2f} 公尺</p>
                    <p><strong>距離範圍:</strong> {proximity_analysis['statistics']['min_distance']:.2f} - {proximity_analysis['statistics']['max_distance']:.2f} 公尺</p>
                    <p><strong>1公里內有避難所:</strong> {proximity_analysis['statistics']['shelters_within_1km']} 個測站</p>
                    <p><strong>5公里內有避難所:</strong> {proximity_analysis['statistics']['shelters_within_5km']} 個測站</p>
                </div>
            </div>
            
            <div class="section">
                <h2>💡 分析結論</h2>
                <div class="summary">
                    <ul>
                        <li>空間疊圖成功整合 AQI 測站與避難所資料</li>
                        <li>地圖提供互動式圖層控制功能</li>
                        <li>鄰近性分析顯示測站與避難所的空間關係</li>
                        <li>座標驗證確保資料品質</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 儲存報告
        output_file = Path(self.shelter_file).parent / "spatial_overlay_analysis_report.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 分析報告已儲存: {output_file}")
        return str(output_file)
    
    def run_analysis(self) -> Dict:
        """執行完整分析"""
        print("🚀 開始空間疊圖分析...")
        
        # 載入資料
        if not self.load_data():
            return {'success': False, 'error': '資料載入失敗'}
        
        # 驗證座標
        validation_results = self.validate_coordinates()
        
        # 建立疊圖
        self.create_overlay_map()
        
        # 鄰近性分析
        proximity_analysis = self.create_proximity_analysis()
        
        # 儲存地圖
        map_file = self.save_map()
        
        # 生成報告
        report_file = self.generate_report(validation_results, proximity_analysis)
        
        results = {
            'success': True,
            'validation': validation_results,
            'proximity_analysis': proximity_analysis,
            'outputs': {
                'map': map_file,
                'report': report_file
            }
        }
        
        print("\n✅ 空間疊圖分析完成!")
        return results

def main():
    """主程式"""
    aqi_file = "/Users/youchangxin/Desktop/class/01_analy/Week 1/outputs/aqi_stations.csv"
    shelter_file = "/Users/youchangxin/Desktop/class/01_analy/Week 2/Hw2/data/避難收容處所_增強版.csv"
    
    analyzer = SpatialOverlayAnalysis(aqi_file, shelter_file)
    results = analyzer.run_analysis()
    
    if results['success']:
        print("\n📋 分析摘要:")
        validation = results['validation']
        proximity = results['proximity_analysis']['statistics']
        
        print(f"📍 AQI 測站: {validation['aqi_stations']['valid']} 有效")
        print(f"🏠 避難所: {validation['shelters']['valid']} 有效, {validation['shelters']['invalid']} 無效")
        print(f"📏 平均距離: {proximity['avg_distance']:.2f} 公尺")
        print(f"\n📁 輸出檔案:")
        for key, file in results['outputs'].items():
            print(f"  - {key}: {file}")
    else:
        print(f"❌ 分析失敗: {results['error']}")

if __name__ == "__main__":
    main()
