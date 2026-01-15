# Implementation Plan

## Phase 1: 项目结构和共用模块

- [x] 1. 创建项目目录结构和共用模块





  - [x] 1.1 创建 `viewer/`、`shared/`、`deploy/` 目录结构


    - 创建展示系统、共用模块、部署脚本的目录
    - _Requirements: 4.1, 4.2, 4.3_
  - [x] 1.2 创建共用数据库模型 `shared/database_models.py`


    - 定义 StoreWhitelist 和 ViewerReviewResult 模型
    - 包含索引定义
    - _Requirements: 4.1_
  - [x] 1.3 编写属性测试：数据导入round-trip


    - **Property 4: 数据导入round-trip**
    - **Validates: Requirements 3.2, 3.3**

## Phase 2: 修改现有审核系统CSV导出

- [x] 2. 增强CSV导出功能





  - [x] 2.1 修改 `csv_exporter.py` 增加战区、省份、城市字段


    - 从数据库获取门店的战区、省份、城市信息
    - 门店不存在时字段为空
    - _Requirements: 5.1, 5.2, 5.3_
  - [x] 2.2 编写属性测试：CSV导出字段完整性


    - **Property 7: CSV导出字段完整性**
    - **Validates: Requirements 5.1, 5.2, 5.3**

- [ ] 3. Checkpoint - 确保所有测试通过
  - Ensure all tests pass, ask the user if questions arise.

## Phase 3: 展示系统后端

- [x] 4. 创建数据导入模块





  - [x] 4.1 创建 `viewer/data_importer.py`


    - 实现白名单Excel导入功能
    - 实现审核结果CSV导入功能
    - 实现文件格式验证
    - _Requirements: 3.2, 3.3, 3.5_
  - [x] 4.2 编写属性测试：导入记录数一致性


    - **Property 5: 导入记录数一致性**
    - **Validates: Requirements 3.4**
  - [x] 4.3 编写属性测试：无效文件格式处理


    - **Property 6: 无效文件格式处理**
    - **Validates: Requirements 3.5**

- [x] 5. 创建展示系统Flask应用





  - [x] 5.1 创建 `viewer/app_viewer.py` 基础框架


    - 初始化Flask应用
    - 配置数据库连接
    - 实现首页路由
    - _Requirements: 1.1, 6.1_
  - [x] 5.2 实现筛选选项API `/api/filters`


    - 返回战区、省份、城市、门店标签、是否合格的选项列表
    - _Requirements: 1.1_
  - [x] 5.3 实现级联筛选API `/api/filters/provinces` 和 `/api/filters/cities`


    - 根据战区返回省份列表
    - 根据省份返回城市列表
    - _Requirements: 1.2, 1.3_
  - [x] 5.4 编写属性测试：级联筛选一致性



    - **Property 1: 级联筛选一致性**
    - **Validates: Requirements 1.2, 1.3**
  - [x] 5.5 实现搜索API `/api/search`


    - 根据筛选条件查询审核结果
    - 支持多条件组合查询
    - _Requirements: 1.4, 1.5_
  - [x] 5.6 编写属性测试：搜索结果筛选正确性


    - **Property 2: 搜索结果筛选正确性**
    - **Validates: Requirements 1.4**
  - [x] 5.7 实现数据上传API `/api/upload/whitelist` 和 `/api/upload/reviews`


    - 处理文件上传
    - 调用数据导入模块
    - 返回导入结果
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 6. Checkpoint - 确保所有测试通过
  - Ensure all tests pass, ask the user if questions arise.

## Phase 4: 展示系统前端

- [x] 7. 创建展示系统前端页面




  - [x] 7.1 创建 `viewer/templates/viewer.html`


    - 筛选区域（战区、省份、城市、门店标签、是否合格下拉菜单）
    - 搜索按钮
    - 结果展示区域
    - 图片模态框
    - _Requirements: 1.1, 2.1, 2.4_
  - [x] 7.2 创建 `viewer/static/viewer.css`


    - 复用审核系统的视觉风格
    - 合格/不合格状态样式
    - _Requirements: 2.2, 2.3, 6.1_
  - [x] 7.3 创建 `viewer/static/viewer.js`


    - 级联筛选逻辑
    - 搜索功能
    - 结果渲染
    - 图片放大功能
    - 加载状态显示
    - _Requirements: 1.2, 1.3, 1.4, 2.4, 6.2, 6.3_
  - [x] 7.4 编写属性测试：搜索结果字段完整性


    - **Property 3: 搜索结果字段完整性**
    - **Validates: Requirements 2.1**

- [x] 8. 创建数据管理页面






  - [x] 8.1 创建 `viewer/templates/admin.html`

    - 白名单上传区域
    - 审核结果CSV上传区域
    - 上传结果显示
    - _Requirements: 3.1_
  - [x] 8.2 实现上传功能的前端逻辑

    - 文件选择和上传
    - 进度显示
    - 结果反馈
    - _Requirements: 3.4, 3.5_

- [ ] 9. Checkpoint - 确保所有测试通过
  - Ensure all tests pass, ask the user if questions arise.

## Phase 5: 部署脚本

- [x] 10. 创建部署脚本






  - [x] 10.1 创建首次安装脚本 `deploy/install.sh`

    - 安装系统依赖（Python、PostgreSQL、Nginx）
    - 创建数据库和用户
    - 配置虚拟环境
    - 配置Nginx和Systemd
    - _Requirements: 7.2, 8.1_
  - [x] 10.2 创建更新脚本 `deploy/update.sh`


    - 拉取最新代码
    - 更新依赖
    - 重启服务
    - _Requirements: 7.3_


  - [x] 10.3 创建Nginx配置 `deploy/nginx.conf`

    - 反向代理配置
    - 静态文件配置
    - _Requirements: 7.2_
  - [x] 10.4 创建Systemd服务配置 `deploy/viewer.service`


    - 服务自启动配置
    - _Requirements: 7.4_

  - [x] 10.5 创建部署说明文档 `deploy/README.md`

    - 部署步骤说明
    - 常见问题解答
    - _Requirements: 7.1_

- [x] 11. Final Checkpoint - 确保所有测试通过





  - Ensure all tests pass, ask the user if questions arise.
