# FinalShell 设备数据更新指南

## 推荐方式：手动上传 + 命令行

这是最简单、最安全的方式，不需要在脚本里保存密码。

### 步骤1：上传文件

1. 打开FinalShell，连接到服务器 `root@139.224.200.133`
2. 在左侧本地文件浏览器，找到你的 `equipment_status` 文件夹
3. 在右侧服务器文件浏览器，导航到 `/var/www/nyb_weekly_check_tool_1.0/equipment_status/`
4. 拖拽上传需要的文件：
   - `*在营门店*.xlsx` （必需）
   - `牛约堡集团_点餐设备表_*.xlsx` （导入POS时需要）
   - `202*.xlsx` （导入机顶盒时需要）

### 步骤2：运行导入命令

在FinalShell底部的终端窗口中执行：

```bash
# 进入项目目录
cd /var/www/nyb_weekly_check_tool_1.0

# 选择一个命令执行：

# 1. 导入所有设备
python3 import_equipment_data.py

# 2. 只导入POS（每日使用）
python3 import_equipment_data.py --only-pos

# 3. 只导入机顶盒（每周使用）
python3 import_equipment_data.py --only-stb

# 4. 清空POS数据
python3 import_equipment_data.py --clear-pos

# 5. 清空机顶盒数据
python3 import_equipment_data.py --clear-stb
```

### 步骤3：验证结果

看到这样的输出就成功了：
```
✅ 找到 245 家营业中门店
✅ 加载 312 条whitelist记录
   导入 42 条记录
✅ 数据保存成功
```

### 步骤4：访问页面查看

打开浏览器访问：https://weeklycheck.blitzepanda.top/equipment

---

## 典型使用场景

### 场景1：每日POS检查（最常用）

**需要上传的文件：**
- `*在营门店*.xlsx`
- `牛约堡集团_点餐设备表_*.xlsx`

**执行命令：**
```bash
cd /var/www/nyb_weekly_check_tool_1.0
python3 import_equipment_data.py --only-pos
```

**效果：**
- 只更新POS数据
- 机顶盒数据保持不变
- 区域经理只需处理新的POS异常

---

### 场景2：周度机顶盒检查

**需要上传的文件：**
- `*在营门店*.xlsx`
- `202*.xlsx`

**执行命令：**
```bash
cd /var/www/nyb_weekly_check_tool_1.0
python3 import_equipment_data.py --only-stb
```

**效果：**
- 只更新机顶盒数据
- POS数据保持不变
- 区域经理只需处理新的机顶盒异常

---

### 场景3：全量更新

**需要上传的文件：**
- `*在营门店*.xlsx`
- `牛约堡集团_点餐设备表_*.xlsx`
- `202*.xlsx`

**执行命令：**
```bash
cd /var/www/nyb_weekly_check_tool_1.0
python3 import_equipment_data.py
```

**效果：**
- 更新所有设备数据
- 清空所有处理记录

---

### 场景4：临时隐藏某类设备

**不需要上传文件**

**执行命令：**
```bash
cd /var/www/nyb_weekly_check_tool_1.0

# 隐藏POS
python3 import_equipment_data.py --clear-pos

# 或隐藏机顶盒
python3 import_equipment_data.py --clear-stb
```

**效果：**
- 页面不显示对应类型的设备
- 不需要重新上传文件

---

## FinalShell 快捷操作

### 保存常用命令

在FinalShell中，你可以保存常用命令：

1. 点击顶部菜单 "工具" → "命令管理器"
2. 添加常用命令：

**命令1：每日POS检查**
```bash
cd /var/www/nyb_weekly_check_tool_1.0 && python3 import_equipment_data.py --only-pos
```

**命令2：周度机顶盒检查**
```bash
cd /var/www/nyb_weekly_check_tool_1.0 && python3 import_equipment_data.py --only-stb
```

**命令3：全量更新**
```bash
cd /var/www/nyb_weekly_check_tool_1.0 && python3 import_equipment_data.py
```

以后只需要点击命令就能执行，不用每次输入。

---

## 常见问题

### Q: 上传文件时提示权限不足？
A: 确保你是用root用户登录的。

### Q: 执行命令时提示找不到文件？
A: 检查是否在正确的目录：
```bash
pwd  # 查看当前目录
cd /var/www/nyb_weekly_check_tool_1.0  # 切换到项目目录
```

### Q: 导入后没有数据？
A: 检查：
1. 文件是否上传成功
2. 文件名格式是否正确
3. 查看导入日志中的跳过原因

### Q: 如何查看服务状态？
A: 
```bash
systemctl status review-viewer
```

### Q: 如何重启服务？
A: 
```bash
systemctl restart review-viewer
```

---

## 优势

使用FinalShell手动操作的优势：
1. ✅ 不需要在脚本里保存密码（更安全）
2. ✅ 可以看到实时的上传进度
3. ✅ 可以直接在终端看到执行结果
4. ✅ 出错时可以立即看到错误信息
5. ✅ 可以保存常用命令，一键执行

---

## 小技巧

### 技巧1：快速切换目录
在FinalShell终端中，可以右键点击右侧文件浏览器的文件夹，选择"在终端中打开"，自动切换到该目录。

### 技巧2：查看历史命令
按键盘上的 ↑ 键可以查看之前执行过的命令。

### 技巧3：批量上传
可以一次选中多个文件，一起拖拽上传。

### 技巧4：对比文件
上传前可以在FinalShell中对比本地和服务器的文件，确保上传的是最新版本。

---

## 总结

使用FinalShell手动上传是最简单、最安全的方式：
1. 打开FinalShell连接服务器
2. 拖拽上传文件
3. 在终端执行导入命令
4. 完成！

不需要配置SSH密钥，不需要在脚本里保存密码，简单直接。
