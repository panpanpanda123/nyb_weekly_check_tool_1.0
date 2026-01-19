# 审核结果展示系统 - 运营筛选功能修改说明

## 修改日期
2025-01-19

## 修改内容

### 功能变更
1. **移除**：门店标签筛选功能
2. **新增**：运营筛选功能（优先临时运营，其次省市运营）

### 运营字段优先级
- 优先使用 `temp_operator`（临时运营）
- 如果临时运营为空，则使用 `city_operator`（省市运营）
- 使用 SQL 的 `COALESCE` 函数实现

### 筛选逻辑
- 运营筛选为独立筛选条件
- 可与战区、省份、城市、是否合格等条件组合使用
- 多条件同时生效（AND 逻辑）

## 修改文件清单

### 1. 后端文件：`viewer/app_viewer.py`
**修改位置 1** - `/api/filters` 接口（约第 60-80 行）
- 移除：门店标签列表查询
- 新增：运营列表查询（使用 COALESCE 优先级）

**修改位置 2** - `/api/search` 接口（约第 180-220 行）
- 移除：`store_tag` 参数和筛选逻辑
- 新增：`operator` 参数和筛选逻辑（JOIN 白名单表）

### 2. 前端模板：`viewer/templates/viewer.html`
**修改位置** - 筛选区域（约第 50 行）
- 移除：门店标签下拉菜单
- 新增：运营下拉菜单（同位置替换）

### 3. 前端脚本：`viewer/static/viewer.js`
**修改位置 1** - 全局状态定义（约第 3-18 行）
- 移除：`store_tags` 和 `store_tag`
- 新增：`operators` 和 `operator`

**修改位置 2** - 加载筛选选项（约第 70 行）
- 移除：填充门店标签下拉菜单
- 新增：填充运营下拉菜单

**修改位置 3** - 事件绑定（约第 230 行）
- 移除：门店标签选择变化事件
- 新增：运营选择变化事件

**修改位置 4** - 构建查询参数（约第 450 行）
- 移除：`store_tag` 参数
- 新增：`operator` 参数

**修改位置 5** - 清除筛选条件（约第 580 行）
- 移除：重置门店标签
- 新增：重置运营

## 数据库查询示例

### 获取运营列表
```sql
SELECT DISTINCT COALESCE(temp_operator, city_operator) as operator
FROM store_whitelist
WHERE COALESCE(temp_operator, city_operator) IS NOT NULL
  AND COALESCE(temp_operator, city_operator) != ''
ORDER BY operator;
```

### 按运营筛选审核结果
```sql
SELECT vr.*
FROM viewer_review_results vr
JOIN store_whitelist sw ON vr.store_id = sw.store_id
WHERE COALESCE(sw.temp_operator, sw.city_operator) = '选中的运营'
  AND vr.war_zone = '选中的战区'  -- 可选
  AND vr.province = '选中的省份'  -- 可选
  AND vr.city = '选中的城市'      -- 可选
  AND vr.review_result = '不合格' -- 可选
ORDER BY vr.store_id, vr.review_time DESC;
```

## 测试建议

### 功能测试
1. ✅ 运营下拉菜单正常加载
2. ✅ 选择运营后能正确筛选结果
3. ✅ 运营 + 战区组合筛选
4. ✅ 运营 + 省份组合筛选
5. ✅ 运营 + 城市组合筛选
6. ✅ 运营 + 是否合格组合筛选
7. ✅ 清除筛选条件功能正常

### 数据验证
1. 验证临时运营优先级（有临时运营的门店）
2. 验证省市运营降级（无临时运营的门店）
3. 验证空值处理（运营字段都为空的门店）

## 部署步骤

1. **提交代码到 GitHub**
   ```bash
   git add viewer/app_viewer.py viewer/templates/viewer.html viewer/static/viewer.js
   git commit -m "feat: 替换门店标签为运营筛选功能（优先临时运营）"
   git push origin main
   ```

2. **服务器更新**
   ```bash
   cd /path/to/project
   git pull origin main
   # 如果使用 systemd 或 supervisor，重启服务
   sudo systemctl restart viewer-app
   # 或
   sudo supervisorctl restart viewer-app
   ```

3. **清除浏览器缓存**
   - 前端文件有修改，建议用户清除缓存或使用 Ctrl+F5 强制刷新

## 注意事项

1. **数据库无需修改**：使用现有字段，无需迁移
2. **向后兼容**：移除的门店标签功能不影响现有数据
3. **性能优化**：`city_operator` 字段已有索引，查询性能良好
4. **已完成状态**：继续使用 localStorage 保存，无需修改

## 回滚方案

如需回滚到门店标签版本：
```bash
git revert HEAD
git push origin main
# 服务器执行 git pull 并重启服务
```

---

**修改完成！** 🎉

所有修改遵循"如无必要，勿增实体"原则，保持代码简洁高效。
