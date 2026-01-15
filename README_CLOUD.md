# 云服务器部署 - 完整指南

## 📋 项目已为云服务器部署做好准备

我已经为您的项目创建了完整的云服务器部署方案，包括配置文件、部署脚本和详细文档。

---

## 🎯 核心问题和解决方案

### 问题1: 硬编码的Windows路径 ❌
**位置**: `app.py` 第278、331、401行
```python
whitelist_file = 'D:/pythonproject/Newyobo_operat_database/daily_data/whitelist/whitelist.xlsx'
```

**解决方案**: ✅
- 创建了 `config.py` 统一管理配置
- 创建了 `.env.example` 环境变量模板
- 创建了 `app_cloud.py` 云服务器适配版本

### 问题2: Flask开发服务器 ❌
**位置**: `app.py` 最后一行
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

**解决方案**: ✅
- 创建了 `gunicorn_config.py` 生产环境配置
- 更新了 `requirements.txt` 添加Gunicorn
- 创建了 `start_server.sh` 启动脚本

### 问题3: 缺少配置管理 ❌

**解决方案**: ✅
- 创建了完整的配置系统
- 支持环境变量
- 支持多环境部署

---

## 📁 新增文件清单

| 文件名 | 用途 | 必需性 |
|--------|------|--------|
| **config.py** | 配置管理 | ⭐⭐⭐⭐⭐ 必需 |
| **.env.example** | 环境变量模板 | ⭐⭐⭐⭐⭐ 必需 |
| **app_cloud.py** | 云服务器版本 | ⭐⭐⭐⭐⭐ 推荐 |
| **gunicorn_config.py** | Gunicorn配置 | ⭐⭐⭐⭐ 推荐 |
| **start_server.sh** | 启动脚本 | ⭐⭐⭐⭐ 推荐 |
| **migrate_to_cloud.py** | 自动迁移脚本 | ⭐⭐⭐ 可选 |
| 云服务器部署指南.md | 完整部署文档 | ⭐⭐⭐⭐⭐ 必读 |
| 代码修改清单.md | 修改检查清单 | ⭐⭐⭐⭐ 必读 |
| 云服务器部署总结.md | 总结报告 | ⭐⭐⭐⭐ 推荐 |
| 快速部署参考.md | 快速参考 | ⭐⭐⭐ 推荐 |

---

## 🚀 两种部署方案

### 方案A: 使用app_cloud.py（强烈推荐）✅

**优点**:
- ✅ 完全适配云服务器
- ✅ 不影响现有代码
- ✅ 配置灵活
- ✅ 包含日志管理
- ✅ 开箱即用

**步骤**:
```bash
# 1. 上传所有文件到服务器
scp -r ./* user@server:/var/www/inspection_system/

# 2. 配置环境
cd /var/www/inspection_system
cp .env.example .env
nano .env  # 修改配置

# 3. 启动
./start_server.sh
```

### 方案B: 修改现有app.py

**优点**:
- ✅ 保持原文件名
- ✅ 无需修改启动命令

**步骤**:
```bash
# 自动修改
python migrate_to_cloud.py

# 或手动修改3处代码
# 见"代码修改清单.md"
```

---

## ⚙️ 必须修改的配置

### 1. 创建.env文件
```bash
cp .env.example .env
nano .env
```

### 2. 修改数据库配置
```bash
DATABASE_URL=postgresql://inspection_user:你的强密码@localhost:5432/configurable_ops
```

### 3. 修改文件路径
```bash
WHITELIST_FILE=/var/www/inspection_system/data/whitelist.xlsx
EXCEL_FILE=检查项记录.xlsx
```

### 4. 生成安全密钥
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# 将输出的密钥填入.env的SECRET_KEY
```

---

## 📖 文档导航

### 新手必读
1. **云服务器部署总结.md** - 先读这个，了解全貌
2. **代码修改清单.md** - 了解需要修改什么
3. **云服务器部署指南.md** - 按步骤部署

### 快速参考
- **快速部署参考.md** - 常用命令和故障排查

### 详细文档
- **云服务器部署指南.md** - 完整的部署步骤（14个步骤）

---

## 🔧 快速部署（5分钟）

### 本地准备
```bash
# 1. 配置环境变量
cp .env.example .env
nano .env  # 修改数据库密码和路径

# 2. 测试（可选）
python app_cloud.py
```

### 云服务器部署
```bash
# 1. 安装环境
sudo apt update
sudo apt install python3 python3-pip python3-venv postgresql -y

# 2. 配置数据库
sudo -u postgres psql
CREATE DATABASE configurable_ops;
CREATE USER inspection_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE configurable_ops TO inspection_user;
\q

# 3. 上传项目
scp -r ./* user@server:/var/www/inspection_system/

# 4. 配置和启动
cd /var/www/inspection_system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # 修改配置
python init_database.py
chmod +x start_server.sh
./start_server.sh
```

---

## ✅ 部署检查清单

### 环境准备
- [ ] 云服务器已购买（推荐2核4G以上）
- [ ] Python 3.8+ 已安装
- [ ] PostgreSQL 已安装
- [ ] 已获取SSH访问权限

### 文件准备
- [ ] 所有项目文件已上传
- [ ] 白名单文件已上传到data/目录
- [ ] .env文件已创建并配置

### 数据库配置
- [ ] PostgreSQL服务已启动
- [ ] 数据库已创建
- [ ] 用户已创建并授权
- [ ] 数据库已初始化

### 应用配置
- [ ] 虚拟环境已创建
- [ ] 依赖已安装
- [ ] 配置文件已修改
- [ ] 应用可以启动

### 功能测试
- [ ] 网页可以访问
- [ ] 可以查看检查项
- [ ] 可以进行审核
- [ ] 可以导出CSV
- [ ] 管理员功能正常

### 生产环境（可选）
- [ ] Systemd服务已配置
- [ ] Nginx反向代理已配置
- [ ] SSL证书已配置
- [ ] 防火墙已配置
- [ ] 日志轮转已配置
- [ ] 自动备份已配置

---

## 🐛 常见问题

### Q1: 数据库连接失败
```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 检查配置
cat .env | grep DATABASE_URL

# 测试连接
psql -U inspection_user -d configurable_ops -h localhost
```

### Q2: 白名单文件找不到
```bash
# 检查文件
ls -la data/whitelist.xlsx

# 检查配置
cat .env | grep WHITELIST_FILE

# 上传文件
scp whitelist.xlsx user@server:/var/www/inspection_system/data/
```

### Q3: 端口被占用
```bash
# 查看占用
sudo netstat -tulpn | grep 5001

# 修改端口
nano .env  # 修改PORT=5002

# 重启
sudo systemctl restart inspection
```

### Q4: 权限问题
```bash
# 修复权限
sudo chown -R www-data:www-data /var/www/inspection_system
sudo chmod -R 755 /var/www/inspection_system
sudo chmod -R 777 /var/www/inspection_system/logs
sudo chmod -R 777 /var/www/inspection_system/uploads
```

---

## 📊 性能建议

### 推荐配置
- **CPU**: 2核以上
- **内存**: 4GB以上
- **硬盘**: 20GB以上
- **带宽**: 5Mbps以上

### Gunicorn配置
```python
workers = CPU核心数 * 2 + 1
worker_class = 'gevent'
threads = 2
timeout = 120
```

### 数据库连接池
```python
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_MAX_OVERFLOW = 20
```

---

## 🔒 安全建议

1. **修改默认密码** - 数据库、管理员账户
2. **使用强密钥** - SECRET_KEY使用随机生成
3. **配置防火墙** - 只开放必要端口
4. **使用HTTPS** - 配置SSL证书
5. **定期更新** - 系统和依赖包
6. **备份数据** - 定期备份数据库
7. **监控日志** - 定期检查异常

---

## 📞 获取帮助

### 查看日志
```bash
# 应用日志
tail -f logs/app.log

# 错误日志
tail -f logs/error.log

# 系统日志
sudo journalctl -u inspection -f
```

### 重启服务
```bash
# 重启应用
sudo systemctl restart inspection

# 重启Nginx
sudo systemctl restart nginx

# 重启PostgreSQL
sudo systemctl restart postgresql
```

---

## 🎉 部署完成后

访问您的应用:
- HTTP: `http://your-server-ip:5001`
- HTTPS: `https://your-domain.com` (配置Nginx后)

---

## 📚 相关资源

- [Flask文档](https://flask.palletsprojects.com/)
- [Gunicorn文档](https://docs.gunicorn.org/)
- [PostgreSQL文档](https://www.postgresql.org/docs/)
- [Nginx文档](https://nginx.org/en/docs/)

---

## 🎯 下一步

1. 阅读 **云服务器部署总结.md** 了解全貌
2. 按照 **云服务器部署指南.md** 逐步部署
3. 使用 **快速部署参考.md** 作为速查手册
4. 遇到问题查看 **代码修改清单.md**

祝部署顺利！🚀
