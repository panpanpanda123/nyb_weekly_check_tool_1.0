# 门店管理系统

一个集成了周清审核、结果展示和门店评级功能的综合管理系统。

## 📚 快速导航

- **[使用指南](使用指南.md)** - 详细的使用说明（推荐先看这个）
- **[部署指南](服务器快速部署.md)** - 服务器部署说明
- **[Git提交指南](GIT提交指南.md)** - 代码提交和更新流程

---

## 🎯 系统概览

本项目包含三个独立系统：

### 1. 周清审核系统（本地使用）
**用途**：运营人员审核门店检查项图片

**特点**：
- 📸 展示三张图片（标准图、现场图1、现场图2）
- ✅ 合格/不合格审核
- 📝 问题描述记录
- 👥 多运营人员协作
- ⌨️ 键盘快捷操作

**启动**：
```bash
python app.py
```
访问：http://localhost:5001

### 2. 审核结果展示系统（云服务器）
**用途**：展示和管理审核结果

**特点**：
- 📊 审核结果展示
- 🔍 多维度筛选
- 📥 数据导入管理
- 📈 统计分析

**访问**：http://blitzepanda.top

### 3. 门店评级系统（云服务器）
**用途**：区域经理对门店进行A/B/C评级

**特点**：
- ⭐ A/B/C三级评级
- 🔍 战区/区域经理筛选
- 📱 移动端响应式
- 💾 自动保存
- 📊 完成率统计

**访问**：http://blitzepanda.top/rating

---

## 🚀 快速开始

### 环境要求
- Python 3.8+
- PostgreSQL 12+（周清审核和展示系统需要）

### 安装依赖
```bash
pip install -r requirements.txt
```

### 本地运行

**周清审核系统：**
```bash
python app.py
```

**审核结果展示系统：**
```bash
python viewer/app_viewer.py
```

**门店评级系统：**
```bash
# 1. 导出门店数据
python export_stores_to_json.py

# 2. 启动应用
python rating_app.py
```

---

## 📖 详细文档

### 使用文档
- **[使用指南](使用指南.md)** - 三个系统的详细使用说明
- **[门店评级系统说明](门店评级系统说明.md)** - 评级系统专项说明
- **[未匹配门店处理](viewer/未匹配门店处理说明.md)** - 数据匹配问题处理

### 部署文档
- **[服务器快速部署](服务器快速部署.md)** - 快速部署参考
- **[评级系统部署指南](deploy/rating_deploy_guide.md)** - 完整部署流程
- **[Nginx配置指南](deploy/nginx_config_guide.md)** - Nginx配置说明
- **[部署总结](部署总结.md)** - 部署经验总结

### 开发文档
- **[Git提交指南](GIT提交指南.md)** - 代码提交流程
- **[提交和部署流程](提交和部署流程.md)** - 完整的提交部署流程
- **[修复说明](修复说明.md)** - 问题修复记录

---

## 📁 项目结构

```
.
├── app.py                      # 周清审核系统主程序
├── rating_app.py               # 门店评级系统主程序
├── viewer/
│   ├── app_viewer.py           # 审核结果展示系统主程序
│   ├── data_importer.py        # 数据导入工具
│   ├── templates/              # 展示和评级系统HTML模板
│   │   ├── viewer.html         # 审核结果展示页面
│   │   ├── rating.html         # 门店评级页面
│   │   └── admin.html          # 数据管理页面
│   └── static/                 # 展示和评级系统静态文件
│       ├── viewer.js/css       # 展示系统前端
│       └── rating.js/css       # 评级系统前端
├── templates/
│   └── index.html              # 周清审核系统页面
├── static/
│   ├── app.js                  # 周清审核系统前端
│   └── style.css
├── shared/
│   └── database_models.py      # 共享数据模型
├── rating_data/                # 评级系统数据目录
│   ├── stores.json             # 门店数据（不提交到Git）
│   └── ratings.json            # 评级数据（不提交到Git）
├── deploy/                     # 部署脚本和文档
├── tests/                      # 测试文件
├── 使用指南.md                 # 📖 使用说明（推荐阅读）
├── README.md                   # 本文件
└── requirements.txt            # Python依赖
```

---

## 🔧 常用操作

### 周清审核系统

**新周期导入数据：**
1. 准备新的Excel文件（包含图片链接）
2. 启动系统：`python app.py`
3. 在网页上上传Excel文件
4. 开始审核

**导出审核结果：**
- 点击页面上的"导出CSV"按钮

### 审核结果展示系统

**更新白名单：**
```bash
python reload_whitelist.py
```

**上传审核结果：**
- 访问 http://blitzepanda.top/admin
- 上传CSV文件

### 门店评级系统

**更新门店数据：**
```bash
python export_stores_to_json.py
scp rating_data/stores.json root@blitzepanda.top:/opt/review-result-viewer/rating_data/
```

**部署更新：**
```bash
# 方法1：从GitHub部署
deploy_from_github.bat

# 方法2：直接上传
scp rating_app.py root@blitzepanda.top:/opt/review-result-viewer/
ssh root@blitzepanda.top "systemctl restart rating"
```

---

## 🔐 数据安全

### 敏感数据（不提交到Git）
- `rating_data/*.json` - 评级数据
- `store_rank/whitelist.xlsx` - 白名单Excel
- `logs/` - 日志文件
- `*.db` - 数据库文件

### 备份建议
```bash
# 备份评级数据
scp root@blitzepanda.top:/opt/review-result-viewer/rating_data/ratings.json ./backup/

# 备份数据库
pg_dump configurable_ops > backup/db_backup_$(date +%Y%m%d).sql
```

---

## 🐛 故障排查

### 周清审核系统
- **图片不显示**：检查Excel中的URL是否可访问
- **上传失败**：检查文件格式和大小（最大50MB）
- **数据库连接失败**：检查PostgreSQL服务是否启动

### 门店评级系统
- **导出CSV报错**：已修复None值问题，更新代码即可
- **评级不显示**：检查服务器上的stores.json文件是否存在
- **页面无样式**：检查Nginx静态文件配置

### 服务器问题
```bash
# 查看服务状态
systemctl status rating

# 查看日志
tail -f /opt/review-result-viewer/logs/rating_app.log

# 重启服务
systemctl restart rating
```

---

## 📊 技术栈

- **后端**：Flask (Python)
- **前端**：原生JavaScript + CSS
- **数据库**：PostgreSQL（周清审核、展示系统）/ JSON文件（评级系统）
- **部署**：Systemd + Nginx
- **服务器**：Ubuntu Linux

---

## 📝 更新日志

### 2026-02-05
- ✅ 修复CSV导出None值错误
- ✅ 创建清晰的使用指南文档
- ✅ 优化项目结构说明

### 2026-02-04
- ✅ 优化门店评级系统UI
- ✅ 修复评级显示问题
- ✅ 完善部署文档
- ✅ 修复端口配置

---

## 📞 支持

如有问题，请查看：
1. **[使用指南](使用指南.md)** - 详细的操作说明
2. **[部署指南](deploy/rating_deploy_guide.md)** - 部署问题排查
3. 或联系技术支持

---

## 📄 许可证

内部使用项目
