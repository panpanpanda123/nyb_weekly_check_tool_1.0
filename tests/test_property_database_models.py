"""
属性测试：数据库模型 round-trip
Property-Based Tests for Database Models

**Feature: review-result-viewer, Property 4: 数据导入round-trip**
**Validates: Requirements 3.2, 3.3**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database_models import (
    Base, 
    StoreWhitelist, 
    ViewerReviewResult
)


# 使用内存SQLite数据库进行测试
TEST_DATABASE_URL = 'sqlite:///:memory:'

# 创建全局引擎和会话工厂（在模块级别）
_engine = create_engine(TEST_DATABASE_URL, echo=False)
Base.metadata.create_all(_engine)
_Session = sessionmaker(bind=_engine)


@contextmanager
def get_test_session():
    """获取测试数据库会话的上下文管理器"""
    session = _Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# 生成有效的门店ID（非空字符串，最大50字符）
store_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N')),
    min_size=1,
    max_size=20
).filter(lambda x: x.strip() != '')

# 生成有效的名称字符串（可以为空，最大255字符）
name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z')),
    min_size=0,
    max_size=50
)

# 生成有效的短字符串（用于战区、省份、城市等，最大50字符）
short_string_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N')),
    min_size=0,
    max_size=20
)


class TestStoreWhitelistRoundTrip:
    """
    **Feature: review-result-viewer, Property 4: 数据导入round-trip**
    **Validates: Requirements 3.2**
    
    测试白名单数据的round-trip：
    *For any* 有效的白名单数据，导入后从数据库查询应能获取到与原始数据一致的记录。
    """
    
    @given(
        store_id=store_id_strategy,
        province=short_string_strategy,
        city=short_string_strategy,
        store_name=name_strategy,
        war_zone=short_string_strategy,
        store_tag=short_string_strategy,
        city_operator=short_string_strategy
    )
    @settings(max_examples=100)
    def test_whitelist_round_trip(
        self, 
        store_id, 
        province, 
        city, 
        store_name, 
        war_zone, 
        store_tag,
        city_operator
    ):
        """
        属性测试：白名单数据导入后查询应返回一致的数据
        
        **Feature: review-result-viewer, Property 4: 数据导入round-trip**
        **Validates: Requirements 3.2**
        """
        with get_test_session() as session:
            # 清理可能存在的同ID记录
            session.query(StoreWhitelist).filter_by(store_id=store_id).delete()
            session.commit()
            
            # 创建白名单记录
            whitelist = StoreWhitelist(
                store_id=store_id,
                province=province if province else None,
                city=city if city else None,
                store_name=store_name if store_name else None,
                war_zone=war_zone if war_zone else None,
                store_tag=store_tag if store_tag else None,
                city_operator=city_operator if city_operator else None
            )
            
            # 导入到数据库
            session.add(whitelist)
            session.commit()
            
            # 从数据库查询
            retrieved = session.query(StoreWhitelist).filter_by(store_id=store_id).first()
            
            # 验证round-trip一致性
            assert retrieved is not None, "记录应该能被查询到"
            assert retrieved.store_id == store_id
            assert retrieved.province == (province if province else None)
            assert retrieved.city == (city if city else None)
            assert retrieved.store_name == (store_name if store_name else None)
            assert retrieved.war_zone == (war_zone if war_zone else None)
            assert retrieved.store_tag == (store_tag if store_tag else None)
            assert retrieved.city_operator == (city_operator if city_operator else None)
            
            # 清理
            session.delete(retrieved)
            session.commit()


class TestViewerReviewResultRoundTrip:
    """
    **Feature: review-result-viewer, Property 4: 数据导入round-trip**
    **Validates: Requirements 3.3**
    
    测试审核结果数据的round-trip：
    *For any* 有效的审核结果CSV数据，导入后从数据库查询应能获取到与原始数据一致的记录。
    """
    
    @given(
        store_name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip() != ''),
        store_id=store_id_strategy,
        war_zone=short_string_strategy,
        province=short_string_strategy,
        city=short_string_strategy,
        area=name_strategy,
        item_name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip() != ''),
        item_category=short_string_strategy,
        review_result=st.sampled_from(['合格', '不合格']),
        problem_note=name_strategy
    )
    @settings(max_examples=100)
    def test_review_result_round_trip(
        self,
        store_name,
        store_id,
        war_zone,
        province,
        city,
        area,
        item_name,
        item_category,
        review_result,
        problem_note
    ):
        """
        属性测试：审核结果数据导入后查询应返回一致的数据
        
        **Feature: review-result-viewer, Property 4: 数据导入round-trip**
        **Validates: Requirements 3.3**
        """
        with get_test_session() as session:
            # 创建审核结果记录
            review = ViewerReviewResult(
                store_name=store_name,
                store_id=store_id,
                war_zone=war_zone if war_zone else None,
                province=province if province else None,
                city=city if city else None,
                area=area if area else None,
                item_name=item_name,
                item_category=item_category if item_category else None,
                review_result=review_result,
                problem_note=problem_note if problem_note else None
            )
            
            # 导入到数据库
            session.add(review)
            session.commit()
            
            # 获取生成的ID
            review_id = review.id
            
            # 从数据库查询
            retrieved = session.query(ViewerReviewResult).filter_by(id=review_id).first()
            
            # 验证round-trip一致性
            assert retrieved is not None, "记录应该能被查询到"
            assert retrieved.store_name == store_name
            assert retrieved.store_id == store_id
            assert retrieved.war_zone == (war_zone if war_zone else None)
            assert retrieved.province == (province if province else None)
            assert retrieved.city == (city if city else None)
            assert retrieved.area == (area if area else None)
            assert retrieved.item_name == item_name
            assert retrieved.item_category == (item_category if item_category else None)
            assert retrieved.review_result == review_result
            assert retrieved.problem_note == (problem_note if problem_note else None)
            
            # 清理
            session.delete(retrieved)
            session.commit()


class TestToDict:
    """测试 to_dict 方法的round-trip一致性"""
    
    @given(
        store_id=store_id_strategy,
        province=short_string_strategy,
        city=short_string_strategy,
        store_name=name_strategy,
        war_zone=short_string_strategy,
        store_tag=short_string_strategy
    )
    @settings(max_examples=100)
    def test_whitelist_to_dict_contains_all_fields(
        self,
        store_id,
        province,
        city,
        store_name,
        war_zone,
        store_tag
    ):
        """
        属性测试：to_dict方法应包含所有必要字段
        
        **Feature: review-result-viewer, Property 4: 数据导入round-trip**
        **Validates: Requirements 3.2**
        """
        whitelist = StoreWhitelist(
            store_id=store_id,
            province=province if province else None,
            city=city if city else None,
            store_name=store_name if store_name else None,
            war_zone=war_zone if war_zone else None,
            store_tag=store_tag if store_tag else None
        )
        
        result = whitelist.to_dict()
        
        # 验证所有必要字段都存在
        assert 'store_id' in result
        assert 'province' in result
        assert 'city' in result
        assert 'store_name' in result
        assert 'war_zone' in result
        assert 'store_tag' in result
        
        # 验证值一致性
        assert result['store_id'] == store_id
        assert result['province'] == (province if province else None)
        assert result['city'] == (city if city else None)
        assert result['store_name'] == (store_name if store_name else None)
        assert result['war_zone'] == (war_zone if war_zone else None)
        assert result['store_tag'] == (store_tag if store_tag else None)
