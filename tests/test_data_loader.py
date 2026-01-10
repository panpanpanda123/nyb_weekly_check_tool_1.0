"""
数据加载模块测试
"""
import pytest
import pandas as pd
from data_loader import DataLoader


def test_data_loader_initialization():
    """测试DataLoader初始化"""
    loader = DataLoader('test.xlsx')
    assert loader.file_path == 'test.xlsx'
    assert loader.df is None
    assert loader.data == []
    assert loader.whitelist_loader is None


def test_data_loader_with_whitelist():
    """测试DataLoader带白名单初始化"""
    loader = DataLoader('test.xlsx', 'whitelist.xlsx')
    assert loader.file_path == 'test.xlsx'
    assert loader.whitelist_path == 'whitelist.xlsx'
    assert loader.whitelist_loader is not None


def test_load_excel_file_not_found():
    """测试加载不存在的文件"""
    loader = DataLoader('nonexistent.xlsx')
    with pytest.raises(FileNotFoundError) as exc_info:
        loader.load_excel()
    assert 'Excel文件不存在' in str(exc_info.value)


def test_validate_data_before_load():
    """测试在加载前验证数据"""
    loader = DataLoader('test.xlsx')
    with pytest.raises(ValueError) as exc_info:
        loader.validate_data()
    assert '数据未加载' in str(exc_info.value)


def test_transform_data_before_load():
    """测试在加载前转换数据"""
    loader = DataLoader('test.xlsx')
    with pytest.raises(ValueError) as exc_info:
        loader.transform_data()
    assert '数据未加载' in str(exc_info.value)


def test_load_real_excel_file():
    """测试加载真实的Excel文件"""
    loader = DataLoader('检查项记录-2026-01-08 1835_321a686696bb498b83a1d0ce09323991.xlsx')
    df = loader.load_excel()
    assert df is not None
    assert len(df) > 0


def test_validate_real_data():
    """测试验证真实数据"""
    loader = DataLoader('检查项记录-2026-01-08 1835_321a686696bb498b83a1d0ce09323991.xlsx')
    loader.load_excel()
    assert loader.validate_data() is True


def test_transform_real_data():
    """测试转换真实数据"""
    loader = DataLoader('检查项记录-2026-01-08 1835_321a686696bb498b83a1d0ce09323991.xlsx')
    loader.load_excel()
    loader.validate_data()
    data = loader.transform_data()
    
    assert len(data) > 0
    # 检查第一条数据的结构
    first_item = data[0]
    assert 'id' in first_item
    assert '检查项名称' in first_item
    assert '门店名称' in first_item
    assert '门店编号' in first_item
    assert '所属区域' in first_item
    assert '标准图' in first_item


def test_unique_id_generation():
    """测试唯一ID生成"""
    loader = DataLoader('检查项记录-2026-01-08 1835_321a686696bb498b83a1d0ce09323991.xlsx')
    data = loader.load_and_process()
    
    # 检查ID格式: 门店编号_检查项名称
    first_item = data[0]
    assert '_' in first_item['id']
    parts = first_item['id'].split('_', 1)
    assert parts[0] == first_item['门店编号']
    assert parts[1] == first_item['检查项名称']


def test_load_and_process():
    """测试一次性加载和处理"""
    loader = DataLoader('检查项记录-2026-01-08 1835_321a686696bb498b83a1d0ce09323991.xlsx')
    data = loader.load_and_process()
    
    assert len(data) > 0
    assert loader.df is not None
    assert loader.data == data


def test_get_data():
    """测试获取数据"""
    loader = DataLoader('检查项记录-2026-01-08 1835_321a686696bb498b83a1d0ce09323991.xlsx')
    loader.load_and_process()
    
    data = loader.get_data()
    assert len(data) > 0
    assert data == loader.data
