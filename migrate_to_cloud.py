#!/usr/bin/env python3
"""
自动迁移脚本 - 将项目适配到云服务器
Automatic Migration Script - Adapt Project for Cloud Server
"""
import os
import shutil
from datetime import datetime

def backup_file(filepath):
    """备份文件"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filepath, backup_path)
        print(f"✓ 已备份: {filepath} -> {backup_path}")
        return True
    return False

def modify_app_py():
    """修改app.py文件"""
    app_file = 'app.py'
    
    if not os.path.exists(app_file):
        print(f"✗ 未找到 {app_file}")
        return False
    
    # 备份原文件
    backup_file(app_file)
    
    # 读取文件内容
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经修改过
    if 'from config import' in content:
        print("⚠ app.py 似乎已经修改过，跳过修改")
        return True
    
    # 修改1: 添加导入
    import_line = """from flask import Flask, render_template, jsonify, request, send_file, Response
import os
from io import BytesIO
from werkzeug.utils import secure_filename
from data_loader import DataLoader
from review_manager_db import ReviewManager
from csv_exporter import CSVExporter
from database import init_db, load_whitelist_to_db, get_all_operators_from_db, get_operator_by_store_id"""
    
    new_import = """from flask import Flask, render_template, jsonify, request, send_file, Response
import os
from io import BytesIO
from werkzeug.utils import secure_filename
from data_loader import DataLoader
from review_manager_db import ReviewManager
from csv_exporter import CSVExporter
from database import init_db, load_whitelist_to_db, get_all_operators_from_db, get_operator_by_store_id

# 导入配置
try:
    from config import HOST, PORT, DEBUG, WHITELIST_FILE, ADMIN_USERS
except ImportError:
    # 如果没有config.py，使用默认配置
    HOST = '0.0.0.0'
    PORT = 5001
    DEBUG = False
    WHITELIST_FILE = 'data/whitelist.xlsx'
    ADMIN_USERS = ['窦']"""
    
    content = content.replace(import_line, new_import)
    
    # 修改2: 替换硬编码路径
    old_path = "'D:/pythonproject/Newyobo_operat_database/daily_data/whitelist/whitelist.xlsx'"
    new_path = "WHITELIST_FILE"
    content = content.replace(f"whitelist_file = {old_path}", f"whitelist_file = {new_path}")
    
    # 修改3: 修改管理员权限检查
    content = content.replace("if operator != '窦':", "if operator not in ADMIN_USERS:")
    
    # 修改4: 修改启动配置
    old_run = "app.run(host='0.0.0.0', port=5001, debug=True)"
    new_run = "app.run(host=HOST, port=PORT, debug=DEBUG)"
    content = content.replace(old_run, new_run)
    
    # 写入修改后的内容
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ 已修改: {app_file}")
    return True

def create_env_file():
    """创建.env文件"""
    if os.path.exists('.env'):
        print("⚠ .env 文件已存在，跳过创建")
        return True
    
    if not os.path.exists('.env.example'):
        print("✗ 未找到 .env.example 模板文件")
        return False
    
    shutil.copy2('.env.example', '.env')
    print("✓ 已创建: .env (请修改其中的配置)")
    return True

def create_directories():
    """创建必要的目录"""
    directories = ['logs', 'data', 'uploads']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ 已创建目录: {directory}")
        else:
            print(f"⚠ 目录已存在: {directory}")
    return True

def check_files():
    """检查必要的文件"""
    required_files = [
        'config.py',
        '.env.example',
        'gunicorn_config.py',
        'requirements.txt',
        'database.py',
        'data_loader.py',
        'review_manager_db.py',
        'csv_exporter.py',
        'whitelist_loader.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("✗ 缺少以下文件:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    print("✓ 所有必要文件都存在")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("云服务器迁移脚本")
    print("=" * 60)
    print()
    
    # 检查文件
    print("1. 检查必要文件...")
    if not check_files():
        print("\n✗ 请确保所有必要文件都存在")
        return
    print()
    
    # 创建目录
    print("2. 创建必要目录...")
    create_directories()
    print()
    
    # 创建.env文件
    print("3. 创建环境变量文件...")
    create_env_file()
    print()
    
    # 修改app.py
    print("4. 修改app.py...")
    choice = input("是否修改现有的app.py? (y/n): ").lower()
    if choice == 'y':
        if modify_app_py():
            print("✓ app.py 修改完成")
        else:
            print("✗ app.py 修改失败")
    else:
        print("⚠ 跳过修改app.py")
        print("  建议使用 app_cloud.py 作为云服务器版本")
    print()
    
    # 完成
    print("=" * 60)
    print("迁移准备完成！")
    print("=" * 60)
    print()
    print("下一步:")
    print("1. 编辑 .env 文件，配置数据库连接和文件路径")
    print("2. 将白名单文件放到 data/ 目录")
    print("3. 阅读 云服务器部署指南.md 了解完整部署步骤")
    print("4. 在云服务器上运行: ./start_server.sh")
    print()

if __name__ == '__main__':
    main()
