# GitHub 上传清单

## 需要上传的文件

### 根目录核心文件
- [x] rating_app.py
- [x] export_stores_to_json.py
- [x] app_cloud.py
- [x] app.py
- [x] database.py
- [x] data_loader.py
- [x] csv_exporter.py
- [x] review_manager_db.py
- [x] whitelist_loader.py
- [x] init_rating_database.py
- [x] reload_whitelist.py
- [x] config.py
- [x] gunicorn_config.py

### 配置文件
- [x] .gitignore
- [x] .gitattributes
- [x] .env.example
- [x] requirements.txt

### 文档
- [x] README.md
- [x] 使用指南.md
- [x] 快速参考.md
- [x] 门店评级系统说明.md
- [x] GIT提交指南.md
- [x] 提交和部署流程.md
- [x] 服务器快速部署.md
- [x] 部署总结.md
- [x] 修复说明.md
- [x] GITHUB上传清单.md
- [x] viewer/未匹配门店处理说明.md

### 部署文件
- [x] deploy/deploy_rating.sh
- [x] deploy/server_deploy.sh
- [x] deploy/rating_deploy_guide.md
- [x] deploy/nginx_config_guide.md
- [x] upload_rating_to_server.bat
- [x] upload_rating_fix.bat
- [x] deploy_from_github.bat

### shared目录
- [x] shared/database_models.py
- [x] shared/__init__.py

### viewer目录
- [x] viewer/app_viewer.py
- [x] viewer/data_importer.py
- [x] viewer/__init__.py
- [x] viewer/templates/rating.html
- [x] viewer/templates/viewer.html
- [x] viewer/templates/admin.html
- [x] viewer/static/rating.js
- [x] viewer/static/rating.css
- [x] viewer/static/viewer.js
- [x] viewer/static/viewer.css

### static目录（周清审核）
- [x] static/app.js
- [x] static/style.css

### templates目录（周清审核）
- [x] templates/index.html

### tests目录（可选）
- [x] tests/test_app.py
- [x] tests/test_csv_exporter.py
- [x] tests/test_data_loader.py
- [x] tests/test_review_manager.py
- [x] tests/test_whitelist_loader.py
- [x] tests/test_unmatched_stores.py
- [x] tests/__init__.py

## 不上传的文件（已在.gitignore中）

### 数据文件
- rating_data/
- store_rank/
- *.xlsx
- *.csv

### 日志
- logs/
- *.log

### Python缓存
- __pycache__/
- *.pyc
- .pytest_cache/
- .hypothesis/

### 环境
- .env
- venv/

### IDE
- .vscode/
- .idea/

### 系统文件
- .DS_Store
- Thumbs.db
- *.lnk

## Git 操作步骤

### 1. 初始化（如果还没有）
```bash
git init
git add .
git commit -m "Initial commit: 门店管理系统"
```

### 2. 添加远程仓库
```bash
git remote add origin https://github.com/your-username/your-repo.git
```

### 3. 推送到GitHub
```bash
git branch -M main
git push -u origin main
```

### 4. 后续更新
```bash
git add .
git commit -m "更新说明"
git push
```

## 云服务器同步步骤

### 方法1：使用上传脚本
```bash
upload_rating_to_server.bat
```

### 方法2：从GitHub拉取
```bash
# SSH到服务器
ssh root@blitzepanda.top

# 克隆或拉取代码
cd /root
git clone https://github.com/your-username/your-repo.git rating
# 或者
cd /root/rating
git pull

# 安装依赖
pip install -r requirements.txt

# 上传数据文件（从本地）
# 在本地执行：
scp rating_data/stores.json root@blitzepanda.top:/root/rating/rating_data/

# 部署
bash deploy/deploy_rating.sh
systemctl restart rating
```

## 注意事项

1. **敏感数据**：确保 `rating_data/` 和 `store_rank/` 不会被上传
2. **环境变量**：使用 `.env` 文件管理敏感配置
3. **数据备份**：定期备份 `rating_data/ratings.json`
4. **版本控制**：使用有意义的commit信息
5. **分支管理**：建议使用 `main` 分支作为生产版本

## 推荐的 .gitignore 检查

上传前确认以下文件被忽略：
```bash
git status --ignored
```

应该看到：
- rating_data/ (ignored)
- store_rank/ (ignored)
- logs/ (ignored)
- __pycache__/ (ignored)
- .env (ignored)
