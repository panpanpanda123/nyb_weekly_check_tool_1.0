"""
审核数据管理器测试
Review Manager Tests
"""
import pytest
from review_manager import ReviewManager
from datetime import datetime


class TestReviewManager:
    """ReviewManager类的单元测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.manager = ReviewManager()
        self.sample_review_data = {
            '门店名称': '牛约堡-手作牛肉汉堡(上海打浦桥)',
            '门店编号': '7',
            '所属区域': '牛约堡/上海战区/上海/上海',
            '检查项名称': '门店餐桌区',
            '标准图': 'https://example.com/image.jpg',
            '审核结果': '合格'
        }
    
    def test_save_review_success(self):
        """测试成功保存审核结果"""
        item_id = '7_门店餐桌区'
        result = self.manager.save_review(item_id, self.sample_review_data)
        
        assert result is True
        assert self.manager.has_review(item_id)
        assert self.manager.get_review_count() == 1
    
    def test_save_review_stores_all_fields(self):
        """测试保存的审核结果包含所有必需字段"""
        item_id = '7_门店餐桌区'
        self.manager.save_review(item_id, self.sample_review_data)
        
        review = self.manager.get_review(item_id)
        
        assert review is not None
        assert review['item_id'] == item_id
        assert review['门店名称'] == '牛约堡-手作牛肉汉堡(上海打浦桥)'
        assert review['门店编号'] == '7'
        assert review['所属区域'] == '牛约堡/上海战区/上海/上海'
        assert review['检查项名称'] == '门店餐桌区'
        assert review['标准图'] == 'https://example.com/image.jpg'
        assert review['审核结果'] == '合格'
        assert '审核时间' in review
    
    def test_save_review_generates_timestamp(self):
        """测试保存审核结果时生成时间戳"""
        item_id = '7_门店餐桌区'
        self.manager.save_review(item_id, self.sample_review_data)
        
        review = self.manager.get_review(item_id)
        timestamp = review['审核时间']
        
        # 验证时间戳格式
        assert timestamp is not None
        datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    
    def test_get_review_nonexistent(self):
        """测试获取不存在的审核结果"""
        result = self.manager.get_review('nonexistent_id')
        assert result is None
    
    def test_update_review_existing(self):
        """测试更新现有审核结果"""
        item_id = '7_门店餐桌区'
        
        # 先保存一个审核结果
        self.manager.save_review(item_id, self.sample_review_data)
        original_review = self.manager.get_review(item_id)
        
        # 更新审核结果
        updated_data = self.sample_review_data.copy()
        updated_data['审核结果'] = '不合格'
        
        result = self.manager.update_review(item_id, updated_data)
        
        assert result is True
        updated_review = self.manager.get_review(item_id)
        assert updated_review['审核结果'] == '不合格'
        # 验证时间戳存在且格式正确（时间戳可能相同因为操作很快）
        assert '审核时间' in updated_review
        datetime.strptime(updated_review['审核时间'], '%Y-%m-%d %H:%M:%S')
    
    def test_update_review_nonexistent_creates_new(self):
        """测试更新不存在的审核结果会创建新记录"""
        item_id = '8_新检查项'
        
        result = self.manager.update_review(item_id, self.sample_review_data)
        
        assert result is True
        assert self.manager.has_review(item_id)
        assert self.manager.get_review_count() == 1
    
    def test_get_all_reviews_empty(self):
        """测试获取空的审核结果列表"""
        reviews = self.manager.get_all_reviews()
        assert reviews == []
    
    def test_get_all_reviews_multiple(self):
        """测试获取多个审核结果"""
        # 保存多个审核结果
        for i in range(3):
            item_id = f'{i}_检查项{i}'
            data = self.sample_review_data.copy()
            data['门店编号'] = str(i)
            self.manager.save_review(item_id, data)
        
        reviews = self.manager.get_all_reviews()
        
        assert len(reviews) == 3
        assert all(isinstance(review, dict) for review in reviews)
    
    def test_has_review(self):
        """测试检查审核结果是否存在"""
        item_id = '7_门店餐桌区'
        
        assert not self.manager.has_review(item_id)
        
        self.manager.save_review(item_id, self.sample_review_data)
        
        assert self.manager.has_review(item_id)
    
    def test_get_review_count(self):
        """测试获取审核结果数量"""
        assert self.manager.get_review_count() == 0
        
        self.manager.save_review('1_item1', self.sample_review_data)
        assert self.manager.get_review_count() == 1
        
        self.manager.save_review('2_item2', self.sample_review_data)
        assert self.manager.get_review_count() == 2
    
    def test_multiple_reviews_different_items(self):
        """测试保存多个不同检查项的审核结果"""
        items = [
            ('7_门店餐桌区', '合格'),
            ('8_门店厨房', '不合格'),
            ('9_门店卫生间', '合格')
        ]
        
        for item_id, result in items:
            data = self.sample_review_data.copy()
            data['审核结果'] = result
            self.manager.save_review(item_id, data)
        
        assert self.manager.get_review_count() == 3
        
        # 验证每个审核结果都正确保存
        for item_id, expected_result in items:
            review = self.manager.get_review(item_id)
            assert review['审核结果'] == expected_result
    
    def test_idempotent_save_same_item(self):
        """测试对同一检查项多次保存会覆盖（幂等性）"""
        item_id = '7_门店餐桌区'
        
        # 第一次保存
        self.manager.save_review(item_id, self.sample_review_data)
        
        # 第二次保存相同ID
        updated_data = self.sample_review_data.copy()
        updated_data['审核结果'] = '不合格'
        self.manager.save_review(item_id, updated_data)
        
        # 应该只有一条记录
        assert self.manager.get_review_count() == 1
        
        # 应该是最新的结果
        review = self.manager.get_review(item_id)
        assert review['审核结果'] == '不合格'
