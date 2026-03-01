#!/usr/bin/env python3
"""
環境設定腳本
自動安裝所需的 Python 套件
"""

import subprocess
import sys
import os

def install_requirements():
    """安裝 requirements.txt 中的套件"""
    try:
        print("正在安裝所需的 Python 套件...")
        
        # 檢查 requirements.txt 是否存在
        if not os.path.exists('requirements.txt'):
            print("錯誤: 找不到 requirements.txt 檔案")
            return False
        
        # 執行 pip install
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ 套件安裝成功")
            return True
        else:
            print(f"✗ 套件安裝失敗: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"安裝過程中發生錯誤: {e}")
        return False

def check_python_version():
    """檢查 Python 版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("錯誤: 需要 Python 3.7 或更高版本")
        return False
    
    print(f"✓ Python 版本: {version.major}.{version.minor}.{version.micro}")
    return True

def check_env_file():
    """檢查 .env 檔案"""
    if not os.path.exists('.env'):
        print("警告: .env 檔案不存在")
        print("請建立 .env 檔案並設定 EPA_API_KEY")
        return False
    
    # 檢查是否有 API Key
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'EPA_API_KEY' not in content:
            print("警告: .env 檔案中沒有設定 EPA_API_KEY")
            print("請在 .env 檔案中新增: EPA_API_KEY=your_api_key_here")
            return False
    
    print("✓ .env 檔案檢查通過")
    return True

def main():
    """主程式"""
    print("=== Python AQI 地圖程式環境設定 ===")
    
    # 檢查 Python 版本
    if not check_python_version():
        return False
    
    # 檢查 .env 檔案
    if not check_env_file():
        print("\n請先設定 .env 檔案後再執行此腳本")
        return False
    
    # 安裝套件
    if not install_requirements():
        return False
    
    print("\n=== 環境設定完成 ===")
    print("現在可以執行: python aqi_mapper.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
