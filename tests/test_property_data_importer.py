"""
数据导入器属性测试
Property-Based Tests for Data Importer
"""
import pytest
import pandas as pd
import tempfile
import os
from contextlib import contextmanager
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from viewer.data_importer import DataImporter, ImportResult
from shared.database_models import Base, StoreWhitelist, ViewerReviewResult


@contextmanager
def get_test_db_session():
    """创建测试数据库会话的上下文管理器"""
    # 使用内存数据库
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


# 生成器：生成白名单数据
@st.composite
def whitelist_data(draw):
    """生成白名单测试数据"""
    num_records = draw(st.integers(min_value=1, max_value=50))
    
    # 生成唯一的门店ID列表
    store_ids = draw(st.lists(
        st.integers(min_value=1000, max_value=99999),
        min_size=num_records,
        max_size=num_records,
        unique=True
    ))
    
    records = []
    for store_id in store_ids:
        record = {
            '门店ID': store_id,
            '门店名称': draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L',)))),
            '战区': draw(st.sampled_from(['华东', '华南', '华北', '西南', ''])),
            '省份': draw(st.sampled_from(['广东', '浙江', '江苏', '上海', '北京', ''])),
            '城市': draw(st.sampled_from(['深圳', '广州', '杭州', '苏州', '上海', '北京', ''])),
            '门店标签': draw(st.sampled_from(['A类', 'B类', 'C类', ''])),
            '省市运营': draw(st.text(min_size=0, max_size=10, alphabet=st.characters(whitelist_categories=('L',)))),
            '临时运营': draw(st.text(min_size=0, max_size=10, alphabet=st.characters(whitelist_categories=('L',)))),
        }
        records.append(record)
    
    return pd.DataFrame(records)


# 生成器：生成审核结果数据
@st.composite
def review_data(draw):
    """生成审核结果测试数据"""
    num_records = draw(st.integers(min_value=1, max_value=50))
    
    records = []
    for i in range(num_records):
        record = {
            '门店名称': draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L',)))),
            '门店编号': str(draw(st.integers(min_value=1000, max_value=9999))),
            '战区': draw(st.sampled_from(['华东', '华南', '华北', '西南', ''])),
            '省份': draw(st.sampled_from(['广东', '浙江', '江苏', '上海', '北京', ''])),
            '城市': draw(st.sampled_from(['深圳', '广州', '杭州', '苏州', '上海', '北京', ''])),
            '所属区域': draw(st.text(min_size=0, max_size=20, alphabet=st.characters(whitelist_categories=('L',)))),
            '检查项名称': draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L',)))),
            '检查项分类': draw(st.sampled_from(['卫生', '陈列', '设备', ''])),
            '标准图': draw(st.text(min_size=0, max_size=50)),
            '审核结果': draw(st.sampled_from(['合格', '不合格'])),
            '问题描述': draw(st.text(min_size=0, max_size=50, alphabet=st.characters(whitelist_categories=('L',)))),
            '审核时间': draw(st.sampled_from(['2026-01-15 10:00:00', '2026-01-14 15:30:00', ''])),
        }
        records.append(record)
    
    return pd.DataFrame(records)


class TestDataImporterProperties:
    """数据导入器属性测试"""
    
    @given(df=whitelist_data())
    @settings(max_examples=100, deadline=None)
    def test_property_whitelist_import_count_consistency(self, df):
        """
        **Feature: review-result-viewer, Property 5: 导入记录数一致性**
        **Validates: Requirements 3.4**
        
        For any 成功导入的白名单文件，返回的导入记录数应等于文件中的有效数据行数
        """
        with get_test_db_session() as session:
            # 创建临时Excel文件
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp:
                tmp_path = tmp.name
                df.to_excel(tmp_path, index=False)
            
            try:
                # 导入数据
                importer = DataImporter(session)
                result = importer.import_whitelist(tmp_path)
                
                # 验证：导入记录数应等于DataFrame的行数
                expected_count = len(df)
                assert result.records_count == expected_count, \
                    f"导入记录数 {result.records_count} 不等于文件行数 {expected_count}"
                
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    
    @given(df=review_data())
    @settings(max_examples=100, deadline=None)
    def test_property_reviews_import_count_consistency(self, df):
        """
        **Feature: review-result-viewer, Property 5: 导入记录数一致性**
        **Validates: Requirements 3.4**
        
        For any 成功导入的审核结果文件，返回的导入记录数应等于文件中的有效数据行数
        """
        with get_test_db_session() as session:
            # 创建临时CSV文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as tmp:
                tmp_path = tmp.name
                df.to_csv(tmp_path, index=False, encoding='utf-8-sig')
            
            try:
                # 导入数据
                importer = DataImporter(session)
                result = importer.import_reviews(tmp_path)
                
                # 验证：导入记录数应等于DataFrame的行数
                expected_count = len(df)
                assert result.records_count == expected_count, \
                    f"导入记录数 {result.records_count} 不等于文件行数 {expected_count}"
                
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    
    @given(
        num_cols=st.integers(min_value=1, max_value=10),
        num_rows=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_invalid_whitelist_format_handling(self, num_cols, num_rows):
        """
        **Feature: review-result-viewer, Property 6: 无效文件格式处理**
        **Validates: Requirements 3.5**
        
        For any 格式不正确的白名单文件（缺少必需列），系统应返回错误响应而不是崩溃或导入错误数据
        """
        with get_test_db_session() as session:
            # 生成随机列名（不包含必需列）
            invalid_columns = [f'col_{i}' for i in range(num_cols)]
            
            # 确保不包含必需列
            if '门店ID' in invalid_columns:
                invalid_columns.remove('门店ID')
            if '门店名称' in invalid_columns:
                invalid_columns.remove('门店名称')
            
            # 生成随机数据
            data = {col: [f'value_{i}' for i in range(num_rows)] for col in invalid_columns}
            df = pd.DataFrame(data)
            
            # 创建临时Excel文件
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp:
                tmp_path = tmp.name
                df.to_excel(tmp_path, index=False)
            
            try:
                # 导入数据
                importer = DataImporter(session)
                result = importer.import_whitelist(tmp_path)
                
                # 验证：应该返回失败结果，而不是崩溃
                assert result.success is False, "无效格式应该返回失败"
                assert result.records_count == 0, "无效格式不应导入任何记录"
                assert result.error_message is not None, "应该有错误消息"
                assert '格式不正确' in result.error_message or '缺少必需列' in result.error_message, \
                    "错误消息应该说明格式问题"
                
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    
    @given(
        num_cols=st.integers(min_value=1, max_value=10),
        num_rows=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_invalid_reviews_format_handling(self, num_cols, num_rows):
        """
        **Feature: review-result-viewer, Property 6: 无效文件格式处理**
        **Validates: Requirements 3.5**
        
        For any 格式不正确的审核结果文件（缺少必需列），系统应返回错误响应而不是崩溃或导入错误数据
        """
        with get_test_db_session() as session:
            # 生成随机列名（不包含必需列）
            invalid_columns = [f'col_{i}' for i in range(num_cols)]
            
            # 确保不包含必需列
            required_cols = ['门店名称', '门店编号', '检查项名称', '审核结果']
            for col in required_cols:
                if col in invalid_columns:
                    invalid_columns.remove(col)
            
            # 生成随机数据
            data = {col: [f'value_{i}' for i in range(num_rows)] for col in invalid_columns}
            df = pd.DataFrame(data)
            
            # 创建临时CSV文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as tmp:
                tmp_path = tmp.name
                df.to_csv(tmp_path, index=False, encoding='utf-8-sig')
            
            try:
                # 导入数据
                importer = DataImporter(session)
                result = importer.import_reviews(tmp_path)
                
                # 验证：应该返回失败结果，而不是崩溃
                assert result.success is False, "无效格式应该返回失败"
                assert result.records_count == 0, "无效格式不应导入任何记录"
                assert result.error_message is not None, "应该有错误消息"
                assert '格式不正确' in result.error_message or '缺少必需列' in result.error_message, \
                    "错误消息应该说明格式问题"
                
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
