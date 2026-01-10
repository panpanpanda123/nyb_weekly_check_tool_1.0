# 门店检查项图片审核系统

一个基于Flask + PostgreSQL的门店检查项审核系统，支持图片查看、审核记录持久化、多用户协作。

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 初始化数据库
```bash
# 确保PostgreSQL正在运行
# 创建数据库
psql -U postgres -c "CREATE DATABASE configurable_ops;"

# 初始化表结构
python init_database.py
```

### 3. 启动系统
```bash
# Windows
双击 "启动周清图片检查系统.bat"

# 或命令行
python app.py
```

### 4. 访问系统
浏览器打开：`http://localhost:5001`

## 📁 项目结构

```
├── app.py                  # Flask主程序
├── database.py             # 数据库配置和模型
├── data_loader.py          # Excel数据加载
├── review_manager_db.py    # 审核数据管理（数据库版本）
├── csv_exporter.py         # CSV导出功能
├── whitelist_loader.py     # 白名单加载
├── init_database.py        # 数据库初始化脚本
├── templates/              # HTML模板
│   └── index.html
├── static/                 # 静态资源
│   ├── app.js             # 前端逻辑
│   └── style.css          # 样式文件
├── requirements.txt        # Python依赖
└── 使用文档.md            # 完整使用文档
```

## ✨ 主要功能

- ✅ 图片审核（合格/不合格）
- ✅ 问题描述记录
- ✅ 数据库持久化存储
- ✅ 按运营人员筛选
- ✅ 按门店统计完成率
- ✅ 图片点击放大查看
- ✅ 自动审核无现场结果项
- ✅ 已完成列表可编辑
- ✅ CSV导出功能
- ✅ 多用户并发支持

## 🔧 技术栈

- **后端**: Python 3.8+, Flask
- **数据库**: PostgreSQL
- **前端**: HTML5, CSS3, JavaScript (原生)
- **数据处理**: Pandas, openpyxl

## 📖 详细文档

查看 [使用文档.md](使用文档.md) 获取完整的安装、使用和故障排除指南。

## 🔑 默认配置

- **端口**: 5001
- **数据库**: `postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops`
- **白名单路径**: `D:/pythonproject/Newyobo_operat_database/daily_data/whitelist/whitelist.xlsx`

## 📝 Excel文件格式

必需列：
- 检查项名称
- 门店名称
- 门店编号
- 所属区域
- 现场结果（JSON数组格式，如 `["https://..."]`）

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License
