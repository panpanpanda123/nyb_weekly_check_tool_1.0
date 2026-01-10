"""
基本应用测试
"""
import pytest
from app import app


@pytest.fixture
def client():
    """创建测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    """测试主页路由"""
    response = client.get('/')
    assert response.status_code == 200


def test_api_items_route(client):
    """测试获取检查项API"""
    response = client.get('/api/items')
    assert response.status_code == 200
    assert response.is_json


def test_api_reviews_route(client):
    """测试获取审核结果API"""
    response = client.get('/api/reviews')
    assert response.status_code == 200
    assert response.is_json


def test_api_review_post(client):
    """测试提交审核结果API"""
    # 首先获取一个有效的item_id
    items_response = client.get('/api/items')
    items = items_response.get_json()
    
    if items and len(items) > 0:
        # 使用第一个检查项的ID
        item_id = items[0]['id']
        response = client.post('/api/review', 
                              json={'item_id': item_id, '审核结果': '合格'})
        assert response.status_code == 200
        assert response.is_json
        data = response.get_json()
        assert data['success'] is True
    else:
        # 如果没有数据，测试应该返回404
        response = client.post('/api/review', 
                              json={'item_id': 'nonexistent', '审核结果': '合格'})
        assert response.status_code == 404
