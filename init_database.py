"""
数据库初始化脚本
Database Initialization Script
"""
from database import init_db, engine
from sqlalchemy import text

def check_database_connection():
    """检查数据库连接"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ 数据库连接成功")
            return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False

def main():
    print("=" * 60)
    print("门店检查项审核系统 - 数据库初始化")
    print("=" * 60)
    
    # 检查连接
    if not check_database_connection():
        print("\n请检查:")
        print("1. PostgreSQL是否正在运行")
        print("2. 数据库 'configurable_ops' 是否已创建")
        print("3. 数据库连接信息是否正确")
        print("   默认: postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops")
        return
    
    # 初始化表
    print("\n正在创建数据库表...")
    init_db()
    
    print("\n✓ 数据库初始化完成！")
    print("\n现在可以启动系统了: python app.py")

if __name__ == '__main__':
    main()
