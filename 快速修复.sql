-- 快速修复 SQL 脚本
-- 为 equipment_processing 表添加 equipment_type 字段

-- 1. 清空旧数据（因为需要添加必需字段）
DELETE FROM equipment_processing;

-- 2. 添加 equipment_type 字段
ALTER TABLE equipment_processing 
ADD COLUMN equipment_type VARCHAR(50) NOT NULL DEFAULT 'POS';

-- 3. 创建复合索引
CREATE INDEX IF NOT EXISTS idx_processing_store_type 
ON equipment_processing(store_id, equipment_type);

-- 4. 移除默认值
ALTER TABLE equipment_processing 
ALTER COLUMN equipment_type DROP DEFAULT;

-- 5. 验证
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'equipment_processing' 
ORDER BY ordinal_position;
