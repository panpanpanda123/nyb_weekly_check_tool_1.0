"""
CSV导出器测试
CSV Exporter Tests
"""
import pytest
from csv_exporter import CSVExporter


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
                '所属区域': '测试区域',
                '检查项名称': '测试项',
                '检查项分类': '周清',
                '负责运营': '张三',
                '标准图': 'http://test.com/img.jpg',
                '审核结果': '合格',
                '审核时间': '2026-01-10 10:00:00'
            }
        ]
        
        csv_content = self.exporter._generate_csv_content(data)
        
        # 验证包含表头
        lines = csv_content.strip().split('\n')
        assert len(lines) == 2  # 表头 + 1行数据
        assert '门店名称' in lines[0]
        
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
        
        # 验证列顺序
        expected_columns = [
            '门店名称',
            '门店编号',
            '所属区域',
            '检查项名称',
            '检查项分类',
            '负责运营',
            '标准图',
            '审核结果',
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
