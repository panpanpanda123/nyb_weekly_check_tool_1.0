"""
共用数据库模型
Shared Database Models for Review System and Viewer System
"""
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, Index
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from datetime import datetime
import os

# 创建基类
Base = declarative_base()


class StoreWhitelist(Base):
    """门店白名单模型 - 共用模型"""
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
        Index('idx_whitelist_war_zone', 'war_zone'),
        Index('idx_whitelist_province', 'province'),
        Index('idx_whitelist_city', 'city'),
        Index('idx_whitelist_store_tag', 'store_tag'),
        Index('idx_city_operator', 'city_operator'),
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


class ViewerReviewResult(Base):
    """审核结果模型 - 展示系统专用表"""
    __tablename__ = 'viewer_review_results'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')
    
    # 门店信息
    store_name = Column(String(255), nullable=False, comment='门店名称')
    store_id = Column(String(50), nullable=False, comment='门店编号')
    war_zone = Column(String(50), comment='战区')
    province = Column(String(50), comment='省份')
    city = Column(String(50), comment='城市')
    area = Column(String(255), comment='所属区域')
    
    # 检查项信息
    item_name = Column(String(255), nullable=False, comment='检查项名称')
    item_category = Column(String(100), comment='检查项分类')
    image_url = Column(Text, comment='图片URL')
    
    # 审核信息
    review_result = Column(String(50), nullable=False, comment='审核结果：合格/不合格')
    problem_note = Column(Text, comment='问题描述')
    review_time = Column(DateTime, comment='审核时间')
    import_time = Column(DateTime, default=datetime.now, comment='导入时间')
    
    # 索引定义
    __table_args__ = (
        Index('idx_viewer_war_zone', 'war_zone'),
        Index('idx_viewer_province', 'province'),
        Index('idx_viewer_city', 'city'),
        Index('idx_viewer_review_result', 'review_result'),
        Index('idx_viewer_composite', 'war_zone', 'province', 'city', 'review_result'),
        Index('idx_viewer_store_id', 'store_id'),
        {'comment': '审核结果展示表'}
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'store_name': self.store_name,
            'store_id': self.store_id,
            'war_zone': self.war_zone or '',
            'province': self.province or '',
            'city': self.city or '',
            'area': self.area or '',
            'item_name': self.item_name,
            'item_category': self.item_category or '',
            'image_url': self.image_url or '',
            'review_result': self.review_result,
            'problem_note': self.problem_note or '',
            'review_time': self.review_time.strftime('%Y-%m-%d %H:%M:%S') if self.review_time else '',
            'import_time': self.import_time.strftime('%Y-%m-%d %H:%M:%S') if self.import_time else ''
        }


def get_database_url(default_db: str = 'configurable_ops') -> str:
    """
    获取数据库连接URL
    
    Args:
        default_db: 默认数据库名称
        
    Returns:
        str: 数据库连接URL
    """
    return os.getenv(
        'DATABASE_URL',
        f'postgresql://postgres:postgres@127.0.0.1:5432/{default_db}'
    )


def create_db_engine(database_url: str = None, echo: bool = False):
    """
    创建数据库引擎
    
    Args:
        database_url: 数据库连接URL，如果为None则使用默认值
        echo: 是否打印SQL语句
        
    Returns:
        Engine: SQLAlchemy引擎
    """
    if database_url is None:
        database_url = get_database_url()
    return create_engine(database_url, echo=echo, pool_pre_ping=True)


def create_session_factory(engine):
    """
    创建会话工厂
    
    Args:
        engine: SQLAlchemy引擎
        
    Returns:
        scoped_session: 线程安全的会话工厂
    """
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)


def init_viewer_db(engine):
    """
    初始化展示系统数据库表
    
    Args:
        engine: SQLAlchemy引擎
    """
    Base.metadata.create_all(engine)
    print("✓ 展示系统数据库表初始化完成")
    print(f"  - 表名: {StoreWhitelist.__tablename__}")
    print(f"  - 表名: {ViewerReviewResult.__tablename__}")
