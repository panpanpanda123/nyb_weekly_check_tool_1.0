# 设备异常功能使用说明

## 功能概述
设备异常监控功能用于追踪和处理门店的离线设备（POS收银系统和机顶盒）。

## 📍 访问地址
- **周清审核**: https://weeklycheck.blitzepanda.top/
- **门店评级**: https://weeklycheck.blitzepanda.top/rating
- **设备异常**: https://weeklycheck.blitzepanda.top/equipment

## 快速开始

### 本地测试
1. 将数据文件放入 `equipment_status/` 目录
2. 双击运行对应的批处理文件：
   - `本地更新所有设备.bat` - 导入所有设备
   - `更新POS数据.bat` - 只导入POS
   - `更新机顶盒数据.bat` - 只导入机顶盒
   - `清空POS数据.bat` - 清空POS数据
   - `清空机顶盒数据.bat` - 清空机顶盒数据

### 服务器部署
参考《手动更新设备数据指南.md》

## 导入模式说明

### 1. 导入所有设备（默认）
```bash
python3 import_equipment_data.py
```
- 导入POS和机顶盒的所有数据
- 清空并替换旧数据和处理记录

### 2. 只导入POS
```bash
python3 import_equipment_data.py --only-pos
```
- 只导入收银系统数据
- 清空旧POS数据和处理记录
- 保留机顶盒数据不变
- **使用场景**：每日检查收银系统状态

### 3. 只导入机顶盒
```bash
python3 import_equipment_data.py --only-stb
```
- 只导入机顶盒数据
- 清空旧机顶盒数据和处理记录
- 保留POS数据不变
- **使用场景**：定期检查机顶盒状态

### 4. 清空POS数据
```bash
python3 import_equipment_data.py --clear-pos
```
- 清空所有POS设备记录和处理记录
- 不导入新数据
- **使用场景**：今天不需要展示POS数据

### 5. 清空机顶盒数据
```bash
python3 import_equipment_data.py --clear-stb
```
- 清空所有机顶盒设备记录和处理记录
- 不导入新数据
- **使用场景**：今天不需要展示机顶盒数据

## 数据文件要求

### 必需文件
1. **在营门店文件**（必需）
   - 文件名：`*在营门店*.xlsx`
   - Sheet：营业门店
   - C列：门店ID
   - I列：营业状态（必须为"营业中"）

2. **收银设备文件**（导入POS时必需）
   - 文件名：`牛约堡集团_点餐设备表_*.xlsx`
   - 设备编号列：门店ID
   - 状态列：离线

3. **机顶盒文件**（导入机顶盒时必需）
   - 文件名：`202*.xlsx`
   - 设备编码列：门店ID
   - 状态列：离线

## 数据处理逻辑

### 过滤规则
1. 只导入营业状态为"营业中"的门店
2. 只导入在白名单中的门店（用于匹配战区和区域经理）
3. 只导入状态为"离线"的设备

### 数据清理规则
- 每次导入会清空对应设备类型的旧数据和处理记录
- `--only-pos`：只清空POS相关数据
- `--only-stb`：只清空机顶盒相关数据
- 默认模式：清空所有设备数据

## 典型使用场景

### 场景1：每日POS检查
```bash
# 每天早上更新POS数据
python3 import_equipment_data.py --only-pos
```
- 机顶盒数据保持不变
- 区域经理只需处理新的POS异常

### 场景2：周度机顶盒检查
```bash
# 每周一更新机顶盒数据
python3 import_equipment_data.py --only-stb
```
- POS数据保持不变
- 区域经理只需处理新的机顶盒异常

### 场景3：临时隐藏某类设备
```bash
# 今天不想显示POS数据
python3 import_equipment_data.py --clear-pos
```
- 页面只显示机顶盒数据
- 不影响数据库中的机顶盒记录

### 场景4：全量更新
```bash
# 同时更新所有设备
python3 import_equipment_data.py
```
- 所有数据都会更新
- 所有处理记录都会清空

## 前端功能

### 筛选功能
- 战区筛选（级联）
- 区域经理筛选（根据战区动态更新）
- 门店搜索（门店ID或名称）

### 处理功能
- 已恢复：标记设备已恢复正常
- 未恢复原因：记录设备未恢复的原因
- 修改：允许修改已处理的记录

### 导出功能
- 导出处理结果为Excel
- 包含门店信息、设备类型、处理状态、处理原因等

## 操作提示

页面顶部会显示操作提示：
1. 请沟通门店重启机顶盒、打开平板确保收银系统在最前展示
2. 注意：机顶盒画面正确也有可能存在掉线情况
3. 小提示：收银系统状态可通过牛约堡小程序查看

## 数据库表结构

### equipment_status
- store_id：门店ID
- store_name：门店名称
- war_zone：战区
- regional_manager：区域经理
- equipment_type：设备类型（POS/机顶盒）
- equipment_id：设备ID
- equipment_name：设备名称
- status：状态
- import_time：导入时间

### equipment_processing
- store_id：门店ID
- equipment_type：设备类型（POS/机顶盒）
- action：处理动作（已恢复/未恢复原因）
- reason：未恢复原因
- processed_at：处理时间
- processed_by：处理人

## 📋 服务器信息
- **IP地址**: 139.224.200.133
- **用户名**: root
- **项目**: /var/www/nyb_weekly_check_tool_1.0
- **服务**: review-viewer
- **端口**: 8000

## 📞 快速命令

```bash
# SSH登录
ssh root@139.224.200.133

# 进入项目目录
cd /var/www/nyb_weekly_check_tool_1.0

# 导入所有设备数据
python3 import_equipment_data.py

# 只导入POS
python3 import_equipment_data.py --only-pos

# 只导入机顶盒
python3 import_equipment_data.py --only-stb

# 清空POS数据
python3 import_equipment_data.py --clear-pos

# 清空机顶盒数据
python3 import_equipment_data.py --clear-stb

# 查看服务
systemctl status review-viewer

# 重启服务
systemctl restart review-viewer

# 查看日志
journalctl -u review-viewer -n 100
```

## 常见问题

### Q: 为什么导入后没有数据？
A: 检查：
1. 文件是否在 `equipment_status/` 目录
2. 门店是否在白名单中
3. 门店营业状态是否为"营业中"
4. 设备状态是否为"离线"

### Q: 如何只更新POS不影响机顶盒？
A: 使用 `--only-pos` 参数

### Q: 处理记录会保留吗？
A: 不会。每次导入对应类型的设备数据时，会清空该类型的处理记录

### Q: 如何更新白名单？
A: 参考《更新白名单完整指南.md》

## 💡 推荐工具
- **WinSCP** - 文件上传+SSH终端，最方便
- **FileZilla** - 纯文件上传
- **PuTTY** - 纯SSH终端

## 相关文档
- 《手动更新设备数据指南.md》- 详细的导入操作指南
- 《更新白名单完整指南.md》- 白名单更新指南
- 《营业状态逻辑变更说明.md》- 营业状态判断逻辑
- 《设备处理功能优化说明.md》- 功能优化历史
