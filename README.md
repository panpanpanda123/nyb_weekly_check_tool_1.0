# 牛约堡周清审核系统

集成三大功能的门店管理系统

## 📋 功能模块

### 📝 周清审核
门店检查项审核和展示
- 访问: https://weeklycheck.blitzepanda.top/

### ⭐ 门店评级  
门店等级评定(A/B/C/D)
- 访问: https://weeklycheck.blitzepanda.top/rating

### 🔧 设备异常
收银设备和机顶盒离线监控
- 访问: https://weeklycheck.blitzepanda.top/equipment

## 🚀 快速开始

### 本地运行
```bash
# 安装依赖
pip install -r requirements.txt

# 启动综合查看器
python viewer/app_viewer.py
```

### 数据导入
```bash
# 周清审核数据
python import_data_to_server.py

# 设备异常数据
python import_equipment_data.py

# 评级数据初始化
python init_rating_database.py
```

## 📁 核心文件

### 应用程序
- `viewer/app_viewer.py` - 主应用(端口8000)
- `app.py` - 周清审核(端口5001)
- `rating_app.py` - 门店评级(端口8001)

### 数据导入
- `import_data_to_server.py` - 周清数据
- `import_equipment_data.py` - 设备数据
- `whitelist_loader.py` - 白名单加载

### 配置
- `config.py` - 数据库配置
- `requirements.txt` - 依赖包
- `whitelist.xlsx` - 门店白名单

## 🔧 设备异常功能

### 更新数据

**方法1: 自动脚本(Windows)**
```bash
更新设备数据.bat
```

**方法2: 自动脚本(Linux/Mac)**
```bash
./更新设备数据.sh
```

**方法3: 手动上传(推荐)**
1. 用WinSCP上传Excel到服务器
2. SSH执行: `python3 import_equipment_data.py`

详见: `手动更新设备数据指南.md`

### 数据文件
放在 `equipment_status/` 目录:
- 牛约堡集团_点餐设备表_*.xlsx
- 202*.xlsx (机顶盒)
- 牛约堡集团_门店档案_*.xlsx

## 📱 移动端支持

- ✅ 响应式布局
- ✅ 触摸优化(按钮≥48px)
- ✅ 字体优化(避免iOS缩放)
- ✅ 支持添加到主屏幕

详见: `移动端优化说明.md`

## 🗄️ 数据库

PostgreSQL数据库: `configurable_ops`

主要表:
- `review_results` - 审核结果
- `store_whitelist` - 门店白名单
- `store_ratings` - 门店评级
- `equipment_status` - 设备异常
- `equipment_processing` - 处理记录

## 🚀 服务器部署

### 服务器信息
- IP: 139.224.200.133
- 项目: `/var/www/nyb_weekly_check_tool_1.0`
- 服务: `review-viewer`
- 端口: 8000

### 部署步骤
```bash
# 1. 提交代码
git add .
git commit -m "更新说明"
git push

# 2. 服务器更新
ssh root@139.224.200.133
cd /var/www/nyb_weekly_check_tool_1.0
git pull
systemctl restart review-viewer
```

### 常用命令
```bash
# 查看状态
systemctl status review-viewer

# 重启服务
systemctl restart review-viewer

# 查看日志
journalctl -u review-viewer -n 50 -f
```

## 📚 文档

- `README.md` - 项目总览(本文件)
- `手动更新设备数据指南.md` - 设备数据更新
- `设备异常功能README.md` - 设备功能说明
- `移动端优化说明.md` - 移动端优化
- `门店评级系统说明.md` - 评级系统说明

## 💬 反馈

有使用问题或BUG,企微找窦(dou)反馈

## 📝 更新日志

### v20260304-4 (2026-03-04)
- ✅ 添加反馈提示
- ✅ 移动端优化
- ✅ 设备异常功能
- ✅ 处理选项优化

## 🔒 注意事项

1. 生产环境使用PostgreSQL
2. 设备数据导入会清空处理记录
3. 带'-'的门店ID会被跳过
4. 更新后清除浏览器缓存

## 📦 主要依赖

- Flask - Web框架
- SQLAlchemy - ORM
- pandas - 数据处理
- openpyxl - Excel读写
- psycopg2 - PostgreSQL驱动

## 🏗️ 项目结构

```
.
├── viewer/              # 综合查看器
│   ├── app_viewer.py   # 主应用
│   ├── templates/      # HTML模板
│   └── static/         # 静态资源
├── shared/             # 共享模块
├── equipment_status/   # 设备数据
├── rating_data/        # 评级数据
├── deploy/            # 部署脚本
└── tests/             # 测试文件
```

## 📄 License

内部项目,仅供牛约堡集团使用
