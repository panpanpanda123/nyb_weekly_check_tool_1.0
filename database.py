"""
数据库模型和连接管理
Database Models and Connection Management
"""
from sqlalchemy import create_engine, Column, String, Text, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
import os

# 数据库连接URL
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

# 创建引擎
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# 创建会话工厂
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# 创建基类
Base = declarative_base()


class Review(Base):
    """审核记录模型"""
    __tablename__ = 'store_inspection_reviews'  # 使用更具体的表名，避免冲突
    
    # 主键
    item_id = Column(String(255), primary_key=True, comment='检查项唯一标识')
    
    # 门店信息（未来可以关联门店表）
    store_name = Column(String(255), nullable=False, comment='门店名称')
    store_id = Column(String(50), nullable=False, index=True, comment='门店编号')
    area = Column(String(255), comment='所属区域')
    
    # 检查项信息
    item_name = Column(String(255), nullable=False, comment='检查项名称')
    image_url = Column(Text, comment='标准图URL')
    
    # 审核信息
    review_result = Column(String(50), nullable=False, comment='审核结果：合格/不合格')
    problem_note = Column(Text, comment='问题描述')
    review_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='审核时间')
    
    # 添加复合索引，提高查询性能
    __table_args__ = (
        Index('idx_store_review', 'store_id', 'review_result'),  # 按门店和结果查询
        Index('idx_review_time', 'review_time'),  # 按时间查询
        {'comment': '门店检查项审核记录表'}
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'item_id': self.item_id,
            '门店名称': self.store_name,
            '门店编号': self.store_id,
            '所属区域': self.area,
            '检查项名称': self.item_name,
            '标准图': self.image_url,
            '审核结果': self.review_result,
            '问题描述': self.problem_note or '',
            '审核时间': self.review_time.strftime('%Y-%m-%d %H:%M:%S') if self.review_time else ''
        }


class StoreWhitelist(Base):
    """门店白名单模型"""
    __tablename__ = 'store_whitelist'
    
    # 主键
    store_id = Column(String(50), primary_key=True, comment='门店ID')
    
    # 门店信息
    province = Column(String(50), comment='省份')
    city = Column(String(50), comment='城市')
    store_name = Column(String(255), comment='门店名称')
    war_zone = Column(String(50), comment='战区')
    store_tag = Column(String(100), comment='门店标签')
    
    # 运营人员信息
    old_operator = Column(String(50), comment='老运营')
    city_operator = Column(String(50), index=True, comment='省市运营')
    temp_operator = Column(String(50), comment='临时运营')
    sub_operator = Column(String(50), comment='次运营')
    
    # 其他信息
    business_status = Column(String(50), comment='门店营业状态')
    menu_version = Column(String(50), comment='菜单版本')
    
    __table_args__ = (
        Index('idx_city_operator', 'city_operator'),  # 按运营人员查询
        {'comment': '门店白名单表'}
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'store_id': self.store_id,
            'province': self.province,
            'city': self.city,
            'store_name': self.store_name,
            'war_zone': self.war_zone,
            'store_tag': self.store_tag,
            'old_operator': self.old_operator,
            'city_operator': self.city_operator,
            'temp_operator': self.temp_operator,
            'sub_operator': self.sub_operator,
            'business_status': self.business_status,
            'menu_version': self.menu_version
        }


def init_db():
    """初始化数据库，创建所有表"""
    # 只创建当前项目定义的表，不影响其他表
    Base.metadata.create_all(engine)
    print("✓ 数据库表初始化完成")
    print(f"  - 表名: {Review.__tablename__}")
    print(f"  - 表名: {StoreWhitelist.__tablename__}")


def load_whitelist_to_db(whitelist_file: str) -> int:
    """
    加载白名单Excel到数据库（覆盖式更新）
    
    Args:
        whitelist_file: 白名单Excel文件路径
        
    Returns:
        int: 加载的门店数量
    """
    try:
        import pandas as pd
        
        # 读取Excel
        df = pd.read_excel(whitelist_file)
        
        session = get_session()
        
        # 清空现有白名单数据
        session.query(StoreWhitelist).delete()
        
        # 批量插入新数据
        count = 0
        for _, row in df.iterrows():
            store = StoreWhitelist(
                store_id=str(int(row['门店ID'])) if pd.notna(row['门店ID']) else None,
                province=str(row['省份']) if pd.notna(row['省份']) else None,
                city=str(row['城市']) if pd.notna(row['城市']) else None,
                store_name=str(row['门店名称']) if pd.notna(row['门店名称']) else None,
                war_zone=str(row['战区']) if pd.notna(row['战区']) else None,
                store_tag=str(row['门店标签']) if pd.notna(row['门店标签']) else None,
                old_operator=str(row['老运营']) if pd.notna(row['老运营']) else None,
                city_operator=str(row['省市运营']) if pd.notna(row['省市运营']) else None,
                temp_operator=str(row['临时运营']) if pd.notna(row['临时运营']) else None,
                sub_operator=str(row['次运营']) if pd.notna(row['次运营']) else None,
                business_status=str(row['门店营业状态']) if pd.notna(row['门店营业状态']) else None,
                menu_version=str(row['菜单版本']) if pd.notna(row['菜单版本']) else None
            )
            session.add(store)
            count += 1
        
        session.commit()
        print(f"✓ 白名单加载完成，共 {count} 条门店数据")
        return count
        
    except Exception as e:
        print(f"✗ 白名单加载失败: {e}")
        session.rollback()
        return 0
    finally:
        session.close()


def get_all_operators_from_db() -> list:
    """
    从数据库获取所有运营人员列表
    
    Returns:
        list: 运营人员列表（去重排序）
    """
    try:
        session = get_session()
        
        # 查询所有不为空的省市运营
        operators = session.query(StoreWhitelist.city_operator).filter(
            StoreWhitelist.city_operator.isnot(None),
            StoreWhitelist.city_operator != ''
        ).distinct().all()
        
        # 提取并排序
        operator_list = sorted([op[0] for op in operators if op[0]])
        
        return operator_list
        
    except Exception as e:
        print(f"获取运营人员列表失败: {e}")
        return []
    finally:
        session.close()


def get_operator_by_store_id(store_id: str) -> str:
    """
    根据门店ID从数据库获取运营人员
    
    Args:
        store_id: 门店ID
        
    Returns:
        str: 运营人员姓名，如果未找到返回'未分配'
    """
    try:
        session = get_session()
        
        store = session.query(StoreWhitelist).filter_by(store_id=store_id).first()
        
        if store and store.city_operator:
            return store.city_operator
        
        return '未分配'
        
    except Exception as e:
        print(f"查询运营人员失败: {e}")
        return '未分配'
    finally:
        session.close()


def get_session():
    """获取数据库会话"""
    return Session()


def close_session():
    """关闭数据库会话"""
    Session.remove()
