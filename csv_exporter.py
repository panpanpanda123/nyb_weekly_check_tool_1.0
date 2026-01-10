"""
CSV导出器模块
CSV Exporter Module
"""
import csv
from io import StringIO
from typing import List, Dict
from datetime import datetime


class CSVExporter:
    """CSV导出器，用于生成审核结果的CSV文件"""
    
    def __init__(self):
        """初始化CSV导出器"""
        pass
    
    def export_reviews(self, reviews: List[Dict], original_data: List[Dict]) -> str:
        """
        导出审核结果为CSV格式
        
        Args:
            reviews: 审核结果列表
            original_data: 原始检查项数据列表
            
        Returns:
            str: CSV格式的字符串内容（包含UTF-8 BOM）
        """
        # 合并原始数据和审核结果
        merged_data = self._merge_data(reviews, original_data)
        
        # 生成CSV内容
        csv_content = self._generate_csv_content(merged_data)
        
        # 添加UTF-8 BOM以支持Excel正确打开中文
        return '\ufeff' + csv_content
    
    def _merge_data(self, reviews: List[Dict], original_data: List[Dict]) -> List[Dict]:
        """
        合并原始数据和审核结果
        
        Args:
            reviews: 审核结果列表
            original_data: 原始检查项数据列表
            
        Returns:
            List[Dict]: 合并后的数据列表
        """
        # 创建审核结果的字典映射，方便查找
        review_map = {review['item_id']: review for review in reviews}
        
        merged = []
        
        for item in original_data:
            item_id = item['id']
            review = review_map.get(item_id)
            
            # 如果有审核结果，则合并
            if review:
                merged_item = {
                    '门店名称': item.get('门店名称', ''),
                    '门店编号': item.get('门店编号', ''),
                    '所属区域': item.get('所属区域', ''),
                    '检查项名称': item.get('检查项名称', ''),
                    '检查项分类': item.get('检查项分类', ''),
                    '负责运营': item.get('负责运营', ''),
                    '标准图': item.get('标准图', ''),
                    '审核结果': review.get('审核结果', ''),
                    '问题描述': review.get('问题描述', ''),
                    '审核时间': review.get('审核时间', '')
                }
                merged.append(merged_item)
        
        return merged
    
    def _generate_csv_content(self, data: List[Dict]) -> str:
        """
        生成CSV格式字符串
        
        Args:
            data: 要导出的数据列表
            
        Returns:
            str: CSV格式的字符串
        """
        if not data:
            return ''
        
        # 使用StringIO作为内存中的文件对象
        output = StringIO()
        
        # 定义CSV列
        fieldnames = [
            '门店名称',
            '门店编号',
            '所属区域',
            '检查项名称',
            '检查项分类',
            '负责运营',
            '标准图',
            '审核结果',
            '问题描述',
            '审核时间'
        ]
        
        # 创建CSV写入器
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator='\n')
        
        # 写入表头
        writer.writeheader()
        
        # 写入数据行
        for row in data:
            writer.writerow(row)
        
        # 获取CSV内容
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
    
    def generate_filename(self) -> str:
        """
        生成带时间戳的文件名
        
        Returns:
            str: 文件名，格式为"审核结果_YYYY-MM-DD.csv"
        """
        timestamp = datetime.now().strftime('%Y-%m-%d')
        return f'审核结果_{timestamp}.csv'
