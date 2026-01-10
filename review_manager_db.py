"""
审核数据管理器模块（数据库版本）
Review Manager Module (Database Version)
"""
from typing import Dict, List, Optional
from datetime import datetime
from database import get_session, Review
from sqlalchemy.exc import SQLAlchemyError


class ReviewManager:
    """审核结果管理器（使用数据库持久化）"""
    
    def __init__(self):
        """初始化审核管理器"""
        pass
    
    def save_review(self, item_id: str, review_data: Dict) -> bool:
        """
        保存新的审核结果
        
        Args:
            item_id: 检查项唯一标识符（门店编号_检查项名称）
            review_data: 审核数据，包含门店信息、检查项信息和审核结果
            
        Returns:
            bool: 保存是否成功
        """
        try:
            session = get_session()
            
            # 检查是否已存在
            existing = session.query(Review).filter_by(item_id=item_id).first()
            
            if existing:
                # 更新现有记录
                existing.store_name = review_data.get('门店名称', existing.store_name)
                existing.store_id = review_data.get('门店编号', existing.store_id)
                existing.area = review_data.get('所属区域', existing.area)
                existing.item_name = review_data.get('检查项名称', existing.item_name)
                existing.image_url = review_data.get('标准图', existing.image_url)
                existing.review_result = review_data.get('审核结果', existing.review_result)
                existing.problem_note = review_data.get('问题描述', existing.problem_note)
                existing.review_time = datetime.now()
            else:
                # 创建新记录
                review = Review(
                    item_id=item_id,
                    store_name=review_data.get('门店名称', ''),
                    store_id=review_data.get('门店编号', ''),
                    area=review_data.get('所属区域', ''),
                    item_name=review_data.get('检查项名称', ''),
                    image_url=review_data.get('标准图', ''),
                    review_result=review_data.get('审核结果', ''),
                    problem_note=review_data.get('问题描述', ''),
                    review_time=datetime.now()
                )
                session.add(review)
            
            session.commit()
            return True
            
        except SQLAlchemyError as e:
            print(f"保存审核结果失败: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def update_review(self, item_id: str, review_data: Dict) -> bool:
        """
        更新现有审核结果
        
        Args:
            item_id: 检查项唯一标识符
            review_data: 新的审核数据
            
        Returns:
            bool: 更新是否成功
        """
        # 使用save_review，它会自动处理更新
        return self.save_review(item_id, review_data)
    
    def get_review(self, item_id: str) -> Optional[Dict]:
        """
        获取指定检查项的审核结果
        
        Args:
            item_id: 检查项唯一标识符
            
        Returns:
            Optional[Dict]: 审核结果字典，如果不存在则返回None
        """
        try:
            session = get_session()
            review = session.query(Review).filter_by(item_id=item_id).first()
            
            if review:
                return review.to_dict()
            return None
            
        except SQLAlchemyError as e:
            print(f"获取审核结果失败: {e}")
            return None
        finally:
            session.close()
    
    def get_all_reviews(self) -> List[Dict]:
        """
        获取所有审核结果
        
        Returns:
            List[Dict]: 所有审核结果的列表
        """
        try:
            session = get_session()
            reviews = session.query(Review).all()
            return [review.to_dict() for review in reviews]
            
        except SQLAlchemyError as e:
            print(f"获取所有审核结果失败: {e}")
            return []
        finally:
            session.close()
    
    def has_review(self, item_id: str) -> bool:
        """
        检查指定检查项是否已有审核结果
        
        Args:
            item_id: 检查项唯一标识符
            
        Returns:
            bool: 是否存在审核结果
        """
        try:
            session = get_session()
            exists = session.query(Review).filter_by(item_id=item_id).first() is not None
            return exists
            
        except SQLAlchemyError as e:
            print(f"检查审核结果失败: {e}")
            return False
        finally:
            session.close()
    
    def get_review_count(self) -> int:
        """
        获取审核结果总数
        
        Returns:
            int: 审核结果数量
        """
        try:
            session = get_session()
            count = session.query(Review).count()
            return count
            
        except SQLAlchemyError as e:
            print(f"获取审核结果数量失败: {e}")
            return 0
        finally:
            session.close()
    
    def clear_all_reviews(self) -> bool:
        """
        清空所有审核记录（用于开始新周期）
        
        Returns:
            bool: 是否成功
        """
        try:
            session = get_session()
            session.query(Review).delete()
            session.commit()
            print("✓ 已清空所有审核记录")
            return True
            
        except SQLAlchemyError as e:
            print(f"清空审核记录失败: {e}")
            session.rollback()
            return False
        finally:
            session.close()
