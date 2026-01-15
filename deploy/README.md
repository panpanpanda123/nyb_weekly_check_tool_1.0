# 审核结果展示系统 - 部署指南

本文档提供审核结果展示系统在 Ubuntu 22.04 LTS 服务器上的完整部署说明。

## 目录

- [系统要求](#系统要求)
- [首次部署](#首次部署)
- [更新部署](#更新部署)
- [服务管理](#服务管理)
- [常见问题](#常见问题)
- [故障排查](#故障排查)

## 系统要求

- **操作系统**: Ubuntu 22.04 LTS
- **内存**: 最低 2GB RAM（推荐 4GB）
- **磁盘空间**: 最低 10GB 可用空间
- **网络**: 开放 80 端口（HTTP）和 443 端口（HTTPS，可选）
- **权限**: root 或 sudo 权限

## 首次部署

### 步骤 1: 准备服务器

确保服务器已更新到最新状态：

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 步骤 2: 下载部署脚本

```bash
# 克隆代码仓库到临时目录
cd /tmp
git clone <your-github-repo-url> review-viewer-temp
cd review-viewer-temp/deploy
```

### 步骤 3: 运行安装脚本

```bash
sudo bash install.sh
```

安装脚本会自动完成以下操作：

1. 安装系统依赖（Python 3.10、PostgreSQL、Nginx）
2. 创建数据库和用户
3. 克隆代码到 `/opt/review-result-viewer`
4. 配置虚拟环境并安装 Python 依赖
5. 初始化数据库表
6. 配置 Nginx 反向代理
7. 配置 Systemd 服务自启动

### 步骤 4: 验证安装

安装完成后，检查服务状态：

```bash
sudo systemctl status review-viewer
```

访问服务器 IP 地址，应该能看到展示系统首页：

```
http://your-server-ip
```

### 步骤 5: 配置域名（可选）

如果有域名，编辑 Nginx 配置：

```bash
sudo nano /etc/nginx/sites-available/review-viewer
```

将 `server_name _;` 改为 `server_name your-domain.com;`

重启 Nginx：

```bash
sudo nginx -t
sudo systemctl restart nginx
```

### 步骤 6: 配置 HTTPS（可选）

使用 Let's Encrypt 免费证书：

```bash
sudo apt-get install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## 更新部署

当代码有更新时，使用更新脚本：

```bash
cd /opt/review-result-viewer/deploy
sudo bash update.sh
```

更新脚本会自动：

1. 停止服务
2. 备份当前版本
3. 从 GitHub 拉取最新代码
4. 更新 Python 依赖
5. 执行数据库迁移（如有）
6. 重启服务

## 服务管理

### 启动服务

```bash
sudo systemctl start review-viewer
```

### 停止服务

```bash
sudo systemctl stop review-viewer
```

### 重启服务

```bash
sudo systemctl restart review-viewer
```

### 查看服务状态

```bash
sudo systemctl status review-viewer
```

### 查看实时日志

```bash
# 查看应用日志
sudo journalctl -u review-viewer -f

# 查看 Nginx 访问日志
sudo tail -f /var/log/nginx/review-viewer-access.log

# 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/review-viewer-error.log
```

### 开机自启动

```bash
# 启用开机自启动
sudo systemctl enable review-viewer

# 禁用开机自启动
sudo systemctl disable review-viewer
```

## 数据管理

### 数据库凭据

数据库凭据保存在：

```bash
cat /root/.review_viewer_db_credentials
```

### 数据库备份

```bash
# 备份数据库
sudo -u postgres pg_dump review_viewer_db > backup_$(date +%Y%m%d).sql

# 恢复数据库
sudo -u postgres psql review_viewer_db < backup_20260115.sql
```

### 上传文件管理

上传的文件存储在：

```
/opt/review-result-viewer/viewer/uploads/
```

定期清理旧文件：

```bash
# 删除 30 天前的文件
find /opt/review-result-viewer/viewer/uploads/ -type f -mtime +30 -delete
```

## 常见问题

### Q1: 服务无法启动

**检查步骤**：

1. 查看服务状态和错误信息：
   ```bash
   sudo systemctl status review-viewer
   sudo journalctl -u review-viewer -n 50
   ```

2. 检查数据库连接：
   ```bash
   sudo -u postgres psql -d review_viewer_db -c "SELECT 1;"
   ```

3. 检查端口占用：
   ```bash
   sudo netstat -tlnp | grep 8000
   ```

### Q2: 无法访问网站

**检查步骤**：

1. 检查 Nginx 状态：
   ```bash
   sudo systemctl status nginx
   sudo nginx -t
   ```

2. 检查防火墙：
   ```bash
   sudo ufw status
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

3. 检查服务是否运行：
   ```bash
   curl http://127.0.0.1:8000
   ```

### Q3: 文件上传失败

**检查步骤**：

1. 检查上传目录权限：
   ```bash
   sudo chown -R www-data:www-data /opt/review-result-viewer/viewer/uploads
   sudo chmod 755 /opt/review-result-viewer/viewer/uploads
   ```

2. 检查文件大小限制：
   ```bash
   # 在 Nginx 配置中确认
   grep client_max_body_size /etc/nginx/sites-available/review-viewer
   ```

### Q4: 数据库连接失败

**检查步骤**：

1. 检查 PostgreSQL 状态：
   ```bash
   sudo systemctl status postgresql
   ```

2. 检查数据库凭据：
   ```bash
   cat /opt/review-result-viewer/.env
   ```

3. 测试数据库连接：
   ```bash
   sudo -u postgres psql -d review_viewer_db
   ```

### Q5: 更新后服务异常

**恢复步骤**：

1. 查看备份列表：
   ```bash
   ls -lh /opt/review-viewer-backups/
   ```

2. 恢复到之前的版本：
   ```bash
   sudo systemctl stop review-viewer
   sudo tar -xzf /opt/review-viewer-backups/backup_YYYYMMDD_HHMMSS.tar.gz -C /
   sudo systemctl start review-viewer
   ```

## 故障排查

### 日志位置

- **应用日志**: `sudo journalctl -u review-viewer`
- **Nginx 访问日志**: `/var/log/nginx/review-viewer-access.log`
- **Nginx 错误日志**: `/var/log/nginx/review-viewer-error.log`
- **PostgreSQL 日志**: `/var/log/postgresql/postgresql-14-main.log`

### 性能监控

```bash
# 查看系统资源使用
htop

# 查看数据库连接数
sudo -u postgres psql -d review_viewer_db -c "SELECT count(*) FROM pg_stat_activity;"

# 查看 Nginx 连接数
sudo netstat -an | grep :80 | wc -l
```

### 重置系统

如果需要完全重置系统：

```bash
# 停止服务
sudo systemctl stop review-viewer
sudo systemctl disable review-viewer

# 删除数据库
sudo -u postgres psql -c "DROP DATABASE review_viewer_db;"
sudo -u postgres psql -c "DROP USER review_viewer;"

# 删除项目文件
sudo rm -rf /opt/review-result-viewer

# 删除配置文件
sudo rm /etc/nginx/sites-enabled/review-viewer
sudo rm /etc/nginx/sites-available/review-viewer
sudo rm /etc/systemd/system/review-viewer.service

# 重新运行安装脚本
```

## 安全建议

1. **定期更新系统**：
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

2. **配置防火墙**：
   ```bash
   sudo ufw enable
   sudo ufw allow ssh
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

3. **定期备份数据库**：
   设置 cron 任务自动备份：
   ```bash
   sudo crontab -e
   # 添加：每天凌晨 2 点备份
   0 2 * * * /usr/bin/pg_dump review_viewer_db > /backup/db_$(date +\%Y\%m\%d).sql
   ```

4. **监控日志**：
   定期检查错误日志，及时发现问题

5. **限制访问**：
   如果只允许特定 IP 访问，在 Nginx 配置中添加：
   ```nginx
   allow 192.168.1.0/24;
   deny all;
   ```

## 联系支持

如有问题，请查看：
- 项目 GitHub Issues
- 系统日志文件
- 本文档的常见问题部分

---

**最后更新**: 2026-01-15
