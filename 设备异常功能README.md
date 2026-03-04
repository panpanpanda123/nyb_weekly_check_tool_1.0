# 设备异常监控功能

## 🎯 功能说明

监控门店的收银设备（POS）和机顶盒离线状态，要求区域经理对异常设备进行整改反馈。

## 📍 访问地址

- **周清审核**: https://weeklycheck.blitzepanda.top/
- **门店评级**: https://weeklycheck.blitzepanda.top/rating
- **设备异常**: https://weeklycheck.blitzepanda.top/equipment

## 🚀 快速开始

### 首次部署

1. 提交代码：`git push`
2. 手动上传到服务器（参考：`手动更新设备数据指南.md`）
3. SSH登录执行：`./deploy_equipment.sh`
4. 访问测试

### 日常更新数据（推荐手动方式）

1. 下载新表格
2. 用WinSCP上传到服务器 `/var/www/nyb_weekly_check_tool_1.0/equipment_status/`
3. SSH登录执行：`python3 import_equipment_data.py`
4. 完成！

详细步骤见：`手动更新设备数据指南.md`

## 📋 服务器信息

- **IP地址**: 139.224.200.133
- **用户名**: root
- **项目**: /var/www/nyb_weekly_check_tool_1.0
- **服务**: review-viewer
- **端口**: 8000

## 📁 文件说明

- `手动更新设备数据指南.md` - **推荐阅读**：手动上传和更新教程
- `设备异常功能部署指南.md` - 完整部署指南
- `更新设备数据.bat` - 自动更新脚本（需配置SSH密钥）
- `更新设备数据.sh` - Linux/Mac自动更新脚本
- `deploy_equipment.sh` - 服务器部署脚本
- `import_equipment_data.py` - 数据导入脚本

## ✨ 功能特点

- ✅ 战区级联筛选区域经理
- ✅ 按门店分组显示设备异常
- ✅ 两种处理动作：已恢复/未恢复(需填写原因)
- ✅ 每次导入数据自动清空处理记录
- ✅ 自动排除暂停营业门店
- ✅ 导出处理结果

## 📞 快速命令

```bash
# SSH登录（用密码）
ssh root@139.224.200.133

# 进入项目目录
cd /var/www/nyb_weekly_check_tool_1.0

# 导入设备数据
python3 import_equipment_data.py

# 查看服务
systemctl status review-viewer

# 查看日志
journalctl -u review-viewer -n 100
```

## 💡 推荐工具

- **WinSCP** - 文件上传+SSH终端，最方便
- **FileZilla** - 纯文件上传
- **PuTTY** - 纯SSH终端

## 💡 提示

- 建议每周更新一次设备数据
- 处理记录不会丢失，放心更新
- 遇到问题查看部署指南
