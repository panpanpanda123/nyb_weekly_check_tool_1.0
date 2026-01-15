"""
展示系统Flask应用属性测试
Property-Based Tests for Viewer Flask Application
"""
import pytest
from contextlib import contextmanager
from hypothesis import given, strategies as st, settings, assume
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
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


# 生成器：生成白名单数据
@st.composite
def whitelist_records(draw):
    """生成白名单测试数据"""
    num_records = draw(st.integers(min_value=1, max_value=30))
    
    # 生成唯一的门店ID列表
    store_ids = draw(st.lists(
        st.integers(min_value=1000, max_value=99999),
        min_size=num_records,
        max_size=num_records,
        unique=True
    ))
    
    # 定义战区-省份-城市的层级关系
    hierarchy = {
        '华东': {
            '浙江': ['杭州', '宁波', '温州'],
            '江苏': ['南京', '苏州', '无锡'],
            '上海': ['上海']
        },
        '华南': {
            '广东': ['广州', '深圳', '东莞'],
            '福建': ['福州', '厦门']
        },
        '华北': {
            '北京': ['北京'],
            '河北': ['石家庄', '唐山']
        }
    }
    
    records = []
    for store_id in store_ids:
        # 随机选择战区
        war_zone = draw(st.sampled_from(list(hierarchy.keys())))
        # 根据战区选择省份
        province = draw(st.sampled_from(list(hierarchy[war_zone].keys())))
        # 根据省份选择城市
        city = draw(st.sampled_from(hierarchy[war_zone][province]))
        
        record = StoreWhitelist(
            store_id=str(store_id),
            store_name=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L',)))),
            war_zone=war_zone,
            province=province,
            city=city,
            store_tag=draw(st.sampled_from(['A类', 'B类', 'C类', 'D类'])),
            city_operator=draw(st.text(min_size=0, max_size=10, alphabet=st.characters(whitelist_categories=('L',))))
        )
        records.append(record)
    
    return records


# 生成器：生成审核结果数据
@st.composite
def review_records(draw, whitelist_data):
    """基于白名单生成审核结果测试数据"""
    if not whitelist_data:
        return []
    
    num_records = draw(st.integers(min_value=1, max_value=min(50, len(whitelist_data) * 3)))
    
    records = []
    for i in range(num_records):
        # 从白名单中随机选择一个门店
        store = draw(st.sampled_from(whitelist_data))
        
        record = ViewerReviewResult(
            store_name=store.store_name,
            store_id=store.store_id,
            war_zone=store.war_zone,
            province=store.province,
            city=store.city,
            area=draw(st.text(min_size=0, max_size=20, alphabet=st.characters(whitelist_categories=('L',)))),
            item_name=draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L',)))),
            item_category=draw(st.sampled_from(['卫生', '陈列', '设备', '服务'])),
            image_url=draw(st.text(min_size=0, max_size=50)),
            review_result=draw(st.sampled_from(['合格', '不合格'])),
            problem_note=draw(st.text(min_size=0, max_size=50, alphabet=st.characters(whitelist_categories=('L',))))
        )
        records.append(record)
    
    return records


class TestAppViewerProperties:
    """展示系统Flask应用属性测试"""
    
    @given(whitelist_data=whitelist_records())
    @settings(max_examples=100, deadline=None)
    def test_property_cascading_filter_consistency(self, whitelist_data):
        """
        **Feature: review-result-viewer, Property 1: 级联筛选一致性**
        **Validates: Requirements 1.2, 1.3**
        
        For any 战区选择，返回的省份列表中的每个省份都应属于该战区；
        For any 省份选择，返回的城市列表中的每个城市都应属于该省份。
        
        注意：此测试验证API返回的数据与数据库中实际存在的数据一致，
        而不是验证数据本身的层级关系是否合理。
        """
        with get_test_app_and_session() as (client, session):
            # 插入白名单数据
            for record in whitelist_data:
                session.add(record)
            session.commit()
            
            # 获取所有战区
            response = client.get('/api/filters')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            
            war_zones = data['data']['war_zones']
            
            # 对每个战区，验证其省份列表的一致性
            for war_zone in war_zones:
                # 获取该战区的省份列表（通过API）
                response = client.get(f'/api/filters/provinces?war_zone={war_zone}')
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                
                api_provinces = set(data['data']['provinces'])
                
                # 从数据库直接查询该战区的省份（作为真实数据源）
                db_provinces = set([p[0] for p in session.query(StoreWhitelist.province)\
                    .filter(StoreWhitelist.war_zone == war_zone)\
                    .filter(StoreWhitelist.province.isnot(None))\
                    .filter(StoreWhitelist.province != '')\
                    .distinct()\
                    .all()])
                
                # 验证：API返回的省份应该与数据库中的一致
                assert api_provinces == db_provinces, \
                    f"战区 '{war_zone}' 的API省份列表与数据库不一致。API: {api_provinces}, DB: {db_provinces}"
            
            # 获取所有省份
            all_provinces = session.query(StoreWhitelist.province)\
                .filter(StoreWhitelist.province.isnot(None))\
                .filter(StoreWhitelist.province != '')\
                .distinct()\
                .all()
            
            # 对每个省份，验证其城市列表的一致性
            for (province,) in all_provinces:
                # 获取该省份的城市列表（通过API）
                response = client.get(f'/api/filters/cities?province={province}')
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                
                api_cities = set(data['data']['cities'])
                
                # 从数据库直接查询该省份的城市（作为真实数据源）
                db_cities = set([c[0] for c in session.query(StoreWhitelist.city)\
                    .filter(StoreWhitelist.province == province)\
                    .filter(StoreWhitelist.city.isnot(None))\
                    .filter(StoreWhitelist.city != '')\
                    .distinct()\
                    .all()])
                
                # 验证：API返回的城市应该与数据库中的一致
                assert api_cities == db_cities, \
                    f"省份 '{province}' 的API城市列表与数据库不一致。API: {api_cities}, DB: {db_cities}"
    
    @given(
        whitelist_data=whitelist_records(),
        data=st.data()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_search_filter_correctness(self, whitelist_data, data):
        """
        **Feature: review-result-viewer, Property 2: 搜索结果筛选正确性**
        **Validates: Requirements 1.4**
        
        For any 筛选条件组合（战区、省份、城市、门店标签、是否合格），
        返回的每条审核结果都应满足所有指定的筛选条件。
        """
        with get_test_app_and_session() as (client, session):
            # 插入白名单数据
            for record in whitelist_data:
                session.add(record)
            session.commit()
            
            # 生成审核结果数据
            review_data = data.draw(review_records(whitelist_data))
            assume(len(review_data) > 0)
            
            for record in review_data:
                session.add(record)
            session.commit()
            
            # 获取可用的筛选选项
            response = client.get('/api/filters')
            assert response.status_code == 200
            filter_data = response.get_json()['data']
            
            # 随机选择筛选条件
            filters = {}
            
            # 可能选择战区
            if filter_data['war_zones'] and data.draw(st.booleans()):
                filters['war_zone'] = data.draw(st.sampled_from(filter_data['war_zones']))
            
            # 可能选择省份
            if filter_data['provinces'] and data.draw(st.booleans()):
                filters['province'] = data.draw(st.sampled_from(filter_data['provinces']))
            
            # 可能选择城市
            if filter_data['cities'] and data.draw(st.booleans()):
                filters['city'] = data.draw(st.sampled_from(filter_data['cities']))
            
            # 可能选择门店标签
            if filter_data['store_tags'] and data.draw(st.booleans()):
                filters['store_tag'] = data.draw(st.sampled_from(filter_data['store_tags']))
            
            # 可能选择审核结果
            if data.draw(st.booleans()):
                filters['review_result'] = data.draw(st.sampled_from(['合格', '不合格']))
            
            # 执行搜索
            response = client.get('/api/search', query_string=filters)
            assert response.status_code == 200
            result = response.get_json()
            assert result['success'] is True
            
            results = result['data']['results']
            
            # 验证：每条结果都应满足所有筛选条件
            for item in results:
                if 'war_zone' in filters:
                    assert item['war_zone'] == filters['war_zone'], \
                        f"结果的战区 '{item['war_zone']}' 不匹配筛选条件 '{filters['war_zone']}'"
                
                if 'province' in filters:
                    assert item['province'] == filters['province'], \
                        f"结果的省份 '{item['province']}' 不匹配筛选条件 '{filters['province']}'"
                
                if 'city' in filters:
                    assert item['city'] == filters['city'], \
                        f"结果的城市 '{item['city']}' 不匹配筛选条件 '{filters['city']}'"
                
                if 'review_result' in filters:
                    assert item['review_result'] == filters['review_result'], \
                        f"结果的审核结果 '{item['review_result']}' 不匹配筛选条件 '{filters['review_result']}'"
                
                # 验证门店标签（需要从白名单查询）
                if 'store_tag' in filters:
                    store = session.query(StoreWhitelist)\
                        .filter(StoreWhitelist.store_id == item['store_id'])\
                        .first()
                    if store:
                        assert store.store_tag == filters['store_tag'], \
                            f"结果的门店标签 '{store.store_tag}' 不匹配筛选条件 '{filters['store_tag']}'"
    
    @given(
        whitelist_data=whitelist_records(),
        data=st.data()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_search_result_field_completeness(self, whitelist_data, data):
        """
        **Feature: review-result-viewer, Property 3: 搜索结果字段完整性**
        **Validates: Requirements 2.1**
        
        For any 搜索结果中的检查项，渲染后的内容应包含门店名称、检查项名称、
        图片URL、审核结果、问题描述（如果不合格）。
        """
        with get_test_app_and_session() as (client, session):
            # 插入白名单数据
            for record in whitelist_data:
                session.add(record)
            session.commit()
            
            # 生成审核结果数据
            review_data = data.draw(review_records(whitelist_data))
            assume(len(review_data) > 0)
            
            for record in review_data:
                session.add(record)
            session.commit()
            
            # 执行搜索（不带筛选条件，获取所有结果）
            response = client.get('/api/search')
            assert response.status_code == 200
            result = response.get_json()
            assert result['success'] is True
            
            results = result['data']['results']
            
            # 验证：每条结果都应包含必需字段
            for item in results:
                # 必需字段
                assert 'store_name' in item, "缺少门店名称字段"
                assert 'item_name' in item, "缺少检查项名称字段"
                assert 'image_url' in item, "缺少图片URL字段"
                assert 'review_result' in item, "缺少审核结果字段"
                
                # 验证字段不为None
                assert item['store_name'] is not None, "门店名称不应为None"
                assert item['item_name'] is not None, "检查项名称不应为None"
                assert item['review_result'] is not None, "审核结果不应为None"
                
                # 如果不合格，应该有问题描述字段
                if item['review_result'] == '不合格':
                    assert 'problem_note' in item, "不合格结果应包含问题描述字段"
