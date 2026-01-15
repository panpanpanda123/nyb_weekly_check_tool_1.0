"""
测试未匹配门店功能
Test Unmatched Stores Feature
"""
import pytest
import pandas as pd
import tempfile
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from viewer.data_importer import DataImporter
from shared.database_models import Base, StoreWhitelist, ViewerReviewResult
import viewer.app_viewer as app_module


@contextmanager
def get_test_app_and_session():
    """创建测试Flask应用和数据库会话的上下文管理器"""
    # 使用内存数据库
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    SessionFactory = scoped_session(sessionmaker(bind=engine))
    
    # 替换Flask应用的数据库会话工厂
    original_session_factory = app_module.SessionFactory
    app_module.SessionFactory = SessionFactory
    
    # 创建测试客户端
    app_module.app.config['TESTING'] = True
    client = app_module.app.test_client()
    
    session = SessionFactory()
    
    try:
        yield client, session
    finally:
        session.close()
        SessionFactory.remove()
        engine.dispose()
        # 恢复原始会话工厂
        app_module.SessionFactory = original_session_factory


def test_unmatched_stores_marking():
    """测试未匹配门店的标记功能"""
    with get_test_app_and_session() as (client, session):
        # 1. 创建白名单数据（只包含部分门店）
        whitelist_data = pd.DataFrame([
            {
                '门店ID': 1001,
                '门店名称': '测试门店A',
                '战区': '华东',
                '省份': '浙江',
                '城市': '杭州',
                '门店标签': 'A类',
                '省市运营': '张三'
            },
            {
                '门店ID': 1002,
                '门店名称': '测试门店B',
                '战区': '华南',
                '省份': '广东',
                '城市': '深圳',
                '门店标签': 'B类',
                '省市运营': '李四'
            }
        ])
        
        # 保存白名单到临时文件
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp:
            whitelist_path = tmp.name
            whitelist_data.to_excel(whitelist_path, index=False)
        
        try:
            # 导入白名单
            importer = DataImporter(session)
            result = importer.import_whitelist(whitelist_path)
            assert result.success is True
            assert result.records_count == 2
            
            # 2. 创建审核结果数据（包含白名单中没有的门店）
            review_data = pd.DataFrame([
                {
                    '门店名称': '测试门店A',
                    '门店编号': '1001',
                    '检查项名称': '卫生检查',
                    '审核结果': '合格',
                    '战区': '',  # CSV中没有提供
                    '省份': '',
                    '城市': ''
                },
                {
                    '门店名称': '测试门店C',  # 这个门店不在白名单中
                    '门店编号': '1003',
                    '检查项名称': '设备检查',
                    '审核结果': '不合格',
                    '问题描述': '设备损坏',
                    '战区': '',  # CSV中没有提供
                    '省份': '',
                    '城市': ''
                },
                {
                    '门店名称': '测试门店D',  # 这个门店也不在白名单中
                    '门店编号': '1004',
                    '检查项名称': '陈列检查',
                    '审核结果': '合格',
                    '战区': '',
                    '省份': '',
                    '城市': ''
                }
            ])
            
            # 保存审核结果到临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as tmp:
                review_path = tmp.name
                review_data.to_csv(review_path, index=False, encoding='utf-8-sig')
            
            # 导入审核结果
            result = importer.import_reviews(review_path)
            assert result.success is True
            assert result.records_count == 3
            assert result.unmatched_stores_count == 2  # 门店1003和1004未匹配
            
            # 3. 验证数据库中的数据
            # 门店A应该从白名单获取地理信息
            store_a_result = session.query(ViewerReviewResult)\
                .filter(ViewerReviewResult.store_id == '1001')\
                .first()
            assert store_a_result is not None
            assert store_a_result.war_zone == '华东'
            assert store_a_result.province == '浙江'
            assert store_a_result.city == '杭州'
            
            # 门店C和D应该被标记为"[未匹配]"
            store_c_result = session.query(ViewerReviewResult)\
                .filter(ViewerReviewResult.store_id == '1003')\
                .first()
            assert store_c_result is not None
            assert store_c_result.war_zone == '[未匹配]'
            assert store_c_result.province == '[未匹配]'
            assert store_c_result.city == '[未匹配]'
            
            store_d_result = session.query(ViewerReviewResult)\
                .filter(ViewerReviewResult.store_id == '1004')\
                .first()
            assert store_d_result is not None
            assert store_d_result.war_zone == '[未匹配]'
            assert store_d_result.province == '[未匹配]'
            assert store_d_result.city == '[未匹配]'
            
            # 4. 测试未匹配门店API
            response = client.get('/api/unmatched-stores')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['data']['total_stores'] == 2  # 门店C和D
            assert data['data']['total_items'] == 2  # 2条审核记录
            
            # 验证返回的门店信息
            stores = data['data']['stores']
            store_ids = [s['store_id'] for s in stores]
            assert '1003' in store_ids
            assert '1004' in store_ids
            
        finally:
            # 清理临时文件
            if os.path.exists(whitelist_path):
                os.unlink(whitelist_path)
            if os.path.exists(review_path):
                os.unlink(review_path)


def test_csv_with_geographic_info():
    """测试CSV中已包含地理信息的情况"""
    with get_test_app_and_session() as (client, session):
        # 创建空白名单
        whitelist_data = pd.DataFrame([
            {
                '门店ID': 1001,
                '门店名称': '测试门店A',
                '战区': '华东',
                '省份': '浙江',
                '城市': '杭州',
                '门店标签': 'A类',
                '省市运营': '张三'
            }
        ])
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp:
            whitelist_path = tmp.name
            whitelist_data.to_excel(whitelist_path, index=False)
        
        try:
            importer = DataImporter(session)
            importer.import_whitelist(whitelist_path)
            
            # 创建审核结果，CSV中已包含地理信息
            review_data = pd.DataFrame([
                {
                    '门店名称': '测试门店B',
                    '门店编号': '1002',  # 不在白名单中
                    '检查项名称': '卫生检查',
                    '审核结果': '合格',
                    '战区': '华北',  # CSV中提供了地理信息
                    '省份': '北京',
                    '城市': '北京'
                }
            ])
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as tmp:
                review_path = tmp.name
                review_data.to_csv(review_path, index=False, encoding='utf-8-sig')
            
            # 导入审核结果
            result = importer.import_reviews(review_path)
            assert result.success is True
            assert result.unmatched_stores_count == 1
            
            # 验证：即使门店不在白名单中，如果CSV提供了地理信息，应该使用CSV的信息
            store_b_result = session.query(ViewerReviewResult)\
                .filter(ViewerReviewResult.store_id == '1002')\
                .first()
            assert store_b_result is not None
            assert store_b_result.war_zone == '华北'  # 使用CSV中的信息
            assert store_b_result.province == '北京'
            assert store_b_result.city == '北京'
            
        finally:
            if os.path.exists(whitelist_path):
                os.unlink(whitelist_path)
            if os.path.exists(review_path):
                os.unlink(review_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
