#!/bin/bash

echo "=========================================="
echo "配置 weeklycheck.blitzepanda.top"
echo "=========================================="
echo

# 1. 创建Nginx配置
echo "📝 创建Nginx配置..."
cat > /etc/nginx/sites-available/weeklycheck << 'EOF'
server {
    listen 80;
    server_name weeklycheck.blitzepanda.top;
    
    access_log /var/log/nginx/weeklycheck_access.log;
    error_log /var/log/nginx/weeklycheck_error.log;
    
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /api {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /opt/review-result-viewer/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

echo "✅ Nginx配置已创建"

# 2. 启用配置
echo
echo "🔗 启用Nginx配置..."
ln -sf /etc/nginx/sites-available/weeklycheck /etc/nginx/sites-enabled/
echo "✅ 配置已启用"

# 3. 测试Nginx配置
echo
echo "🧪 测试Nginx配置..."
if nginx -t; then
    echo "✅ Nginx配置正确"
else
    echo "❌ Nginx配置错误"
    exit 1
fi

# 4. 重载Nginx
echo
echo "🔄 重载Nginx..."
systemctl reload nginx
echo "✅ Nginx已重载"

# 5. 检查服务
echo
echo "🔍 检查周清审核服务..."
if systemctl is-active --quiet review-viewer; then
    echo "✅ 服务正在运行"
else
    echo "⚠️  服务未运行，尝试启动..."
    systemctl start review-viewer 2>/dev/null
    sleep 2
    if systemctl is-active --quiet review-viewer; then
        echo "✅ 服务启动成功"
    else
        echo "⚠️  服务未配置或启动失败"
        echo "   如果是首次配置，请参考文档创建服务"
    fi
fi

echo
echo "=========================================="
echo "✅ 配置完成！"
echo "=========================================="
echo
echo "📱 访问地址: http://weeklycheck.blitzepanda.top"
echo
echo "⚠️  重要提示:"
echo "1. 确保DNS已配置（A记录 weeklycheck 指向服务器IP）"
echo "2. 等待DNS生效（可能需要几分钟）"
echo "3. 确保周清审核服务运行在5001端口"
echo
echo "🔍 验证命令:"
echo "   nslookup weeklycheck.blitzepanda.top  # 检查DNS"
echo "   netstat -tlnp | grep 5001             # 检查端口"
echo "   curl http://weeklycheck.blitzepanda.top  # 测试访问"
echo
echo "🔒 配置HTTPS（可选）:"
echo "   certbot --nginx -d weeklycheck.blitzepanda.top"
echo
