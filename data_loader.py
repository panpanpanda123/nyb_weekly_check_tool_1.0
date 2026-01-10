"""
数据加载模块
Data Loader Module
"""
import pandas as pd
from typing import List, Dict, Optional
from whitelist_loader import WhitelistLoader


class DataLoader:
    """Excel数据加载器"""
    
    # 必需字段列表
    REQUIRED_FIELDS = [
        '检查项名称',
        '门店名称',
        '门店编号',
        '所属区域'
    ]
    
    def __init__(self, file_path: str, whitelist_path: Optional[str] = None):
        """
        初始化数据加载器
        
        Args:
            file_path: Excel文件路径
            whitelist_path: 白名单文件路径（可选）
        """
        self.file_path = file_path
        self.whitelist_path = whitelist_path
        self.df: Optional[pd.DataFrame] = None
        self.data: List[Dict] = []
        self.whitelist_loader: Optional[WhitelistLoader] = None
        
        # 如果提供了白名单路径，加载白名单
        if whitelist_path:
            self.whitelist_loader = WhitelistLoader(whitelist_path)
            self.whitelist_loader.load_whitelist()
    
    def load_excel(self) -> pd.DataFrame:
        """
        读取Excel文件
        
        Returns:
            pd.DataFrame: 读取的数据框
            
        Raises:
            FileNotFoundError: 文件不存在
            Exception: 其他读取错误
        """
        try:
            self.df = pd.read_excel(self.file_path)
            return self.df
        except FileNotFoundError:
            raise FileNotFoundError(f"Excel文件不存在: {self.file_path}")
        except Exception as e:
            raise Exception(f"读取Excel文件失败: {str(e)}")
    
    def validate_data(self) -> bool:
        """
        验证数据是否包含所有必需字段
        
        Returns:
            bool: 验证是否通过
            
        Raises:
            ValueError: 缺少必需字段时抛出异常，包含缺失字段列表
        """
        if self.df is None:
            raise ValueError("数据未加载，请先调用load_excel()")
        
        # 检查缺失的字段
        missing_fields = [field for field in self.REQUIRED_FIELDS 
                         if field not in self.df.columns]
        
        if missing_fields:
            raise ValueError(f"Excel文件缺少必需字段: {', '.join(missing_fields)}")
        
        return True
    
    def transform_data(self) -> List[Dict]:
        """
        将DataFrame转换为字典列表，并为每个检查项生成唯一ID
        
        Returns:
            List[Dict]: 转换后的数据列表
        """
        if self.df is None:
            raise ValueError("数据未加载，请先调用load_excel()")
        
        self.data = []
        
        for _, row in self.df.iterrows():
            # 生成唯一ID: 门店编号_检查项名称
            store_id = str(int(row['门店编号'])) if pd.notna(row['门店编号']) else 'unknown'
            item_name = str(row['检查项名称']) if pd.notna(row['检查项名称']) else 'unknown'
            unique_id = f"{store_id}_{item_name}"
            
            # 从"现场结果"列获取图片链接
            image_url = ''
            has_result = False
            
            # 尝试从"现场结果"列获取图片链接
            if '现场结果' in self.df.columns and pd.notna(row['现场结果']):
                try:
                    import json
                    result_data = str(row['现场结果']).strip()
                    
                    # 处理可能的格式：JSON数组后面跟着额外的URL
                    # 例如：["url1"],url2 这种情况
                    if result_data.startswith('[') and '],' in result_data:
                        # 只取JSON数组部分
                        json_end = result_data.index('],') + 1
                        result_data = result_data[:json_end]
                    
                    # 解析JSON数组
                    urls = json.loads(result_data)
                    if isinstance(urls, list) and len(urls) > 0:
                        # 取第一个URL，并检查是否是HTML标签
                        first_url = urls[0]
                        if isinstance(first_url, str):
                            # 检查是否是HTML标签
                            if first_url.strip().startswith('<img'):
                                # 提取src属性
                                import re
                                match = re.search(r'src="([^"]+)"', first_url)
                                if match:
                                    image_url = match.group(1)
                                    has_result = True
                            else:
                                # 直接使用URL
                                image_url = first_url
                                has_result = True
                except (json.JSONDecodeError, ValueError) as e:
                    # 如果解析失败，尝试直接使用字符串
                    result_str = str(row['现场结果']).strip()
                    if result_str and result_str != 'nan':
                        # 检查是否是HTML标签
                        if result_str.startswith('<img'):
                            import re
                            match = re.search(r'src="([^"]+)"', result_str)
                            if match:
                                image_url = match.group(1)
                                has_result = True
                        else:
                            image_url = result_str
                            has_result = True
            
            # 构建数据项
            item = {
                'id': unique_id,
                '检查项名称': str(row['检查项名称']) if pd.notna(row['检查项名称']) else '',
                '门店名称': str(row['门店名称']) if pd.notna(row['门店名称']) else '',
                '门店编号': str(int(row['门店编号'])) if pd.notna(row['门店编号']) else '',
                '所属区域': str(row['所属区域']) if pd.notna(row['所属区域']) else '',
                '标准图': image_url,  # 这里存储的是现场结果的图片URL
                '无现场结果': not has_result  # 标记是否缺少现场结果
            }
            
            # 如果存在检查项分类字段，也包含进来
            if '检查项分类' in self.df.columns:
                item['检查项分类'] = str(row['检查项分类']) if pd.notna(row['检查项分类']) else ''
            
            # 关联运营人员信息
            if self.whitelist_loader:
                operator = self.whitelist_loader.assign_operator(item['门店编号'])
                item['负责运营'] = operator
            else:
                item['负责运营'] = '未分配'
            
            self.data.append(item)
        
        return self.data
    
    def load_and_process(self) -> List[Dict]:
        """
        一次性完成加载、验证和转换
        
        Returns:
            List[Dict]: 处理后的数据列表
        """
        self.load_excel()
        self.validate_data()
        return self.transform_data()
    
    def get_data(self) -> List[Dict]:
        """
        获取已处理的数据
        
        Returns:
            List[Dict]: 数据列表
        """
        return self.data
    
    def get_all_operators(self) -> List[str]:
        """
        获取所有运营人员列表
        
        Returns:
            List[str]: 运营人员列表
        """
        if self.whitelist_loader:
            return self.whitelist_loader.get_all_operators()
        return []
    
    def filter_by_operator(self, operator: str) -> List[Dict]:
        """
        按运营人员筛选数据
        
        Args:
            operator: 运营人员姓名，"全部"表示不筛选
            
        Returns:
            List[Dict]: 筛选后的数据列表
        """
        if operator == "全部" or not operator:
            return self.data
        
        return [item for item in self.data if item.get('负责运营') == operator]
