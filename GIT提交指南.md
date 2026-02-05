# Git提交和部署指南

## 准备工作

### 1. 检查修改
```bash
git status
```

### 2. 查看差异
```bash
git diff
```

## 提交到Git

### 1. 添加所有修改
```bash
git add .
```

### 2. 提交
```bash
git commit -m "修复CSV导出None值错误"
```

### 3. 推送到GitHub
```bash
git push origin main
```

## 部署到服务器

### 方法1：一键修复脚本（推荐）

**Windows用户：**
```bash
upload_rating_fix.bat
```

这个脚本会自动：
- ✅ 上传修复后的 rating_app.py
- ✅ 上传数据文件 stores.json
- ✅ 修复Nginx端口配置（8000→8001）
- ✅ 重启服务
- ✅ 验证部署

### 方法2：手动上传文件

**上传应用代码：**
```bash
scp rating_app.py root@blitzepanda.top:/opt/review-result-viewer/
scp viewer/static/rating.js root@blitzepanda.top:/opt/review-result-viewer/viewer/static/
scp viewer/static/rating.css root@blitzepanda.top:/opt/review-result-viewer/viewer/static/
scp viewer/templates/rating.html root@blitzepanda.top:/opt/review-result-viewer/viewer/templates/
```

**上传数据文件：**
```bash
scp rating_data/stores.json root@blitzepanda.top:/opt/review-result-viewer/rating_data/
```

**修复Nginx配置并重启服务：**
```bash
ssh root@blitzepanda.top "sed -i 's|proxy_pass http://127.0.0.1:8000|proxy_pass http://127.0.0.1:8001|g' /etc/nginx/sites-available/default && nginx -t && systemctl reload nginx && systemctl restart rating"
```

### 方法2：从GitHub拉取

```bash
# SSH到服务器
ssh root@blitzepanda.top

# 进入项目目录
cd /opt/review-result-viewer

# 拉取最新代码
git pull

# 重启服务
systemctl restart rating
```

## 验证部署

### 1. 检查服务状态
```bash
ssh root@blitzepanda.top "systemctl status rating"
```

### 2. 测试API
```bash
curl http://blitzepanda.top/api/rating/war-zones
```

### 3. 浏览器访问
http://blitzepanda.top/rating

## 常见问题

### Q: 评级状态不显示
**解决**：已修复 rating_app.py 中的 current_rating 返回格式

### Q: CSS/JS不加载
**解决**：检查Nginx配置中的 `/static/` location

### Q: 数据为空
**解决**：确保 rating_data/stores.json 已上传到服务器

## 文件清单

### 需要上传到GitHub的文件
- ✅ rating_app.py
- ✅ export_stores_to_json.py
- ✅ viewer/templates/rating.html
- ✅ viewer/static/rating.js
- ✅ viewer/static/rating.css
- ✅ rating_data/.gitkeep
- ✅ rating_data/README.md
- ✅ deploy/server_deploy.sh
- ✅ deploy/nginx_config_guide.md
- ✅ README.md
- ✅ .gitignore

### 不上传到GitHub的文件（敏感数据）
- ❌ rating_data/stores.json
- ❌ rating_data/ratings.json
- ❌ store_rank/whitelist.xlsx
- ❌ logs/

## 更新日志

### 2026-02-05
- ✅ 修复CSV导出None值错误（处理数据字段为空的情况）

### 2026-02-04
- ✅ 优化界面UI（现代化设计）
- ✅ 修复评级状态显示问题（rating字段提取）
- ✅ 修复端口配置（8000→8001）
- ✅ 完善服务器部署脚本和文档
- ✅ 添加Nginx配置指南
- ✅ 修复1月堂食营业额数据源（使用T列）
- ✅ 项目清理（删除过期文件）
- ✅ 创建一键修复上传脚本
