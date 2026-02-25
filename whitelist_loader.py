"""
白名单加载模块
Whitelist Loader Module
"""
import pandas as pd
from typing import Dict, Optional
import os


class WhitelistLoader:
    """白名单数据加载器，用于加载运营人员分配信息"""
    
    def __init__(self, file_path: str):
        """
        初始化白名单加载器
        
        Args:
            file_path: 白名单Excel文件路径
        """
        self.file_path = file_path
        self.df: Optional[pd.DataFrame] = None
        self.operator_mapping: Dict[str, str] = {}  # {门店ID: 运营人员}
    
    def load_whitelist(self) -> bool:
        """
        读取白名单Excel文件
        
        Returns:
            bool: 是否成功加载
        """
        try:
            if not os.path.exists(self.file_path):
                print(f"警告: 白名单文件不存在: {self.file_path}")
                print("系统将继续运行，所有门店显示为'未分配'")
                return False
            
            self.df = pd.read_excel(self.file_path)
            print(f"成功加载白名单文件，共 {len(self.df)} 条门店数据")
            
            # 生成运营人员映射
            self._generate_operator_mapping()
            
            return True
            
        except Exception as e:
            print(f"警告: 读取白名单文件失败: {str(e)}")
            print("系统将继续运行，所有门店显示为'未分配'")
            return False
    
    def _generate_operator_mapping(self):
        """
        生成门店ID到运营人员的映射
        优先级：临时运营 > 省市运营 > "未分配"
        """
        if self.df is None:
            return
        
        for _, row in self.df.iterrows():
            # 安全地转换门店ID
            store_id = None
            raw_id = row.get('门店ID')
            
            if pd.notna(raw_id):
                try:
                    # 尝试转换为整数
                    if isinstance(raw_id, (int, float)):
                        store_id = str(int(raw_id))
                    else:
                        # 如果是字符串，清理后再转换
                        cleaned_id = str(raw_id).strip().replace('-', '').replace(' ', '')
                        if cleaned_id.isdigit():
                            store_id = cleaned_id
                        else:
                            # 如果包含非数字字符，直接使用原始值
                            store_id = str(raw_id).strip()
                except (ValueError, TypeError):
                    # 转换失败，使用原始字符串
                    store_id = str(raw_id).strip()
            
            if store_id is None or store_id == '':
                continue
            
            # 确定负责运营人员（优先临时运营）
            operator = self._get_operator(row)
            self.operator_mapping[store_id] = operator
    
    def _get_operator(self, row) -> str:
        """
        获取门店负责运营人员
        优先级：临时运营 > 省市运营 > "未分配"
        
        Args:
            row: DataFrame的一行数据
            
        Returns:
            str: 运营人员姓名
        """
        # 检查临时运营
        if '临时运营' in row and pd.notna(row['临时运营']) and str(row['临时运营']).strip():
            return str(row['临时运营']).strip()
        
        # 检查省市运营
        if '省市运营' in row and pd.notna(row['省市运营']) and str(row['省市运营']).strip():
            return str(row['省市运营']).strip()
        
        # 都没有则返回未分配
        return "未分配"
    
    def get_operator_mapping(self) -> Dict[str, str]:
        """
        获取门店ID到运营人员的映射字典
        
        Returns:
            Dict[str, str]: {门店ID: 运营人员}
        """
        return self.operator_mapping
    
    def assign_operator(self, store_id: str) -> str:
        """
        为指定门店ID分配运营人员
        
        Args:
            store_id: 门店ID（字符串格式）
            
        Returns:
            str: 运营人员姓名，如果未找到则返回"未分配"
        """
        return self.operator_mapping.get(store_id, "未分配")
    
    def get_all_operators(self) -> list:
        """
        获取所有运营人员列表（去重）
        
        Returns:
            list: 运营人员姓名列表
        """
        operators = set(self.operator_mapping.values())
        # 移除"未分配"，然后排序
        operators.discard("未分配")
        return sorted(list(operators))
    
    def get_stores_by_operator(self, operator: str) -> list:
        """
        获取指定运营人员负责的所有门店ID
        
        Args:
            operator: 运营人员姓名
            
        Returns:
            list: 门店ID列表
        """
        return [store_id for store_id, op in self.operator_mapping.items() 
                if op == operator]
