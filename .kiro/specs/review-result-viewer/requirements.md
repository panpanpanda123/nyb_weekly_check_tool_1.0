# Requirements Document

## Introduction

本项目是"门店检查项图片审核系统"的配套展示系统，用于向不在公司的同事展示审核结果。系统提供多级筛选功能（战区>省份>城市>门店标签>是否合格），展示符合条件的检查项信息。数据通过管理员上传白名单和审核结果CSV文件来更新。

系统部署在Ubuntu 22.04云服务器上，使用PostgreSQL数据库，通过GitHub实现自动化部署。现有审核系统保持在本地运行。

同时，需要对现有审核系统的CSV导出功能进行增强，增加"战区""省份""城市"字段。

## Glossary

- **审核结果展示系统 (Review Result Viewer)**：面向外部同事的只读查看系统
- **审核系统 (Review System)**：现有的内部审核操作系统
- **白名单 (Whitelist)**：包含门店基础信息的Excel文件，含战区、省份、城市、门店标签等字段
- **审核结果CSV (Review Result CSV)**：审核系统导出的审核结果文件
- **战区 (War Zone)**：门店所属的大区划分
- **门店标签 (Store Tag)**：门店的分类标签

## Requirements

### Requirement 1

**User Story:** As a 外部同事, I want to 按战区、省份、城市、门店标签、是否合格筛选审核结果, so that I can 快速找到我关心的门店检查情况。

#### Acceptance Criteria

1. WHEN 用户访问展示系统首页 THEN 审核结果展示系统 SHALL 显示战区、省份、城市、门店标签、是否合格五个筛选下拉菜单和一个搜索按钮
2. WHEN 用户选择战区 THEN 审核结果展示系统 SHALL 根据所选战区动态更新省份下拉菜单的可选项
3. WHEN 用户选择省份 THEN 审核结果展示系统 SHALL 根据所选省份动态更新城市下拉菜单的可选项
4. WHEN 用户点击搜索按钮 THEN 审核结果展示系统 SHALL 根据所有筛选条件查询并展示符合条件的检查项
5. WHEN 筛选条件为空时点击搜索 THEN 审核结果展示系统 SHALL 展示所有审核结果

### Requirement 2

**User Story:** As a 外部同事, I want to 查看检查项的详细信息, so that I can 了解门店的具体检查情况。

#### Acceptance Criteria

1. WHEN 搜索结果展示时 THEN 审核结果展示系统 SHALL 显示每个检查项的门店名称、检查项名称、检查项图片、合格与否、问题描述
2. WHEN 检查项为不合格 THEN 审核结果展示系统 SHALL 以红色标识显示不合格状态和问题描述
3. WHEN 检查项为合格 THEN 审核结果展示系统 SHALL 以绿色标识显示合格状态
4. WHEN 用户点击检查项图片 THEN 审核结果展示系统 SHALL 以模态框形式放大显示图片

### Requirement 3

**User Story:** As a 管理员, I want to 上传白名单和审核结果文件来更新数据, so that I can 保持展示系统的数据最新。

#### Acceptance Criteria

1. WHEN 管理员访问数据管理页面 THEN 审核结果展示系统 SHALL 显示白名单上传和审核结果CSV上传两个功能区域
2. WHEN 管理员上传白名单Excel文件 THEN 审核结果展示系统 SHALL 解析文件并更新数据库中的门店基础信息
3. WHEN 管理员上传审核结果CSV文件 THEN 审核结果展示系统 SHALL 解析文件并更新数据库中的审核结果数据
4. WHEN 文件上传成功 THEN 审核结果展示系统 SHALL 显示导入成功的记录数量
5. IF 上传的文件格式不正确 THEN 审核结果展示系统 SHALL 显示明确的错误提示信息

### Requirement 4

**User Story:** As a 开发者, I want to 两个项目共用部分代码模块, so that I can 减少代码重复并便于维护。

#### Acceptance Criteria

1. WHEN 展示系统需要数据库操作 THEN 审核结果展示系统 SHALL 复用现有的数据库模型定义
2. WHEN 展示系统需要解析白名单 THEN 审核结果展示系统 SHALL 复用现有的白名单加载器模块
3. WHEN 两个系统部署时 THEN 审核结果展示系统 SHALL 使用独立的Flask应用入口和端口

### Requirement 5

**User Story:** As a 审核人员, I want to 导出的审核结果CSV包含战区、省份、城市字段, so that I can 在展示系统中正确关联门店信息。

#### Acceptance Criteria

1. WHEN 审核系统导出CSV时 THEN 审核系统 SHALL 在导出数据中包含战区、省份、城市三个字段
2. WHEN 导出CSV时门店在白名单中存在 THEN 审核系统 SHALL 从白名单数据库中获取该门店的战区、省份、城市信息
3. WHEN 导出CSV时门店在白名单中不存在 THEN 审核系统 SHALL 将战区、省份、城市字段设为空值

### Requirement 6

**User Story:** As a 外部同事, I want to 系统界面简洁易用, so that I can 快速上手使用。

#### Acceptance Criteria

1. WHEN 用户访问展示系统 THEN 审核结果展示系统 SHALL 采用与审核系统相似的视觉风格
2. WHEN 搜索结果为空 THEN 审核结果展示系统 SHALL 显示友好的提示信息
3. WHEN 数据正在加载 THEN 审核结果展示系统 SHALL 显示加载状态指示器

### Requirement 7

**User Story:** As a 管理员, I want to 通过GitHub一键部署系统到云服务器, so that I can 简化部署和更新流程。

#### Acceptance Criteria

1. WHEN 管理员推送代码到GitHub THEN 审核结果展示系统 SHALL 提供自动化部署脚本
2. WHEN 首次部署到Ubuntu 22.04服务器 THEN 审核结果展示系统 SHALL 提供一键安装脚本自动安装所有依赖（Python、PostgreSQL、Nginx等）
3. WHEN 系统需要更新 THEN 审核结果展示系统 SHALL 提供一键更新脚本从GitHub拉取最新代码并重启服务
4. WHEN 服务器重启 THEN 审核结果展示系统 SHALL 自动启动Web服务

### Requirement 8

**User Story:** As a 管理员, I want to 数据库部署在云服务器上, so that I can 集中管理展示系统的数据。

#### Acceptance Criteria

1. WHEN 首次部署时 THEN 审核结果展示系统 SHALL 自动创建PostgreSQL数据库和所需表结构
2. WHEN 上传数据文件时 THEN 审核结果展示系统 SHALL 将数据存储到服务器的PostgreSQL数据库中
3. WHEN 数据库连接失败 THEN 审核结果展示系统 SHALL 显示明确的错误提示并记录日志
