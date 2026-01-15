#!/usr/bin/env python3
"""
简单的文件上传工具 - 通过 HTTP 上传到服务器
"""
import requests
import os
import sys

# 服务器配置
SERVER_URL = "http://139.224.200.133"

def upload_whitelist(file_path):
    """上传白名单文件"""
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    print(f"📤 正在上传白名单文件: {file_path}")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(f"{SERVER_URL}/api/upload/whitelist", files=files, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ {result.get('message')}")
                return True
            else:
                print(f"❌ 上传失败: {result.get('error')}")
                return False
        else:
            print(f"❌ 上传失败，HTTP状态码: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ 上传失败: {str(e)}")
        return False

def upload_reviews(file_path):
    """上传审核结果文件"""
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    print(f"📤 正在上传审核结果文件: {file_path}")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'text/csv')}
            response = requests.post(f"{SERVER_URL}/api/upload/reviews", files=files, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ {result.get('message')}")
                return True
            else:
                print(f"❌ 上传失败: {result.get('error')}")
                return False
        else:
            print(f"❌ 上传失败，HTTP状态码: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ 上传失败: {str(e)}")
        return False

def main():
    print("=" * 50)
    print("📁 文件上传工具")
    print("=" * 50)
    print()
    
    print("请选择要上传的文件类型：")
    print("1. 白名单文件 (Excel .xlsx)")
    print("2. 审核结果文件 (CSV .csv)")
    print()
    
    choice = input("请输入选项 (1/2): ").strip()
    
    if choice == "1":
        file_path = input("\n请输入白名单文件路径: ").strip().strip('"')
        if upload_whitelist(file_path):
            print(f"\n🎉 上传成功！现在可以访问 {SERVER_URL} 查看数据")
    
    elif choice == "2":
        file_path = input("\n请输入审核结果文件路径: ").strip().strip('"')
        if upload_reviews(file_path):
            print(f"\n🎉 上传成功！现在可以访问 {SERVER_URL} 查看数据")
    
    else:
        print("❌ 无效选项！")
    
    print()
    input("按回车键退出...")

if __name__ == "__main__":
    main()
