# 门店数据目录

此目录用于存放门店评级系统的数据文件。

## 文件说明

### stores.json
门店基础数据，包含：
- store_id: 门店ID
- store_name: 门店名称
- city: 城市
- war_zone: 战区
- regional_manager: 区域经理
- dine_in_revenue: 1月堂食营业额

**生成方式**：
```bash
python export_stores_to_json.py
```

### ratings.json
评级数据，格式：
```json
{
  "门店ID": {
    "rating": "A",
    "updated_at": "2026-02-04T12:00:00"
  }
}
```

**自动生成**：系统运行时自动创建

## 部署说明

### 本地开发
1. 运行 `python export_stores_to_json.py` 生成 stores.json
2. 启动应用 `python rating_app.py`

### 云服务器部署
1. 上传 stores.json 到服务器：
```bash
scp rating_data/stores.json root@blitzepanda.top:/opt/review-result-viewer/rating_data/
```

2. ratings.json 会自动创建

## 备份

定期备份 ratings.json：
```bash
# 从服务器下载
scp root@blitzepanda.top:/opt/review-result-viewer/rating_data/ratings.json ./backup/

# 或在服务器上备份
cp rating_data/ratings.json rating_data/ratings.backup.$(date +%Y%m%d).json
```

## 注意事项

- ⚠️ 这些文件包含敏感数据，不要上传到GitHub
- ⚠️ 已在 .gitignore 中排除 *.json 和 *.csv 文件
- ✅ 只有 .gitkeep 和 README.md 会被提交到Git
