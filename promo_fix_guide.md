# 活动参与度重复数据修复指南

## 问题描述

在活动参与度监控系统中，发现同一个门店会显示多条数据，导致数据重复。

## 问题原因

1. 数据库表结构问题：`promo_participation` 表使用自增 `id` 作为主键，而不是 `store_id`
2. 导入逻辑问题：之前只清空"同一日期"的数据，如果新文件包含多天数据但日期不同，会导致重复

## 解决方案

### 1. 修改数据库表结构

将 `store_id` 改为主键，确保每个门店只能有一条记录。

### 2. 修改导入逻辑

每次导入时清空所有旧数据，以最新上传的文件为准。

## 执行步骤（推荐使用快速修复脚本）

### 服务器环境修复步骤

1. SSH 连接到服务器：
```bash
ssh root@weeklycheck.blitzepanda.top
```

2. 进入项目目录：
```bash
cd /root/review-viewer
```

3. 激活虚拟环境：
```bash
source venv/bin/activate
```

4. 运行快速修复脚本：
```bash
python fix_promo_duplicates.py
```

这个脚本会：
- 自动清理可能存在的临时表
- 检查并显示重复数据统计
- 创建新表结构（store_id 作为主键）
- 每个门店只保留最新的一条记录
- 自动创建索引

5. 重启服务：
```bash
sudo systemctl restart review-viewer
```

### 本地环境修复步骤

```bash
python fix_promo_duplicates.py
```

## 验证结果

1. 访问 https://weeklycheck.blitzepanda.top/promoratio
2. 搜索任意门店，确认每个门店只显示一条数据
3. 检查数据是否为最新上传文件中的数据

## 常见错误处理

### 错误：duplicate key value violates unique constraint

如果看到这个错误，说明临时表中已经有数据了。

解决方法：
1. 使用 `fix_promo_duplicates.py` 脚本（推荐）
2. 或者手动删除临时表后重试：
```bash
psql -U postgres -d configurable_ops -c "DROP TABLE IF EXISTS promo_participation_new;"
```

## 后续导入新数据

修复完成后，使用以下命令导入新的活动参与度数据：

```bash
# 将新的 Excel 文件放到 promo_data 文件夹
# 然后运行导入脚本
python import_promo_data.py
```

导入脚本会自动：
- 清空所有旧数据
- 导入新文件中的数据
- 由于 store_id 是主键，不会再出现重复

## 文件修改清单

- `shared/database_models.py` - 修改 PromoParticipation 模型
- `import_promo_data.py` - 修改导入逻辑
- `fix_promo_duplicates.py` - 快速修复脚本（推荐使用）
- `migrate_promo_table.py` - 迁移脚本（备用）
