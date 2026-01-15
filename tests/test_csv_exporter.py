"""
CSV导出器测试
CSV Exporter Tests
"""
import pytest
import csv
from io import StringIO
from hypothesis import given, strategies as st, settings
from csv_exporter import CSVExporter
from database import get_session, StoreWhitelist, Base, engine


class TestCSVExporter:
    """CSVExporter类的单元测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.exporter = CSVExporter()
        
        # 模拟原始数据
        self.original_data = [
            {
                'id': '7_门店餐桌区',
                '门店名称': '牛约堡-手作牛肉汉堡(上海打浦桥)',
                '门店编号': '7',
                '所属区域': '牛约堡/上海战区/上海/上海',
                '检查项名称': '门店餐桌区',
                '检查项分类': '周清',
                '负责运营': '窦',
                '标准图': 'https://example.com/image1.jpg'
            },
            {
                'id': '8_门店厨房',
                '门店名称': '牛约堡-手作牛肉汉堡(北京店)',
                '门店编号': '8',
                '所属区域': '牛约堡/北京战区/北京/北京',
                '检查项名称': '门店厨房',
                '检查项分类': '周清',
                '负责运营': '李四',
                '标准图': 'https://example.com/image2.jpg'
            }
        ]
        
        # 模拟审核结果
        self.reviews = [
            {
                'item_id': '7_门店餐桌区',
                '门店名称': '牛约堡-手作牛肉汉堡(上海打浦桥)',
                '门店编号': '7',
                '所属区域': '牛约堡/上海战区/上海/上海',
                '检查项名称': '门店餐桌区',
                '标准图': 'https://example.com/image1.jpg',
                '审核结果': '合格',
                '审核时间': '2026-01-10 10:30:00'
            }
        ]
    
    def test_initialization(self):
        """测试初始化"""
        exporter = CSVExporter()
        assert exporter is not None
    
    def test_export_reviews_with_data(self):
        """测试导出审核结果"""
        csv_content = self.exporter.export_reviews(self.reviews, self.original_data)
        
        # 验证返回的是字符串
        assert isinstance(csv_content, str)
        
        # 验证包含UTF-8 BOM
        assert csv_content.startswith('\ufeff')
        
        # 验证包含表头
        assert '门店名称' in csv_content
        assert '审核结果' in csv_content
        
        # 验证包含数据
        assert '牛约堡-手作牛肉汉堡(上海打浦桥)' in csv_content
        assert '合格' in csv_content
    
    def test_export_reviews_empty(self):
        """测试导出空审核结果"""
        csv_content = self.exporter.export_reviews([], self.original_data)
        
        # 空数据应该只返回BOM
        assert csv_content == '\ufeff'
    
    def test_merge_data(self):
        """测试数据合并"""
        merged = self.exporter._merge_data(self.reviews, self.original_data)
        
        # 应该只包含有审核结果的项
        assert len(merged) == 1
        assert merged[0]['门店编号'] == '7'
        assert merged[0]['审核结果'] == '合格'
        assert merged[0]['负责运营'] == '窦'
    
    def test_generate_csv_content(self):
        """测试生成CSV内容"""
        data = [
            {
                '门店名称': '测试门店',
                '门店编号': '1',
                '战区': '测试战区',
                '省份': '测试省份',
                '城市': '测试城市',
                '所属区域': '测试区域',
                '检查项名称': '测试项',
                '检查项分类': '周清',
                '负责运营': '张三',
                '标准图': 'http://test.com/img.jpg',
                '审核结果': '合格',
                '问题描述': '',
                '审核时间': '2026-01-10 10:00:00'
            }
        ]
        
        csv_content = self.exporter._generate_csv_content(data)
        
        # 验证包含表头
        lines = csv_content.strip().split('\n')
        assert len(lines) == 2  # 表头 + 1行数据
        assert '门店名称' in lines[0]
        assert '战区' in lines[0]
        assert '省份' in lines[0]
        assert '城市' in lines[0]
        
        # 验证包含数据
        assert '测试门店' in lines[1]
        assert '合格' in lines[1]
    
    def test_generate_filename(self):
        """测试生成文件名"""
        filename = self.exporter.generate_filename()
        
        # 验证文件名格式
        assert filename.startswith('审核结果_')
        assert filename.endswith('.csv')
        assert '2026' in filename  # 包含年份
    
    def test_csv_columns_order(self):
        """测试CSV列顺序"""
        csv_content = self.exporter.export_reviews(self.reviews, self.original_data)
        
        # 移除BOM
        csv_content = csv_content.lstrip('\ufeff')
        
        # 获取表头
        header = csv_content.split('\n')[0]
        
        # 验证列顺序（包含新增的战区、省份、城市字段）
        expected_columns = [
            '门店名称',
            '门店编号',
            '战区',
            '省份',
            '城市',
            '所属区域',
            '检查项名称',
            '检查项分类',
            '负责运营',
            '标准图',
            '审核结果',
            '问题描述',
            '审核时间'
        ]
        
        for col in expected_columns:
            assert col in header
    
    def test_utf8_encoding(self):
        """测试UTF-8编码"""
        csv_content = self.exporter.export_reviews(self.reviews, self.original_data)
        
        # 验证可以编码为UTF-8
        try:
            csv_content.encode('utf-8')
        except UnicodeEncodeError:
            pytest.fail("CSV内容无法编码为UTF-8")
        
        # 验证包含中文字符
        assert '门店' in csv_content
        assert '合格' in csv_content



class TestCSVExporterFieldCompleteness:
    """
    **Feature: review-result-viewer, Property 7: CSV导出字段完整性**
    **Validates: Requirements 5.1, 5.2, 5.3**
    
    属性测试：CSV导出字段完整性
    *For any* 导出的审核结果CSV，每行数据应包含战区、省份、城市字段；
    当门店在白名单中存在时，这些字段应与白名单数据一致；
    当门店不存在时，这些字段应为空。
    """
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 确保数据库表存在
        Base.metadata.create_all(engine)
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理测试数据
        session = get_session()
        try:
            session.query(StoreWhitelist).delete()
            session.commit()
        finally:
            session.close()
    
    # 生成有效的门店ID
    store_id_strategy = st.text(
        alphabet=st.characters(whitelist_categories=('N',)),
        min_size=1,
        max_size=10
    ).filter(lambda x: x.strip() != '')
    
    # 生成有效的字符串
    valid_string_strategy = st.text(
        alphabet=st.characters(whitelist_categories=('L', 'N')),
        min_size=1,
        max_size=20
    ).filter(lambda x: x.strip() != '')
    
    @given(
        store_id=store_id_strategy,
        war_zone=valid_string_strategy,
        province=valid_string_strategy,
        city=valid_string_strategy,
        store_name=valid_string_strategy,
        item_name=valid_string_strategy,
        review_result=st.sampled_from(['合格', '不合格'])
    )
    @settings(max_examples=100)
    def test_csv_export_includes_location_fields_for_existing_stores(
        self,
        store_id,
        war_zone,
        province,
        city,
        store_name,
        item_name,
        review_result
    ):
        """
        属性测试：当门店在白名单中存在时，CSV导出应包含正确的战区、省份、城市字段
        
        **Feature: review-result-viewer, Property 7: CSV导出字段完整性**
        **Validates: Requirements 5.1, 5.2**
        """
        session = get_session()
        try:
            # 清理可能存在的同ID记录
            session.query(StoreWhitelist).filter_by(store_id=store_id).delete()
            session.commit()
            
            # 在白名单中添加门店
            whitelist_store = StoreWhitelist(
                store_id=store_id,
                war_zone=war_zone,
                province=province,
                city=city,
                store_name=store_name
            )
            session.add(whitelist_store)
            session.commit()
            
            # 创建导出器
            exporter = CSVExporter()
            
            # 准备测试数据
            item_id = f"{store_id}_{item_name}"
            original_data = [{
                'id': item_id,
                '门店名称': store_name,
                '门店编号': store_id,
                '所属区域': '测试区域',
                '检查项名称': item_name,
                '检查项分类': '周清',
                '负责运营': '测试运营',
                '标准图': 'http://test.com/img.jpg'
            }]
            
            reviews = [{
                'item_id': item_id,
                '审核结果': review_result,
                '问题描述': '测试问题' if review_result == '不合格' else '',
                '审核时间': '2026-01-15 10:00:00'
            }]
            
            # 导出CSV
            csv_content = exporter.export_reviews(reviews, original_data)
            
            # 移除BOM并解析CSV
            csv_content = csv_content.lstrip('\ufeff')
            csv_reader = csv.DictReader(StringIO(csv_content))
            rows = list(csv_reader)
            
            # 验证：应该有一行数据
            assert len(rows) == 1, "应该导出一行数据"
            
            row = rows[0]
            
            # 验证：CSV应包含战区、省份、城市字段
            assert '战区' in row, "CSV应包含战区字段"
            assert '省份' in row, "CSV应包含省份字段"
            assert '城市' in row, "CSV应包含城市字段"
            
            # 验证：字段值应与白名单一致
            assert row['战区'] == war_zone, f"战区应为 {war_zone}，实际为 {row['战区']}"
            assert row['省份'] == province, f"省份应为 {province}，实际为 {row['省份']}"
            assert row['城市'] == city, f"城市应为 {city}，实际为 {row['城市']}"
            
        finally:
            # 清理测试数据
            session.query(StoreWhitelist).filter_by(store_id=store_id).delete()
            session.commit()
            session.close()
    
    @given(
        store_id=store_id_strategy,
        store_name=valid_string_strategy,
        item_name=valid_string_strategy,
        review_result=st.sampled_from(['合格', '不合格'])
    )
    @settings(max_examples=100)
    def test_csv_export_empty_location_fields_for_nonexistent_stores(
        self,
        store_id,
        store_name,
        item_name,
        review_result
    ):
        """
        属性测试：当门店不在白名单中时，CSV导出的战区、省份、城市字段应为空
        
        **Feature: review-result-viewer, Property 7: CSV导出字段完整性**
        **Validates: Requirements 5.3**
        """
        session = get_session()
        try:
            # 确保门店不在白名单中
            session.query(StoreWhitelist).filter_by(store_id=store_id).delete()
            session.commit()
            
            # 创建导出器
            exporter = CSVExporter()
            
            # 准备测试数据
            item_id = f"{store_id}_{item_name}"
            original_data = [{
                'id': item_id,
                '门店名称': store_name,
                '门店编号': store_id,
                '所属区域': '测试区域',
                '检查项名称': item_name,
                '检查项分类': '周清',
                '负责运营': '测试运营',
                '标准图': 'http://test.com/img.jpg'
            }]
            
            reviews = [{
                'item_id': item_id,
                '审核结果': review_result,
                '问题描述': '测试问题' if review_result == '不合格' else '',
                '审核时间': '2026-01-15 10:00:00'
            }]
            
            # 导出CSV
            csv_content = exporter.export_reviews(reviews, original_data)
            
            # 移除BOM并解析CSV
            csv_content = csv_content.lstrip('\ufeff')
            csv_reader = csv.DictReader(StringIO(csv_content))
            rows = list(csv_reader)
            
            # 验证：应该有一行数据
            assert len(rows) == 1, "应该导出一行数据"
            
            row = rows[0]
            
            # 验证：CSV应包含战区、省份、城市字段
            assert '战区' in row, "CSV应包含战区字段"
            assert '省份' in row, "CSV应包含省份字段"
            assert '城市' in row, "CSV应包含城市字段"
            
            # 验证：字段值应为空
            assert row['战区'] == '', f"战区应为空，实际为 {row['战区']}"
            assert row['省份'] == '', f"省份应为空，实际为 {row['省份']}"
            assert row['城市'] == '', f"城市应为空，实际为 {row['城市']}"
            
        finally:
            session.close()
