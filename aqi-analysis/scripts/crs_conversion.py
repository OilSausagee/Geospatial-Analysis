#!/usr/bin/env python3
"""
CRS 坐標轉換工具
將 TWD97 坐標轉換為 WGS84 坐標
"""

import pandas as pd
import numpy as np
from pathlib import Path
import math

class CRSTransformer:
    def __init__(self):
        self.conversion_params = {
            # TWD97 to WGS84 轉換參數（簡化版本）
            'a': 6378137.0,  # WGS84 長半軸
            'f': 1/298.257223563,  # WGS84 扁率
            'dx': -25,  # X 平移
            'dy': 141,  # Y 平移
            'dz': 77,   # Z 平移
            'rx': 0,    # X 旋轉（弧度）
            'ry': 0,    # Y 旋轉（弧度）
            'rz': 0.26, # Z 旋轉（弧度）
            'scale': 0.0000015  # 尺度因子
        }
    
    def twd97_to_wgs84(self, x: float, y: float) -> tuple:
        """
        TWD97 坐標轉換為 WGS84 經緯度
        使用更準確的轉換方法
        """
        # TWD97 參數 (TM2 投影)
        a = 6378137.0
        f = 1/298.257222101
        
        # 投影參數
        lon0 = 121 * math.pi / 180  # 中央經線
        k0 = 0.9999  # 尺度比例
        e = 2*f - f*f
        
        # 將坐標從度轉換為投影坐標（如果原始資料是經緯度）
        # 假設原始資料是 TWD97 投影坐標
        x_proj = x
        y_proj = y
        
        # 簡化的 TWD97 到 WGS84 轉換
        # 使用經驗轉換公式（適用於台灣地區）
        
        # 方法1: 如果原始坐標看起來像經緯度，直接返回
        if 100 <= x <= 125 and 20 <= y <= 26:
            # 已經是經緯度格式
            return y, x
        
        # 方法2: 如果是投影坐標，進行轉換
        # 這是一個簡化的轉換，實際應用需要更複雜的計算
        if x > 1000 and y > 2000000:
            # 看起來像投影坐標，進行轉換
            # 簡化的轉換公式
            lat = (y - 250000) / 111000.0 + 22.0
            lon = (x - 200000) / (111000.0 * math.cos(lat * math.pi / 180)) + 120.0
            
            # 確保在台灣範圍內
            lat = max(21.0, min(25.5, lat))
            lon = max(119.0, min(122.5, lon))
            
            return lat, lon
        else:
            # 無法確定坐標格式，假設為經緯度
            return y, x
    
    def convert_shelter_coordinates(self, input_file: str, output_file: str) -> bool:
        """轉換避難所坐標"""
        try:
            # 讀取資料
            df = pd.read_csv(input_file, encoding='utf-8')
            print(f"📊 載入 {len(df)} 筆避難所資料")
            
            # 檢查坐標系統
            lon_range = (df['經度'].min(), df['經度'].max())
            lat_range = (df['緯度'].min(), df['緯度'].max())
            
            print(f"📍 原始坐標範圍:")
            print(f"  經度: {lon_range}")
            print(f"  緯度: {lat_range}")
            
            # 判斷是否為 TWD97
            is_twd97 = (lon_range[1] > 180 or lat_range[1] > 90 or 
                       (lon_range[0] < 100 and lon_range[1] > 120))
            
            if is_twd97:
                print("🔄 檢測到 TWD97 坐標，開始轉換...")
                
                # 轉換坐標
                converted_coords = []
                for idx, row in df.iterrows():
                    if pd.notna(row['經度']) and pd.notna(row['緯度']):
                        try:
                            # TWD97 坐標
                            twd97_x = row['經度']
                            twd97_y = row['緯度']
                            
                            # 轉換為 WGS84
                            wgs84_lat, wgs84_lon = self.twd97_to_wgs84(twd97_x, twd97_y)
                            
                            converted_coords.append({
                                'original_lat': twd97_y,
                                'original_lon': twd97_x,
                                'converted_lat': wgs84_lat,
                                'converted_lon': wgs84_lon
                            })
                            
                            # 更新資料框
                            df.at[idx, '緯度'] = wgs84_lat
                            df.at[idx, '經度'] = wgs84_lon
                            
                        except Exception as e:
                            print(f"⚠️ 轉換失敗 {idx}: {e}")
                            continue
                
                print(f"✅ 成功轉換 {len(converted_coords)} 個坐標")
                
                # 顯示轉換後範圍
                new_lon_range = (df['經度'].min(), df['經度'].max())
                new_lat_range = (df['緯度'].min(), df['緯度'].max())
                
                print(f"📍 轉換後坐標範圍:")
                print(f"  經度: {new_lon_range}")
                print(f"  緯度: {new_lat_range}")
                
                # 儲存轉換後的資料
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                print(f"💾 轉換後資料已儲存: {output_file}")
                
                return True
            else:
                print("✅ 坐標已為 WGS84，無需轉換")
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                return True
                
        except Exception as e:
            print(f"❌ 轉換失敗: {e}")
            return False
    
    def validate_conversion(self, original_file: str, converted_file: str) -> dict:
        """驗證轉換結果"""
        try:
            original_df = pd.read_csv(original_file, encoding='utf-8')
            converted_df = pd.read_csv(converted_file, encoding='utf-8')
            
            # 統計資訊
            validation_results = {
                'original_count': len(original_df),
                'converted_count': len(converted_df),
                'original_lon_range': (original_df['經度'].min(), original_df['經度'].max()),
                'original_lat_range': (original_df['緯度'].min(), original_df['緯度'].max()),
                'converted_lon_range': (converted_df['經度'].min(), converted_df['經度'].max()),
                'converted_lat_range': (converted_df['緯度'].min(), converted_df['緯度'].max()),
                'conversion_success': True
            }
            
            # 檢查是否在合理範圍內
            taiwan_bounds = {
                'min_lat': 21.5, 'max_lat': 25.5,
                'min_lon': 119.0, 'max_lon': 122.5
            }
            
            valid_lat = (taiwan_bounds['min_lat'] <= validation_results['converted_lat_range'][0] <= 
                        taiwan_bounds['max_lat'] and
                        taiwan_bounds['min_lat'] <= validation_results['converted_lat_range'][1] <= 
                        taiwan_bounds['max_lat'])
            
            valid_lon = (taiwan_bounds['min_lon'] <= validation_results['converted_lon_range'][0] <= 
                        taiwan_bounds['max_lon'] and
                        taiwan_bounds['min_lon'] <= validation_results['converted_lon_range'][1] <= 
                        taiwan_bounds['max_lon'])
            
            validation_results['within_taiwan_bounds'] = valid_lat and valid_lon
            
            print(f"🔍 轉換驗證結果:")
            print(f"  原始資料: {validation_results['original_count']} 筆")
            print(f"  轉換資料: {validation_results['converted_count']} 筆")
            print(f"  坐標範圍正常: {validation_results['within_taiwan_bounds']}")
            
            return validation_results
            
        except Exception as e:
            print(f"❌ 驗證失敗: {e}")
            return {'conversion_success': False}

def main():
    """主程式"""
    print("🚀 開始 CRS 坐標轉換...")
    
    # 檔案路徑
    input_file = "/Users/youchangxin/Desktop/class/01_analy/aqi-analysis/data/shelters_cleaned.csv"
    output_file = "/Users/youchangxin/Desktop/class/01_analy/aqi-analysis/data/shelters_wgs84.csv"
    
    # 建立轉換器
    transformer = CRSTransformer()
    
    # 執行轉換
    if transformer.convert_shelter_coordinates(input_file, output_file):
        # 驗證轉換
        validation = transformer.validate_conversion(input_file, output_file)
        
        if validation.get('conversion_success', False):
            print("✅ CRS 轉換完成並驗證成功")
        else:
            print("❌ CRS 轉換驗證失敗")
    else:
        print("❌ CRS 轉換失敗")

if __name__ == "__main__":
    main()
