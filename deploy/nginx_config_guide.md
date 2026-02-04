# Nginx配置指南

## 当前环境

- 项目目录: `/opt/review-result-viewer`
- 评级系统端口: `8000`
- 已有其他Nginx服务运行中

## 配置步骤

### 1. 找到Nginx配置文件

```bash
# 查看Nginx主配置文件位置
nginx -t

# 常见位置：
# /etc/nginx/nginx.conf
# /etc/nginx/sites-available/default
# /etc/nginx/conf.d/default.conf
```

### 2. 备份现有配置

```bash
# 备份配置文件
cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.$(date +%Y%m%d)
```

### 3. 编辑Nginx配置

找到你的server块（通常是监听80或443端口的），在里面添加以下location块：

```bash
# 编辑配置文件
nano /etc/nginx/sites-available/default
# 或
vim /etc/nginx/sites-available/default
```

### 4. 添加评级系统配置

在现有的 `server { ... }` 块内添加：

```nginx
server {
    listen 80;
    server_name blitzepanda.top;
    
    # ... 你现有的其他配置 ...
    
    # ==================== 门店评级系统 ====================
    
    # 评级页面
    location /rating {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 评级API
    location /api/rating {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态文件（可选，提高性能）
    location /static {
        alias /opt/review-result-viewer/viewer/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # ... 你现有的其他配置 ...
}
```

### 5. 测试配置

```bash
# 测试Nginx配置是否正确
nginx -t
```

如果显示 `syntax is ok` 和 `test is successful`，说明配置正确。

### 6. 重载Nginx

```bash
# 重载Nginx配置（不中断服务）
systemctl reload nginx

# 或者重启Nginx
systemctl restart nginx
```

### 7. 验证

```bash
# 检查Nginx状态
systemctl status nginx

# 检查评级服务状态
systemctl status rating

# 测试访问
curl http://localhost:8000/rating
```

## 完整配置示例

如果你的Nginx配置文件是空的或需要完整示例：

```nginx
server {
    listen 80;
    server_name blitzepanda.top;
    
    # 日志
    access_log /var/log/nginx/blitzepanda_access.log;
    error_log /var/log/nginx/blitzepanda_error.log;
    
    # 根目录（你现有的应用）
    location / {
        # 你现有的配置
        proxy_pass http://127.0.0.1:5001;  # 假设周清审核在5001端口
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
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
    
    # 静态文件
    location /static {
        alias /opt/review-result-viewer/viewer/static;
        expires 30d;
    }
}
```

## 常见问题

### Q1: 502 Bad Gateway
**原因**: 评级服务未启动或端口不对

**解决**:
```bash
# 检查服务状态
systemctl status rating

# 启动服务
systemctl start rating

# 检查端口
netstat -tlnp | grep 8000
```

### Q2: 404 Not Found
**原因**: Nginx配置路径不对

**解决**:
```bash
# 检查Nginx配置
nginx -t

# 查看Nginx错误日志
tail -f /var/log/nginx/error.log
```

### Q3: 配置不生效
**原因**: 没有重载Nginx

**解决**:
```bash
# 重载配置
systemctl reload nginx
```

### Q4: 与现有服务冲突
**原因**: location路径冲突

**解决**: 确保 `/rating` 和 `/api/rating` 路径不与现有配置冲突

## 快速命令参考

```bash
# 查看Nginx配置文件位置
nginx -V 2>&1 | grep -o '\-\-conf-path=\S*'

# 测试配置
nginx -t

# 重载配置
systemctl reload nginx

# 查看Nginx日志
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# 查看评级服务日志
tail -f /opt/review-result-viewer/logs/rating_service.log

# 检查端口占用
netstat -tlnp | grep 8000
```

## 安全建议

1. **限制访问频率**（可选）
```nginx
location /api/rating {
    limit_req zone=api burst=10 nodelay;
    proxy_pass http://127.0.0.1:8000;
    # ... 其他配置
}
```

2. **启用HTTPS**（推荐）
```nginx
server {
    listen 443 ssl;
    server_name blitzepanda.top;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # ... 其他配置
}
```

3. **添加访问控制**（可选）
```nginx
location /rating {
    # 只允许特定IP访问
    allow 192.168.1.0/24;
    deny all;
    
    proxy_pass http://127.0.0.1:8000;
    # ... 其他配置
}
```
