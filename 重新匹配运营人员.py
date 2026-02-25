"""
重新匹配运营人员（不影响审核结果）
"""
from whitelist_loader import WhitelistLoader
from database import Session, Review

whitelist_file = 'D:/pythonproject/Newyobo_operat_database/daily_data/whitelist/whitelist.xlsx'

print("=" * 60)
print("重新匹配运营人员")
print("=" * 60)
print()

# 1. 加载whitelist
print("📥 加载whitelist...")
loader = WhitelistLoader(whitelist_file)
success = loader.load_whitelist()

if not success:
    print("❌ whitelist加载失败")
    exit(1)

print(f"✅ whitelist加载成功")
print()

# 2. 连接数据库
print("🔗 连接数据库...")
try:
    session = Session()
    print("✅ 数据库连接成功")
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    print("   请确保PostgreSQL正在运行")
    exit(1)

print()

# 3. 获取所有审核记录
print("📊 获取审核记录...")
try:
    reviews = session.query(Review).all()
    print(f"✅ 找到 {len(reviews)} 条审核记录")
except Exception as e:
    print(f"❌ 查询失败: {e}")
    session.close()
    exit(1)

print()

# 4. 重新匹配运营人员
print("🔄 重新匹配运营人员...")
updated_count = 0
unassigned_before = 0
unassigned_after = 0

for review in reviews:
    old_operator = review.operator if hasattr(review, 'operator') else '未分配'
    
    # 统计之前未分配的数量
    if old_operator == "未分配" or old_operator is None:
        unassigned_before += 1
    
    # 重新匹配运营人员
    new_operator = loader.assign_operator(review.store_id)
    
    # 统计之后未分配的数量
    if new_operator == "未分配":
        unassigned_after += 1
    
    # 如果运营人员有变化，更新数据库
    if old_operator != new_operator:
        review.operator = new_operator
        updated_count += 1
        
        if updated_count <= 5:  # 只显示前5个
            print(f"   更新: 门店{review.store_id} {old_operator} -> {new_operator}")

if updated_count > 5:
    print(f"   ... 还有 {updated_count - 5} 条记录已更新")

# 提交更改
try:
    session.commit()
    print()
    print(f"✅ 匹配完成，已提交到数据库")
except Exception as e:
    session.rollback()
    print(f"❌ 提交失败: {e}")
    session.close()
    exit(1)

print()

# 5. 显示结果
print("📈 匹配结果:")
print(f"   总审核记录: {len(reviews)} 条")
print(f"   更新记录: {updated_count} 条")
print(f"   未分配（修复前）: {unassigned_before} 条")
print(f"   未分配（修复后）: {unassigned_after} 条")
print(f"   成功修复: {unassigned_before - unassigned_after} 条")
print()

# 6. 显示运营人员统计
print("👥 运营人员统计:")
operator_stats = {}
for review in reviews:
    operator = review.operator if hasattr(review, 'operator') and review.operator else '未分配'
    operator_stats[operator] = operator_stats.get(operator, 0) + 1

for operator, count in sorted(operator_stats.items(), key=lambda x: x[1], reverse=True):
    print(f"   {operator}: {count} 条审核记录")

print()

# 关闭会话
session.close()

print("=" * 60)
print("✅ 完成！审核结果已保留，运营人员已重新匹配")
print("=" * 60)
print()
print("💡 下一步:")
print("   1. 启动系统: 双击'启动周清审核.bat'")
print("   2. 访问: http://localhost:5001")
print("   3. 导出CSV，运营人员信息已更新")
print("   4. 上传到云服务器")
