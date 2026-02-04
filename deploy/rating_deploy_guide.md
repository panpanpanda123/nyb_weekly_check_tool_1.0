# 门店评级系统部署指南

## 当前问题诊断

### 问题现象
- 页面能打开但没有UI样式
- 筛选下拉菜单为空
- 完成率统计为空

### 问题原因
1. **端口不匹配**: 服务运行在8001端口，但Nginx可能配置的是8000
2. **数据文件可能缺失**: stores.json 可能未正确上传

## 立即修复步骤

### 步骤1: 上传修复后的代码

```bash
# 上传修复后的 rating_app.py（已修正端口为8001）
scp rating_app.py root@blitzepanda.top:/opt/review-result-viewer/
```

### 步骤2: 确认数据文件存在

```bash
# SSH到服务器
ssh root@blitzepanda.top

# 检查数据文件
ls -lh /opt/review-result-viewer/rating_data/stores.json

# 如果文件不存在或大小为0，从本地上传
exit

# 上传数据文件
scp rating_data/stores.json root@blitzepanda.top:/opt/review-result-viewer/rating_data/
```

### 步骤3: 检查并修复Nginx配置

```bash
# SSH到服务器
ssh root@blitzepanda.top

# 查看当前Nginx配置
cat /etc/nginx/sites-available/default | grep -A 10 "location /rating"

# 如果端口是8000，需要改为8001
nano /etc/nginx/sites-available/default
```

**确保配置如下**（注意端口是8001）：

```nginx
# 门店评级系统
location /rating {
    proxy_pass http://127.0.0.1:8001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /api/rating {
    proxy_pass http://127.0.0.1:8001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# 静态文件
location /static/ {
    alias /opt/review-result-viewer/viewer/static/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

**保存后测试并重载**：

```bash
# 测试配置
nginx -t

# 重载Nginx
systemctl reload nginx
```

### 步骤4: 重启评级服务

```bash
# 重启服务
systemctl restart rating

# 等待3秒
sleep 3

# 检查服务状态
systemctl status rating

# 查看服务日志
tail -20 /opt/review-result-viewer/logs/rating_app.log
```

### 步骤5: 验证修复

```bash
# 测试API（应该返回战区列表）
curl http://127.0.0.1:8001/api/rating/war-zones

# 测试外网访问
curl http://blitzepanda.top/api/rating/war-zones

# 测试静态文件
curl -I http://blitzepanda.top/static/rating.js
```

## 一键修复脚本

创建并运行此脚本：

```bash
# 在服务器上创建修复脚本
cat > /tmp/fix_rating.sh << 'EOF'
#!/bin/bash

echo "🔧 开始修复门店评级系统..."

# 1. 检查数据文件
echo "📊 检查数据文件..."
if [ ! -f /opt/review-result-viewer/rating_data/stores.json ]; then
    echo "❌ stores.json 不存在！请先上传数据文件"
    exit 1
fi

FILE_SIZE=$(stat -f%z /opt/review-result-viewer/rating_data/stores.json 2>/dev/null || stat -c%s /opt/review-result-viewer/rating_data/stores.json)
if [ "$FILE_SIZE" -lt 1000 ]; then
    echo "❌ stores.json 文件太小（${FILE_SIZE} bytes），可能是空文件"
    exit 1
fi
echo "✅ 数据文件正常（${FILE_SIZE} bytes）"

# 2. 检查Nginx配置中的端口
echo "🔍 检查Nginx配置..."
if grep -q "proxy_pass http://127.0.0.1:8000" /etc/nginx/sites-available/default; then
    echo "⚠️  发现端口配置错误，正在修复..."
    sed -i 's|proxy_pass http://127.0.0.1:8000|proxy_pass http://127.0.0.1:8001|g' /etc/nginx/sites-available/default
    
    # 测试配置
    if nginx -t; then
        echo "✅ Nginx配置已修复"
        systemctl reload nginx
        echo "✅ Nginx已重载"
    else
        echo "❌ Nginx配置测试失败"
        exit 1
    fi
else
    echo "✅ Nginx端口配置正确"
fi

# 3. 重启评级服务
echo "🔄 重启评级服务..."
systemctl restart rating
sleep 3

# 4. 检查服务状态
if systemctl is-active --quiet rating; then
    echo "✅ 评级服务运行正常"
else
    echo "❌ 评级服务启动失败"
    systemctl status rating
    exit 1
fi

# 5. 测试API
echo "🧪 测试API..."
RESPONSE=$(curl -s http://127.0.0.1:8001/api/rating/war-zones)
if echo "$RESPONSE" | grep -q "success"; then
    echo "✅ API测试通过"
else
    echo "❌ API测试失败"
    echo "响应: $RESPONSE"
    exit 1
fi

echo ""
echo "✅ 修复完成！"
echo "📱 请访问: http://blitzepanda.top/rating"
EOF

# 运行修复脚本
chmod +x /tmp/fix_rating.sh
/tmp/fix_rating.sh
```

## 手动检查清单

如果自动修复失败，按此清单逐项检查：

### ✅ 1. 数据文件
```bash
ls -lh /opt/review-result-viewer/rating_data/stores.json
# 应该显示文件大小 > 100KB
```

### ✅ 2. 服务状态
```bash
systemctl status rating
# 应该显示 Active: active (running)
```

### ✅ 3. 端口监听
```bash
netstat -tlnp | grep 8001
# 应该显示 python3 在监听 8001 端口
```

### ✅ 4. Nginx配置
```bash
grep -A 5 "location /rating" /etc/nginx/sites-available/default
# 应该显示 proxy_pass http://127.0.0.1:8001
```

### ✅ 5. API响应
```bash
curl http://127.0.0.1:8001/api/rating/war-zones
# 应该返回JSON格式的战区列表
```

### ✅ 6. 静态文件
```bash
curl -I http://blitzepanda.top/static/rating.js
# 应该返回 200 OK
```

## 常见错误及解决

### 错误1: 下拉菜单为空
**原因**: stores.json 文件不存在或为空

**解决**:
```bash
# 从本地上传
scp rating_data/stores.json root@blitzepanda.top:/opt/review-result-viewer/rating_data/
```

### 错误2: 502 Bad Gateway
**原因**: 服务未启动或端口不对

**解决**:
```bash
systemctl restart rating
# 检查端口
netstat -tlnp | grep 8001
```

### 错误3: 静态文件404
**原因**: Nginx配置中 /static/ 路径不对

**解决**: 确保Nginx配置中有：
```nginx
location /static/ {
    alias /opt/review-result-viewer/viewer/static/;
}
```
注意：路径末尾的 `/` 很重要！

### 错误4: 服务启动失败
**原因**: Python依赖缺失或代码错误

**解决**:
```bash
# 查看详细错误
journalctl -u rating -n 50

# 手动运行测试
cd /opt/review-result-viewer
python3 rating_app.py
```

## 完整部署流程（从零开始）

如果需要完全重新部署：

```bash
# 1. 上传所有文件
scp rating_app.py root@blitzepanda.top:/opt/review-result-viewer/
scp rating_data/stores.json root@blitzepanda.top:/opt/review-result-viewer/rating_data/
scp viewer/templates/rating.html root@blitzepanda.top:/opt/review-result-viewer/viewer/templates/
scp viewer/static/rating.js root@blitzepanda.top:/opt/review-result-viewer/viewer/static/
scp viewer/static/rating.css root@blitzepanda.top:/opt/review-result-viewer/viewer/static/

# 2. SSH到服务器
ssh root@blitzepanda.top

# 3. 创建systemd服务
cat > /etc/systemd/system/rating.service << 'EOF'
[Unit]
Description=Store Rating System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/review-result-viewer
ExecStart=/usr/bin/python3 rating_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 4. 启动服务
systemctl daemon-reload
systemctl enable rating
systemctl start rating

# 5. 配置Nginx（添加到 /etc/nginx/sites-available/default）
# 参考上面的Nginx配置

# 6. 重载Nginx
nginx -t && systemctl reload nginx

# 7. 验证
curl http://blitzepanda.top/api/rating/war-zones
```

## 联系信息

如果问题仍未解决，请提供以下信息：

1. 服务状态: `systemctl status rating`
2. 服务日志: `tail -50 /opt/review-result-viewer/logs/rating_app.log`
3. Nginx错误日志: `tail -50 /var/log/nginx/error.log`
4. API测试结果: `curl http://127.0.0.1:8001/api/rating/war-zones`
