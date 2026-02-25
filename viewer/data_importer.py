"""
数据导入模块
Data Importer Module for Viewer System
"""
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy.orm import Session
from shared.database_models import StoreWhitelist, ViewerReviewResult, StoreOperationData


@dataclass
class ImportResult:
    """导入结果数据类"""
    success: bool
    records_count: int
    unmatched_stores_count: int = 0  # 新增：未匹配的门店数量
    error_message: Optional[str] = None


class DataImporter:
    """数据导入器，用于导入白名单和审核结果数据"""
    
    def __init__(self, session: Session):
        """
        初始化数据导入器
        
        Args:
            session: SQLAlchemy数据库会话
        """
        self.session = session
    
    def import_whitelist(self, file_path: str) -> ImportResult:
        """
        导入白名单Excel文件
        
        Args:
            file_path: 白名单Excel文件路径
            
        Returns:
            ImportResult: 导入结果
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 验证文件格式
            if not self.validate_whitelist_format(df):
                return ImportResult(
                    success=False,
                    records_count=0,
                    error_message="白名单文件格式不正确，缺少必需列"
                )
            
            # 清空现有数据
            self.session.query(StoreWhitelist).delete()
            
            # 导入数据（使用字典去重，保留最后一条）
            records_count = 0
            stores_dict = {}  # 用于去重
            
            for _, row in df.iterrows():
                # 兼容"门店ID"和"门店编号"两种列名
                store_id_value = row.get('门店ID') if '门店ID' in df.columns else row.get('门店编号')
                
                # 跳过门店ID为空的行
                if pd.isna(store_id_value):
                    continue
                
                # 处理门店ID：跳过带'-'的异常门店ID
                try:
                    # 如果是字符串且包含'-'，直接跳过
                    if isinstance(store_id_value, str) and '-' in str(store_id_value):
                        print(f"⚠️  跳过异常门店ID: {store_id_value}")
                        continue
                    
                    # 正常转换为字符串
                    if isinstance(store_id_value, str):
                        store_id = str(int(store_id_value.strip()))
                    else:
                        store_id = str(int(store_id_value))
                except (ValueError, TypeError):
                    # 如果转换失败，跳过这一行
                    print(f"⚠️  跳过无效门店ID: {store_id_value}")
                    continue
                
                store = StoreWhitelist(
                    store_id=store_id,
                    province=str(row.get('省份', '')) if pd.notna(row.get('省份')) else None,
                    city=str(row.get('城市', '')) if pd.notna(row.get('城市')) else None,
                    store_name=str(row.get('门店名称', '')) if pd.notna(row.get('门店名称')) else None,
                    war_zone=str(row.get('战区', '')) if pd.notna(row.get('战区')) else None,
                    store_tag=str(row.get('门店标签', '')) if pd.notna(row.get('门店标签')) else None,
                    old_operator=str(row.get('老运营', '')) if pd.notna(row.get('老运营')) else None,
                    city_operator=str(row.get('省市运营', '')) if pd.notna(row.get('省市运营')) else None,
                    temp_operator=str(row.get('临时运营', '')) if pd.notna(row.get('临时运营')) else None,
                    sub_operator=str(row.get('次运营', '')) if pd.notna(row.get('次运营')) else None,
                    regional_manager=str(row.get('区域经理', '')) if pd.notna(row.get('区域经理')) else None,
                    business_status=str(row.get('门店营业状态', '')) if pd.notna(row.get('门店营业状态')) else None,
                    menu_version=str(row.get('菜单版本', '')) if pd.notna(row.get('菜单版本')) else None
                )
                
                # 使用字典去重（如果有重复ID，保留最后一条）
                stores_dict[store_id] = store
            
            # 批量添加去重后的门店
            for store in stores_dict.values():
                self.session.add(store)
                records_count += 1
            
            # 提交事务
            self.session.commit()
            
            return ImportResult(
                success=True,
                records_count=records_count,
                error_message=None
            )
            
        except Exception as e:
            self.session.rollback()
            return ImportResult(
                success=False,
                records_count=0,
                error_message=f"导入白名单失败: {str(e)}"
            )
    
    def import_reviews(self, file_path: str) -> ImportResult:
        """
        导入审核结果CSV文件
        
        如果门店在白名单中找不到，会将战区/省份/城市标记为"[未匹配]"
        
        Args:
            file_path: 审核结果CSV文件路径
            
        Returns:
            ImportResult: 导入结果，包含未匹配门店的数量
        """
        try:
            # 读取CSV文件
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            # 验证文件格式
            if not self.validate_reviews_format(df):
                return ImportResult(
                    success=False,
                    records_count=0,
                    unmatched_stores_count=0,
                    error_message="审核结果文件格式不正确，缺少必需列"
                )
            
            # 清空现有数据
            self.session.query(ViewerReviewResult).delete()
            
            # 预先加载所有白名单门店到内存，提高查询效率
            whitelist_stores = {}
            for store in self.session.query(StoreWhitelist).all():
                whitelist_stores[store.store_id] = store
            
            # 导入数据
            records_count = 0
            unmatched_stores_count = 0
            unmatched_store_ids = set()  # 记录未匹配的门店ID
            import_time = datetime.now()
            
            for _, row in df.iterrows():
                # 门店编号转换为字符串，保留前导零
                store_id_raw = row.get('门店编号', '')
                if pd.notna(store_id_raw):
                    # 如果是数字类型，转换为整数再转字符串（去除小数点）
                    if isinstance(store_id_raw, (int, float)):
                        store_id = str(int(store_id_raw))
                    else:
                        # 如果已经是字符串，直接使用
                        store_id = str(store_id_raw).strip()
                else:
                    store_id = ''
                
                # 尝试从白名单中获取门店信息
                whitelist_store = whitelist_stores.get(store_id)
                
                # 如果CSV中已有战区/省份/城市，优先使用CSV中的数据
                war_zone = str(row.get('战区', '')) if pd.notna(row.get('战区')) else None
                province = str(row.get('省份', '')) if pd.notna(row.get('省份')) else None
                city = str(row.get('城市', '')) if pd.notna(row.get('城市')) else None
                
                # 如果CSV中没有这些信息，尝试从白名单获取
                if whitelist_store:
                    # 如果CSV中没有战区/省份/城市，从白名单补充
                    if not war_zone:
                        war_zone = whitelist_store.war_zone
                    if not province:
                        province = whitelist_store.province
                    if not city:
                        city = whitelist_store.city
                else:
                    # 门店在白名单中不存在，标记为未匹配
                    if store_id and store_id not in unmatched_store_ids:
                        unmatched_stores_count += 1
                        unmatched_store_ids.add(store_id)
                    
                    # 如果CSV中也没有地理信息，标记为"[未匹配]"
                    if not war_zone:
                        war_zone = "[未匹配]"
                    if not province:
                        province = "[未匹配]"
                    if not city:
                        city = "[未匹配]"
                
                # 解析审核时间
                review_time = None
                if pd.notna(row.get('审核时间')):
                    try:
                        review_time = pd.to_datetime(row['审核时间'])
                    except:
                        pass
                
                result = ViewerReviewResult(
                    store_name=str(row.get('门店名称', '')) if pd.notna(row.get('门店名称')) else '',
                    store_id=store_id,
                    war_zone=war_zone,
                    province=province,
                    city=city,
                    area=str(row.get('所属区域', '')) if pd.notna(row.get('所属区域')) else None,
                    item_name=str(row.get('检查项名称', '')) if pd.notna(row.get('检查项名称')) else '',
                    item_category=str(row.get('检查项分类', '')) if pd.notna(row.get('检查项分类')) else None,
                    image_url=str(row.get('标准图', '')) if pd.notna(row.get('标准图')) else None,
                    review_result=str(row.get('审核结果', '')) if pd.notna(row.get('审核结果')) else '',
                    problem_note=str(row.get('问题描述', '')) if pd.notna(row.get('问题描述')) else None,
                    review_time=review_time,
                    import_time=import_time
                )
                self.session.add(result)
                records_count += 1
            
            # 提交事务
            self.session.commit()
            
            return ImportResult(
                success=True,
                records_count=records_count,
                unmatched_stores_count=unmatched_stores_count,
                error_message=None
            )
            
        except Exception as e:
            self.session.rollback()
            return ImportResult(
                success=False,
                records_count=0,
                unmatched_stores_count=0,
                error_message=f"导入审核结果失败: {str(e)}"
            )
    
    def validate_whitelist_format(self, df: pd.DataFrame) -> bool:
        """
        验证白名单文件格式
        
        Args:
            df: pandas DataFrame
            
        Returns:
            bool: 格式是否正确
        """
        # 兼容"门店ID"和"门店编号"两种列名
        has_store_id = '门店ID' in df.columns or '门店编号' in df.columns
        has_store_name = '门店名称' in df.columns
        return has_store_id and has_store_name
    
    def validate_reviews_format(self, df: pd.DataFrame) -> bool:
        """
        验证审核结果文件格式
        
        Args:
            df: pandas DataFrame
            
        Returns:
            bool: 格式是否正确
        """
        required_columns = ['门店名称', '门店编号', '检查项名称', '审核结果']
        return all(col in df.columns for col in required_columns)
    
    def import_operation_data(self, file_path: str, sheet_name: str = 'Sheet2') -> ImportResult:
        """
        导入门店运营数据（从Excel的Sheet2）
        
        Args:
            file_path: Excel文件路径
            sheet_name: Sheet名称，默认为'Sheet2'
            
        Returns:
            ImportResult: 导入结果
        """
        try:
            # 读取Excel文件的指定Sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # 验证文件格式（至少需要门店ID列）
            if 'A' not in df.columns and '门店ID' not in df.columns and '门店编号' not in df.columns:
                # 尝试使用第一列作为门店ID
                if len(df.columns) > 0:
                    df.rename(columns={df.columns[0]: '门店ID'}, inplace=True)
                else:
                    return ImportResult(
                        success=False,
                        records_count=0,
                        error_message="运营数据文件格式不正确，缺少门店ID列"
                    )
            
            # 清空现有数据
            self.session.query(StoreOperationData).delete()
            
            # 导入数据
            records_count = 0
            for _, row in df.iterrows():
                # 获取门店ID（兼容多种列名）
                store_id_value = None
                for col_name in ['门店ID', '门店编号', 'A', df.columns[0]]:
                    if col_name in df.columns and pd.notna(row.get(col_name)):
                        store_id_value = row.get(col_name)
                        break
                
                # 跳过门店ID为空的行
                if store_id_value is None or pd.isna(store_id_value):
                    continue
                
                # 转换门店ID为字符串
                if isinstance(store_id_value, (int, float)):
                    store_id = str(int(store_id_value))
                else:
                    store_id = str(store_id_value).strip()
                
                # 获取运营数据（尝试多种可能的列名）
                # 优先使用"1月堂食营业额"（T列），如果没有则使用"堂食营业额"
                dine_in_revenue = self._get_column_value(row, df.columns, ['1月堂食营业额', '堂食营业额', '营业额', 'B'])
                comprehensive_score = self._get_column_value(row, df.columns, ['综合得分', '得分', 'C'])
                operation_score = self._get_column_value(row, df.columns, ['评分', '运营评分', 'D'])
                
                operation_data = StoreOperationData(
                    store_id=store_id,
                    dine_in_revenue=dine_in_revenue,
                    comprehensive_score=comprehensive_score,
                    operation_score=operation_score,
                    updated_at=datetime.now()
                )
                self.session.add(operation_data)
                records_count += 1
            
            # 提交事务
            self.session.commit()
            
            return ImportResult(
                success=True,
                records_count=records_count,
                error_message=None
            )
            
        except Exception as e:
            self.session.rollback()
            return ImportResult(
                success=False,
                records_count=0,
                error_message=f"导入运营数据失败: {str(e)}"
            )
    
    def _get_column_value(self, row: pd.Series, columns: pd.Index, possible_names: List[str]) -> Optional[str]:
        """
        从行中获取列值（尝试多个可能的列名）
        
        Args:
            row: pandas Series（一行数据）
            columns: DataFrame的列名列表
            possible_names: 可能的列名列表
            
        Returns:
            str: 列值（如果找到），否则返回None
        """
        for name in possible_names:
            if name in columns and pd.notna(row.get(name)):
                value = row.get(name)
                # 转换为字符串
                if isinstance(value, (int, float)):
                    return str(value)
                else:
                    return str(value).strip()
        return None
