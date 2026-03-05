# Task 8: 设备分类处理功能实现总结

## 需求描述

将设备异常处理从"按门店统一处理"改为"按设备类型分别处理"。一家门店的 POS（收银系统）和机顶盒可以分别反馈处理状态。

## 实现方案

### 1. 数据库层修改

**文件**: `shared/database_models.py`

- 在 `EquipmentProcessing` 模型中添加 `equipment_type` 字段（必需字段）
- 添加复合索引 `idx_processing_store_type` (store_id, equipment_type)
- 更新 `to_dict()` 方法包含 `equipment_type`

**关键变更**:
```python
# 新增字段
equipment_type = Column(String(50), nullable=False, comment='设备类型：POS/机顶盒')

# 新增索引
Index('idx_processing_store_type', 'store_id', 'equipment_type')
```

### 2. 后端 API 修改

**文件**: `viewer/app_viewer.py`

#### 2.1 搜索 API (`/api/equipment/search`)
- 修改处理记录查询逻辑，按 `store_id` 和 `equipment_type` 组合键存储
- 返回数据中分别包含 `processing_pos` 和 `processing_stb` 字段

**关键变更**:
```python
# 处理记录按门店ID和设备类型分组
processing_dict = {}
for p in processing_records:
    key = f"{p.store_id}_{p.equipment_type}"
    processing_dict[key] = p.to_dict()

# 返回数据包含两种设备类型的处理状态
stores_data[equipment.store_id] = {
    # ...
    'processing_pos': processing_dict.get(f"{equipment.store_id}_POS"),
    'processing_stb': processing_dict.get(f"{equipment.store_id}_机顶盒")
}
```

#### 2.2 处理 API (`/api/equipment/process`)
- 请求参数新增 `equipment_type` 字段（必需）
- 查询和更新处理记录时同时使用 `store_id` 和 `equipment_type` 作为条件

**关键变更**:
```python
# 请求参数
equipment_type = data.get('equipment_type')  # POS/机顶盒

# 查询条件
existing = session.query(EquipmentProcessing)\
    .filter(EquipmentProcessing.store_id == store_id)\
    .filter(EquipmentProcessing.equipment_type == equipment_type)\
    .first()
```

#### 2.3 导出 API (`/api/equipment/export`)
- 更新导出逻辑，按 `store_id` 和 `equipment_type` 匹配处理记录
- 导出字段名称从"特殊情况理由"改为"未恢复原因"

### 3. 前端界面修改

**文件**: `viewer/static/equipment.js`

#### 3.1 渲染逻辑 (`renderEquipmentList`)
- 将设备列表按类型分组（POS / 机顶盒）
- 每个设备组独立渲染，包含：
  - 设备组标题（收银系统 POS / 机顶盒）
  - 该类型的设备列表
  - 该类型的处理按钮区域

**关键变更**:
```javascript
// 按设备类型分组
const posEquipment = store.equipment.filter(eq => eq.equipment_type === 'POS');
const stbEquipment = store.equipment.filter(eq => eq.equipment_type === '机顶盒');

// 分别渲染每个设备组
${posEquipment.length > 0 ? `
    <div class="equipment-group">
        <div class="equipment-group-title">收银系统 (POS)</div>
        <!-- 设备列表 -->
        ${renderProcessingSection(store, 'POS', store.processing_pos)}
    </div>
` : ''}
```

#### 3.2 处理区域渲染 (`renderProcessingSection`)
- 接收 `equipmentType` 参数
- 在处理按钮和输入框上添加 `data-equipment-type` 属性
- 根据设备类型显示对应的处理状态

**关键变更**:
```javascript
function renderProcessingSection(store, equipmentType, processing) {
    // 处理按钮带设备类型标识
    <div class="processing-actions" data-equipment-type="${equipmentType}">
        <button class="action-btn btn-processed" data-action="已恢复">✓ 已恢复</button>
        <button class="action-btn btn-special">⚠ 未恢复</button>
    </div>
    <div class="reason-input-container" data-equipment-type="${equipmentType}" style="display:none;">
        <!-- 输入框 -->
    </div>
}
```

#### 3.3 事件绑定 (`bindProcessingEvents`)
- 从按钮的父元素获取 `data-equipment-type` 属性
- 根据设备类型定位对应的输入框和按钮
- 调用处理函数时传递 `equipmentType` 参数

**关键变更**:
```javascript
// 获取设备类型
const actionsDiv = this.closest('.processing-actions');
const equipmentType = actionsDiv.dataset.equipmentType;

// 定位对应的输入框
const reasonContainer = card.querySelector(
    `.reason-input-container[data-equipment-type="${equipmentType}"]`
);
```

#### 3.4 处理函数 (`processEquipment`)
- 函数签名增加 `equipmentType` 参数
- 请求体中包含 `equipment_type` 字段

**关键变更**:
```javascript
async function processEquipment(storeId, equipmentType, action, reason) {
    body: JSON.stringify({
        store_id: storeId,
        equipment_type: equipmentType,  // 新增
        action: action,
        reason: reason
    })
}
```

### 4. 样式修改

**文件**: `viewer/static/equipment.css`

新增设备分组样式：
- `.equipment-group` - 设备组容器
- `.equipment-group-title` - 设备组标题
- 移动端响应式优化

### 5. 缓存版本更新

**文件**: `viewer/templates/equipment.html`

- 更新 CSS 缓存版本：`v=20260305-1`

### 6. 数据库迁移脚本

**文件**: `migrate_equipment_processing.py`

- 检查表和列是否存在
- 清空旧的处理记录（因为新增必需字段）
- 添加 `equipment_type` 列
- 创建复合索引
- 移除默认值

## 部署文档

**文件**: `设备分类处理更新指南.md`

包含完整的部署步骤、注意事项和回滚方案。

## 测试要点

1. **设备分组显示**
   - 确认 POS 和机顶盒分别显示在不同的设备组中
   - 设备组标题正确显示

2. **独立处理**
   - 可以单独处理 POS 设备（已恢复/未恢复）
   - 可以单独处理机顶盒设备（已恢复/未恢复）
   - 两种设备的处理状态互不影响

3. **状态显示**
   - 处理后状态正确显示在对应的设备组下
   - 刷新页面后状态保持正确

4. **导出功能**
   - 导出的 Excel 文件包含设备类型和对应的处理状态
   - 数据完整准确

5. **移动端**
   - 移动端显示正常
   - 按钮可点击，输入框可用

## 影响范围

### 数据库
- `equipment_processing` 表结构变更
- 旧的处理记录被清空

### 用户影响
- 区域经理需要重新处理设备异常
- 可以更精细地管理不同类型设备的处理状态

### 兼容性
- 不影响其他功能（周清审核、门店评级）
- 需要清除浏览器缓存以加载新的 JS/CSS

## 文件清单

### 修改的文件
1. `shared/database_models.py` - 数据库模型
2. `viewer/app_viewer.py` - 后端 API
3. `viewer/static/equipment.js` - 前端逻辑
4. `viewer/static/equipment.css` - 样式文件
5. `viewer/templates/equipment.html` - HTML 模板

### 新增的文件
1. `migrate_equipment_processing.py` - 数据库迁移脚本
2. `设备分类处理更新指南.md` - 部署指南
3. `TASK8_设备分类处理实现总结.md` - 本文档

## 完成状态

✅ 数据库模型修改完成
✅ 后端 API 修改完成
✅ 前端界面修改完成
✅ 样式优化完成
✅ 迁移脚本编写完成
✅ 部署文档编写完成

## 下一步

1. 在本地或测试环境验证功能
2. 备份生产数据库
3. 按照部署指南执行部署
4. 验证功能正常
5. 通知区域经理重新处理设备异常
