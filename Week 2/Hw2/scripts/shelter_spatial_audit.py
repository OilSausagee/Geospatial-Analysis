#!/usr/bin/env python3
"""
避難收容處所空間審計工具
檢查座標品質、離群值偵測、資料增強
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple

class ShelterSpatialAudit:
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.df = None
        self.audit_results = {}
        
        # 台灣邊界定義 (WGS84)
        self.taiwan_bounds = {
            'min_lat': 21.5,    # 最南端
            'max_lat': 25.5,    # 最北端
            'min_lon': 119.0,   # 最西端
            'max_lon': 122.5    # 最東端
        }
        
        # TWD97 座標範圍 (大約)
        self.twd97_bounds = {
            'min_x': 170000,    # 最小 X
            'max_x': 340000,    # 最大 X
            'min_y': 2400000,   # 最小 Y
            'max_y': 2750000   # 最大 Y
        }
    
    def load_data(self) -> bool:
        """載入避難所資料"""
        try:
            self.df = pd.read_csv(self.data_file, encoding='utf-8')
            print(f"✅ 成功載入 {len(self.df)} 筆避難所資料")
            print(f"📊 資料欄位: {list(self.df.columns)}")
            return True
        except Exception as e:
            print(f"❌ 載入資料失敗: {e}")
            return False
    
    def detect_coordinate_system(self) -> Dict:
        """檢測座標系統 (TWD97 vs WGS84)"""
        print("\n🔍 檢測座標系統...")
        
        # 提取經緯度資料
        lons = self.df['經度'].dropna()
        lats = self.df['緯度'].dropna()
        
        # 檢查座標範圍
        lon_range = (lons.min(), lons.max())
        lat_range = (lats.min(), lats.max())
        
        print(f"📍 經度範圍: {lon_range}")
        print(f"📍 緯度範圍: {lat_range}")
        
        # 判斷座標系統
        is_wgs84 = True
        reasons = []
        
        # 檢查經緯度範圍是否符合 WGS84
        if (lon_range[0] >= self.taiwan_bounds['min_lon'] and 
            lon_range[1] <= self.taiwan_bounds['max_lon'] and
            lat_range[0] >= self.taiwan_bounds['min_lat'] and 
            lat_range[1] <= self.taiwan_bounds['max_lat']):
            reasons.append("經緯度範圍符合台灣 WGS84 範圍")
        else:
            is_wgs84 = False
            reasons.append("經緯度範圍超出台灣 WGS84 範圍")
        
        # 檢查是否為 TWD97
        if (lon_range[0] >= self.twd97_bounds['min_x'] and 
            lon_range[1] <= self.twd97_bounds['max_x']):
            is_wgs84 = False
            reasons.append("經度範圍符合 TWD97 X 座標範圍")
        
        # 檢查小數位數
        lon_decimals = lons.apply(lambda x: len(str(x).split('.')[-1]) if '.' in str(x) else 0)
        lat_decimals = lats.apply(lambda x: len(str(x).split('.')[-1]) if '.' in str(x) else 0)
        
        avg_lon_decimals = lon_decimals.mean()
        avg_lat_decimals = lat_decimals.mean()
        
        print(f"🔢 經度平均小數位數: {avg_lon_decimals:.1f}")
        print(f"🔢 緯度平均小數位數: {avg_lat_decimals:.1f}")
        
        if avg_lon_decimals > 3 and avg_lat_decimals > 3:
            reasons.append("座標精度高，符合 WGS84 經緯度特徵")
        else:
            reasons.append("座標精度較低，可能為 TWD97 投影座標")
        
        result = {
            'coordinate_system': 'WGS84' if is_wgs84 else 'TWD97',
            'confidence': 'high' if is_wgs84 else 'medium',
            'reasons': reasons,
            'lon_range': lon_range,
            'lat_range': lat_range,
            'avg_decimals': {
                'longitude': avg_lon_decimals,
                'latitude': avg_lat_decimals
            }
        }
        
        self.audit_results['coordinate_system'] = result
        return result
    
    def detect_outliers(self) -> Dict:
        """偵測離群值"""
        print("\n🚨 偵測離群值...")
        
        # 移除缺失值
        valid_coords = self.df.dropna(subset=['經度', '緯度'])
        
        outliers = {
            'zero_coordinates': [],
            'outside_taiwan': [],
            'extreme_values': [],
            'invalid_coordinates': []
        }
        
        for idx, row in valid_coords.iterrows():
            lon, lat = row['經度'], row['緯度']
            
            # 檢查 (0,0) 座標
            if abs(lon) < 0.001 and abs(lat) < 0.001:
                outliers['zero_coordinates'].append({
                    'index': idx,
                    'name': row['避難收容處所名稱'],
                    'location': row.get('縣市及鄉鎮市區', ''),
                    'coordinates': (lon, lat)
                })
            
            # 檢查是否在台灣邊界外
            if (lat < self.taiwan_bounds['min_lat'] or 
                lat > self.taiwan_bounds['max_lat'] or
                lon < self.taiwan_bounds['min_lon'] or 
                lon > self.taiwan_bounds['max_lon']):
                outliers['outside_taiwan'].append({
                    'index': idx,
                    'name': row['避難收容處所名稱'],
                    'location': row.get('縣市及鄉鎮市區', ''),
                    'coordinates': (lon, lat)
                })
            
            # 檢查極端值
            if abs(lon) > 180 or abs(lat) > 90:
                outliers['extreme_values'].append({
                    'index': idx,
                    'name': row['避難收容處所名稱'],
                    'location': row.get('縣市及鄉鎮市區', ''),
                    'coordinates': (lon, lat)
                })
        
        # 統計
        total_outliers = sum(len(v) for v in outliers.values())
        total_valid = len(valid_coords)
        
        print(f"⚠️ 發現 {total_outliers} 個離群值 (共 {total_valid} 個有效座標)")
        for category, items in outliers.items():
            if items:
                print(f"  - {category}: {len(items)} 個")
        
        result = {
            'total_outliers': total_outliers,
            'total_valid': total_valid,
            'outlier_percentage': (total_outliers / total_valid) * 100,
            'categories': outliers
        }
        
        self.audit_results['outliers'] = result
        return result
    
    def infer_is_indoor(self) -> Dict:
        """根據設施名稱推斷是否為室內避難所"""
        print("\n🏠 推斷室內/室外避難所...")
        
        # 定義關鍵字模式
        indoor_keywords = [
            '學校', '活動中心', '辦公處', '社區中心', '集會所', '教室', '體育館',
            '圖書館', '禮堂', '會議室', '村辦公處', '里辦公處', '區公所',
            '鄉公所', '鎮公所', '市公所', '縣政府', '醫院', '診所',
            '教會', '寺廟', '宮', '堂', '中心', '館', '大樓', '大廳'
        ]
        
        outdoor_keywords = [
            '公園', '廣場', '運動場', '球場', '停車場', '河濱', '海灘',
            '草原', '空地', '廢棄', '臨時', '帳篷', '露營'
        ]
        
        # 建立推斷函數
        def classify_facility(name: str) -> Tuple[bool, str]:
            if pd.isna(name) or not isinstance(name, str):
                return False, "無名稱資料"
            
            name_lower = name.lower()
            
            # 檢查室內關鍵字
            for keyword in indoor_keywords:
                if keyword in name:
                    return True, f"包含關鍵字: {keyword}"
            
            # 檢查室外關鍵字
            for keyword in outdoor_keywords:
                if keyword in name:
                    return False, f"包含關鍵字: {keyword}"
            
            # 預設為室內（避難所通常為室內）
            return True, "預設為室內"
        
        # 應用推斷
        results = []
        for idx, row in self.df.iterrows():
            name = row['避難收容處所名稱']
            is_indoor, reason = classify_facility(name)
            
            results.append({
                'index': idx,
                'name': name,
                'is_indoor': is_indoor,
                'reason': reason
            })
        
        # 統計
        indoor_count = sum(1 for r in results if r['is_indoor'])
        outdoor_count = len(results) - indoor_count
        
        print(f"🏠 室內避難所: {indoor_count} 個 ({(indoor_count/len(results)*100):.1f}%)")
        print(f"🌳 室外避難所: {outdoor_count} 個 ({(outdoor_count/len(results)*100):.1f}%)")
        
        # 新增到資料框
        self.df['is_indoor'] = [r['is_indoor'] for r in results]
        self.df['indoor_reason'] = [r['reason'] for r in results]
        
        result = {
            'total_facilities': len(results),
            'indoor_count': indoor_count,
            'outdoor_count': outdoor_count,
            'indoor_percentage': (indoor_count / len(results)) * 100,
            'classifications': results
        }
        
        self.audit_results['is_indoor'] = result
        return result
    
    def create_visualization(self) -> str:
        """建立視覺化圖表"""
        print("\n📊 建立視覺化圖表...")
        
        # 設定中文字體
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 建立圖表
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('避難收容處所空間審計結果', fontsize=16, fontweight='bold')
        
        # 1. 座標分佈圖
        valid_coords = self.df.dropna(subset=['經度', '緯度'])
        axes[0, 0].scatter(valid_coords['經度'], valid_coords['緯度'], 
                         alpha=0.6, s=20, c='blue')
        axes[0, 0].set_title('避難所座標分佈')
        axes[0, 0].set_xlabel('經度')
        axes[0, 0].set_ylabel('緯度')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 室內/室外分佈
        if 'is_indoor' in self.df.columns:
            indoor_outdoor = self.df['is_indoor'].value_counts()
            axes[0, 1].pie(indoor_outdoor.values, labels=['室內', '室外'], 
                          autopct='%1.1f%%', colors=['lightblue', 'lightgreen'])
            axes[0, 1].set_title('室內/室外避難所分佈')
        
        # 3. 離群值統計
        if 'outliers' in self.audit_results:
            outlier_data = self.audit_results['outliers']
            categories = []
            counts = []
            
            for category, items in outlier_data['categories'].items():
                if items:
                    categories.append(category.replace('_', ' ').title())
                    counts.append(len(items))
            
            if categories:
                axes[1, 0].bar(categories, counts, color='orange', alpha=0.7)
                axes[1, 0].set_title('離群值類型分佈')
                axes[1, 0].set_ylabel('數量')
                axes[1, 0].tick_params(axis='x', rotation=45)
        
        # 4. 縣市分佈
        county_counts = self.df['縣市及鄉鎮市區'].str.split(',').str[0].value_counts().head(10)
        axes[1, 1].bar(range(len(county_counts)), county_counts.values, color='green', alpha=0.7)
        axes[1, 1].set_title('各縣市避難所數量 (前10名)')
        axes[1, 1].set_ylabel('數量')
        axes[1, 1].set_xticks(range(len(county_counts)))
        axes[1, 1].set_xticklabels(county_counts.index, rotation=45)
        
        plt.tight_layout()
        
        # 儲存圖表
        output_file = Path(self.data_file).parent / "shelter_spatial_audit_visualization.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📈 視覺化圖表已儲存: {output_file}")
        return str(output_file)
    
    def generate_report(self) -> str:
        """生成審計報告"""
        print("\n📝 生成審計報告...")
        
        # 收集所有結果
        coord_result = self.audit_results.get('coordinate_system', {})
        outlier_result = self.audit_results.get('outliers', {})
        indoor_result = self.audit_results.get('is_indoor', {})
        
        # 生成 HTML 報告
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>避難收容處所空間審計報告</title>
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
                <h1>🏛️ 避難收容處所空間審計報告</h1>
                <p>資料檔案: {self.data_file}</p>
                <p>審計時間: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>📊 總體摘要</h2>
                <div class="summary">
                    <p><strong>總避難所數量:</strong> {len(self.df)}</p>
                    <p><strong>有效座標數量:</strong> {len(self.df.dropna(subset=['經度', '緯度']))}</p>
                    <p><strong>座標系統:</strong> {coord_result.get('coordinate_system', 'Unknown')}</p>
                    <p><strong>離群值數量:</strong> {outlier_result.get('total_outliers', 0)}</p>
                    <p><strong>室內避難所:</strong> {indoor_result.get('indoor_count', 0)} ({indoor_result.get('indoor_percentage', 0):.1f}%)</p>
                </div>
            </div>
            
            <div class="section">
                <h2>🗺️ 座標系統分析</h2>
                <div class="{'summary' if coord_result.get('coordinate_system') == 'WGS84' else 'warning'}">
                    <p><strong>偵測結果:</strong> {coord_result.get('coordinate_system', 'Unknown')}</p>
                    <p><strong>信心程度:</strong> {coord_result.get('confidence', 'Unknown')}</p>
                    <p><strong>經度範圍:</strong> {coord_result.get('lon_range', ('N/A', 'N/A'))}</p>
                    <p><strong>緯度範圍:</strong> {coord_result.get('lat_range', ('N/A', 'N/A'))}</p>
                    <p><strong>判斷依據:</strong></p>
                    <ul>
        """
        
        for reason in coord_result.get('reasons', []):
            html_content += f"                        <li>{reason}</li>"
        
        html_content += f"""
                    </ul>
                </div>
            </div>
            
            <div class="section">
                <h2>🚨 離群值分析</h2>
                <div class="{'error' if outlier_result.get('total_outliers', 0) > 0 else 'summary'}">
                    <p><strong>離群值總數:</strong> {outlier_result.get('total_outliers', 0)}</p>
                    <p><strong>離群值比例:</strong> {outlier_result.get('outlier_percentage', 0):.2f}%</p>
        """
        
        for category, items in outlier_result.get('categories', {}).items():
            if items:
                html_content += f"""
                    <p><strong>{category.replace('_', ' ').title()}:</strong> {len(items)} 個</p>
                    <table>
                        <tr><th>避難所名稱</th><th>位置</th><th>座標</th></tr>
                """
                for item in items[:5]:  # 只顯示前5個
                    html_content += f"""
                        <tr>
                            <td>{item['name']}</td>
                            <td>{item['location']}</td>
                            <td>({item['coordinates'][0]:.6f}, {item['coordinates'][1]:.6f})</td>
                        </tr>
                    """
                if len(items) > 5:
                    html_content += f"""
                        <tr>
                            <td colspan="3">... 還有 {len(items) - 5} 個</td>
                        </tr>
                    """
                html_content += "</table>"
        
        html_content += """
                </div>
            </div>
            
            <div class="section">
                <h2>🏠 室內/室外分類</h2>
                <div class="summary">
                    <p><strong>室內避難所:</strong> """ + str(indoor_result.get('indoor_count', 0)) + f""" ({indoor_result.get('indoor_percentage', 0):.1f}%)</p>
                    <p><strong>室外避難所:</strong> """ + str(indoor_result.get('outdoor_count', 0)) + f""" ({100-indoor_result.get('indoor_percentage', 0):.1f}%)</p>
                    <p><strong>分類方法:</strong> 基於設施名稱關鍵字自動推斷</p>
                </div>
            </div>
            
            <div class="section">
                <h2>💡 建議</h2>
                <div class="summary">
                    <ul>
                        <li>確認座標系統並進行必要的坐標轉換</li>
                        <li>檢查並修正離群值座標</li>
                        <li>人工驗證室內/室外分類的準確性</li>
                        <li>建立座標品質監控機制</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 儲存報告
        output_file = Path(self.data_file).parent / "shelter_spatial_audit_report.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 審計報告已儲存: {output_file}")
        return str(output_file)
    
    def save_enhanced_data(self) -> str:
        """儲存增強後的資料"""
        print("\n💾 儲存增強後的資料...")
        
        output_file = Path(self.data_file).parent / "避難收容處所_增強版.csv"
        self.df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"💾 增強資料已儲存: {output_file}")
        return str(output_file)
    
    def run_full_audit(self) -> Dict:
        """執行完整空間審計"""
        print("🚀 開始避難收容處所空間審計...")
        
        if not self.load_data():
            return {'success': False, 'error': '資料載入失敗'}
        
        # 執行所有檢查
        self.detect_coordinate_system()
        self.detect_outliers()
        self.infer_is_indoor()
        
        # 生成輸出
        viz_file = self.create_visualization()
        report_file = self.generate_report()
        enhanced_file = self.save_enhanced_data()
        
        results = {
            'success': True,
            'audit_results': self.audit_results,
            'outputs': {
                'visualization': viz_file,
                'report': report_file,
                'enhanced_data': enhanced_file
            }
        }
        
        print("\n✅ 空間審計完成!")
        return results

def main():
    """主程式"""
    data_file = "/Users/youchangxin/Desktop/class/01_analy/Week 2/Hw2/data/避難收容處所點位檔案v9.csv"
    
    auditor = ShelterSpatialAudit(data_file)
    results = auditor.run_full_audit()
    
    if results['success']:
        print("\n📋 審計摘要:")
        coord_sys = results['audit_results']['coordinate_system']['coordinate_system']
        outliers = results['audit_results']['outliers']['total_outliers']
        indoor_pct = results['audit_results']['is_indoor']['indoor_percentage']
        
        print(f"🗺️ 座標系統: {coord_sys}")
        print(f"🚨 離群值: {outliers} 個")
        print(f"🏠 室內避難所: {indoor_pct:.1f}%")
        print(f"\n📁 輸出檔案:")
        for key, file in results['outputs'].items():
            print(f"  - {key}: {file}")
    else:
        print(f"❌ 審計失敗: {results['error']}")

if __name__ == "__main__":
    main()
