# 门店管理系统

一个集成了周清审核和门店评级功能的Web应用系统。

## 系统组成

### 1. 周清审核系统
用于门店检查项图片审核，支持多运营人员协作。

**功能特点：**
- 📸 图片审核（合格/不合格）
- 📝 问题描述记录
- 👥 多运营人员筛选
- 📊 审核进度统计
- 📥 CSV导出

**访问地址：**
- 本地：http://localhost:5001
- 云服务器：http://blitzepanda.top

### 2. 门店评级系统
用于区域经理对门店进行A/B/C评级。

**功能特点：**
- ⭐ A/B/C三级评级
- 🔍 战区/区域经理筛选
- 📱 移动端响应式设计
- 💾 自动保存评级
- 📊 完成率统计
- 📥 CSV导出

**访问地址：**
- 本地：http://localhost:8000/rating
- 云服务器：http://blitzepanda.top/rating

## 技术栈

- **后端**: Flask (Python)
- **前端**: 原生JavaScript + CSS
- **数据库**: PostgreSQL（周清审核）/ JSON文件（门店评级）
- **部署**: Gunicorn + Nginx + Systemd

## 快速开始

### 环境要求
- Python 3.8+
- PostgreSQL 12+（周清审核系统需要）

### 安装依赖
```bash
pip install -r requirements.txt
```

### 周清审核系统

#### 本地运行
```bash
python app.py
```
访问：http://localhost:5001

#### 云服务器运行
```bash
python app_cloud.py
```

### 门店评级系统

#### 1. 导出门店数据
```bash
python export_stores_to_json.py
```

#### 2. 启动应用
```bash
python rating_app.py
```
访问：http://localhost:8000/rating

## 部署到云服务器

### 门店评级系统部署

1. **上传文件**
```bash
upload_rating_to_server.bat
```

2. **SSH连接服务器**
```bash
ssh root@blitzepanda.top
cd /root/rating
```

3. **运行部署脚本**
```bash
bash deploy/deploy_rating.sh
```

4. **启动服务**
```bash
systemctl start rating
systemctl status rating
```

5. **配置Nginx**（参考 `deploy/rating_deploy_guide.md`）

### 周清审核系统部署

参考现有的云服务器配置，使用 `app_cloud.py`。

## 项目结构

```
.
├── rating_app.py              # 门店评级应用
├── app_cloud.py               # 周清审核云版本
├── app.py                     # 周清审核本地版本
├── export_stores_to_json.py   # 数据导出工具
├── database.py                # 数据库连接
├── data_loader.py             # 数据加载器
├── csv_exporter.py            # CSV导出
├── review_manager_db.py       # 审核管理器
├── whitelist_loader.py        # 白名单加载器
├── init_rating_database.py    # 评级数据库初始化
├── reload_whitelist.py        # 重新加载白名单
├── config.py                  # 配置文件
├── gunicorn_config.py         # Gunicorn配置
├── requirements.txt           # Python依赖
├── README.md                  # 项目说明
├── 门店评级系统说明.md        # 评级系统详细说明
├── deploy/                    # 部署脚本和文档
│   ├── deploy_rating.sh
│   └── rating_deploy_guide.md
├── shared/                    # 共享模块
│   ├── database_models.py     # 数据模型
│   └── __init__.py
├── viewer/                    # 展示系统
│   ├── app_viewer.py          # 展示应用
│   ├── data_importer.py       # 数据导入器
│   ├── templates/             # HTML模板
│   │   ├── rating.html
│   │   ├── viewer.html
│   │   └── admin.html
│   └── static/                # 静态文件
│       ├── rating.js
│       ├── rating.css
│       ├── viewer.js
│       └── viewer.css
├── static/                    # 周清静态文件
│   ├── app.js
│   └── style.css
├── templates/                 # 周清模板
│   └── index.html
└── tests/                     # 测试文件
    ├── test_app.py
    ├── test_csv_exporter.py
    ├── test_data_loader.py
    ├── test_review_manager.py
    └── test_whitelist_loader.py
```

## 数据文件

### 门店数据
- `rating_data/stores.json` - 门店基础数据
- `rating_data/ratings.json` - 评级数据

### 白名单
- `store_rank/whitelist.xlsx` - 门店白名单Excel

**注意：** 这些文件包含敏感信息，不会上传到GitHub。

## 配置说明

### 数据库配置
编辑 `config.py` 或设置环境变量：
```python
DATABASE_URL = "postgresql://user:password@host:port/database"
```

### 环境变量
复制 `.env.example` 为 `.env` 并配置：
```
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
```

## 开发

### 运行测试
```bash
pytest tests/
```

### 代码格式化
```bash
black .
flake8 .
```

## 常见问题

### Q: 门店数据如何更新？
A: 运行 `python export_stores_to_json.py` 重新导出数据，然后上传到服务器。

### Q: 如何备份评级数据？
A: 定期备份 `rating_data/ratings.json` 文件。

### Q: 页面显示404错误？
A: 检查Nginx配置，确保proxy_pass指向正确的端口。

## 许可证

内部使用项目

## 联系方式

如有问题，请联系技术支持。
