# 门店评级系统云服务器部署指南

## 系统架构

门店评级系统是一个独立的Flask应用，使用JSON文件存储数据，无需数据库。

## 部署步骤

### 1. 准备文件

需要上传到服务器的文件：
```
rating_app.py                    # 主应用文件
rating_data/stores.json          # 门店数据文件
rating_data/ratings.json         # 评级数据文件（自动创建）
viewer/templates/rating.html     # 页面模板
viewer/static/rating.js          # 前端JS
viewer/static/rating.css         # 前端CSS
```

### 2. 服务器配置

#### 2.1 安装依赖
```bash
pip install flask
```

#### 2.2 创建systemd服务
创建文件 `/etc/systemd/system/rating.service`:

```ini
[Unit]
Description=Store Rating System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/rating
ExecStart=/usr/bin/python3 rating_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2.3 启动服务
```bash
systemctl daemon-reload
systemctl enable rating
systemctl start rating
systemctl status rating
```

### 3. Nginx配置

在Nginx配置中添加：

```nginx
# 门店评级系统
location /rating {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /api/rating {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /static {
    alias /root/rating/viewer/static;
    expires 30d;
}
```

重启Nginx：
```bash
nginx -t
systemctl reload nginx
```

### 4. 访问地址

- 本地测试: http://localhost:8000/rating
- 云服务器: http://blitzepanda.top/rating

## 数据管理

### 更新门店数据

1. 在本地运行导出脚本：
```bash
python export_stores_to_json.py
```

2. 上传新的 `rating_data/stores.json` 到服务器

3. 重启服务：
```bash
systemctl restart rating
```

### 备份评级数据

评级数据保存在 `rating_data/ratings.json`，定期备份此文件：
```bash
cp rating_data/ratings.json rating_data/ratings_backup_$(date +%Y%m%d).json
```

### 查看评级数据

```bash
cat rating_data/ratings.json | python -m json.tool
```

## 日志查看

应用日志：
```bash
tail -f logs/rating_app.log
```

系统服务日志：
```bash
journalctl -u rating -f
```

## 故障排查

### 服务无法启动
```bash
# 查看服务状态
systemctl status rating

# 查看详细日志
journalctl -u rating -n 50
```

### API返回404
检查Nginx配置是否正确，确保proxy_pass指向正确的端口。

### 数据未更新
1. 检查 `rating_data/stores.json` 文件是否存在
2. 检查文件权限
3. 重启服务

## 性能优化

### 使用Gunicorn（推荐生产环境）

1. 安装Gunicorn：
```bash
pip install gunicorn
```

2. 修改systemd服务：
```ini
ExecStart=/usr/bin/gunicorn -w 4 -b 127.0.0.1:8000 rating_app:app
```

3. 重启服务：
```bash
systemctl daemon-reload
systemctl restart rating
```

## 安全建议

1. 定期备份 `rating_data/ratings.json`
2. 设置适当的文件权限
3. 使用HTTPS（通过Nginx配置SSL）
4. 限制API访问频率（可选）

## 更新流程

1. 备份当前数据
2. 上传新文件
3. 重启服务
4. 验证功能正常
