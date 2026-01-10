"""
白名单加载器测试
Whitelist Loader Tests
"""
import pytest
import pandas as pd
from whitelist_loader import WhitelistLoader
import os


class TestWhitelistLoader:
    """WhitelistLoader类的单元测试"""
    
    def test_initialization(self):
        """测试初始化"""
        loader = WhitelistLoader('test_whitelist.xlsx')
        assert loader.file_path == 'test_whitelist.xlsx'
        assert loader.df is None
        assert loader.operator_mapping == {}
    
    def test_load_real_whitelist(self):
        """测试加载真实白名单文件"""
        file_path = 'D:/pythonproject/Newyobo_operat_database/daily_data/whitelist/whitelist.xlsx'
        
        if not os.path.exists(file_path):
            pytest.skip("白名单文件不存在，跳过测试")
        
        loader = WhitelistLoader(file_path)
        result = loader.load_whitelist()
        
        assert result is True
        assert loader.df is not None
        assert len(loader.df) > 0
        assert len(loader.operator_mapping) > 0
    
    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        loader = WhitelistLoader('nonexistent_file.xlsx')
        result = loader.load_whitelist()
        
        # 应该返回False但不抛出异常
        assert result is False
        assert loader.df is None
        assert loader.operator_mapping == {}
    
    def test_operator_priority(self):
        """测试运营人员分配优先级（临时运营 > 省市运营）"""
        # 创建测试数据
        test_data = pd.DataFrame({
            '门店ID': [1, 2, 3, 4],
            '省市运营': ['张三', '李四', '王五', None],
            '临时运营': ['赵六', None, None, None]
        })
        
        loader = WhitelistLoader('test.xlsx')
        loader.df = test_data
        loader._generate_operator_mapping()
        
        # 门店1有临时运营，应该分配给临时运营
        assert loader.assign_operator('1') == '赵六'
        
        # 门店2没有临时运营，应该分配给省市运营
        assert loader.assign_operator('2') == '李四'
        
        # 门店3没有临时运营，应该分配给省市运营
        assert loader.assign_operator('3') == '王五'
        
        # 门店4两者都没有，应该显示未分配
        assert loader.assign_operator('4') == '未分配'
    
    def test_assign_operator_not_found(self):
        """测试分配不存在的门店"""
        loader = WhitelistLoader('test.xlsx')
        loader.operator_mapping = {'1': '张三', '2': '李四'}
        
        # 不存在的门店应该返回"未分配"
        assert loader.assign_operator('999') == '未分配'
    
    def test_get_all_operators(self):
        """测试获取所有运营人员列表"""
        loader = WhitelistLoader('test.xlsx')
        loader.operator_mapping = {
            '1': '张三',
            '2': '李四',
            '3': '张三',  # 重复
            '4': '王五',
            '5': '未分配'
        }
        
        operators = loader.get_all_operators()
        
        # 应该去重且排序，不包含"未分配"
        assert operators == ['张三', '李四', '王五']
    
    def test_get_stores_by_operator(self):
        """测试获取指定运营人员负责的门店"""
        loader = WhitelistLoader('test.xlsx')
        loader.operator_mapping = {
            '1': '张三',
            '2': '李四',
            '3': '张三',
            '4': '王五'
        }
        
        # 张三负责门店1和3
        stores = loader.get_stores_by_operator('张三')
        assert set(stores) == {'1', '3'}
        
        # 李四负责门店2
        stores = loader.get_stores_by_operator('李四')
        assert stores == ['2']
        
        # 不存在的运营人员
        stores = loader.get_stores_by_operator('不存在')
        assert stores == []
    
    def test_real_whitelist_data_structure(self):
        """测试真实白名单文件的数据结构"""
        file_path = 'D:/pythonproject/Newyobo_operat_database/daily_data/whitelist/whitelist.xlsx'
        
        if not os.path.exists(file_path):
            pytest.skip("白名单文件不存在，跳过测试")
        
        loader = WhitelistLoader(file_path)
        loader.load_whitelist()
        
        # 验证必需字段存在
        assert '门店ID' in loader.df.columns
        assert '省市运营' in loader.df.columns
        assert '临时运营' in loader.df.columns
        
        # 验证至少有一些运营人员
        operators = loader.get_all_operators()
        assert len(operators) > 0
        
        # 验证映射关系
        assert len(loader.operator_mapping) > 0
        
        # 打印一些统计信息
        print(f"\n白名单统计:")
        print(f"  总门店数: {len(loader.df)}")
        print(f"  运营人员数: {len(operators)}")
        print(f"  运营人员列表: {operators}")
