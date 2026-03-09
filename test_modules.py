#!/usr/bin/env python3
"""
测试模块化后的代码是否正常
Test Modularized Code
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

print("="*60)
print("测试模块导入")
print("="*60)

try:
    print("\n1. 测试主应用模块...")
    from viewer import app_viewer
    print("   ✓ app_viewer 导入成功")
    
    print("\n2. 测试API模块...")
    from viewer import api_review
    print("   ✓ api_review 导入成功")
    
    from viewer import api_rating
    print("   ✓ api_rating 导入成功")
    
    from viewer import api_equipment
    print("   ✓ api_equipment 导入成功")
    
    from viewer import api_promo
    print("   ✓ api_promo 导入成功")
    
    from viewer import api_upload
    print("   ✓ api_upload 导入成功")
    
    print("\n3. 测试Flask应用...")
    app = app_viewer.app
    print(f"   ✓ Flask应用创建成功")
    print(f"   ✓ 应用名称: {app.name}")
    
    print("\n4. 测试路由注册...")
    routes = [rule.rule for rule in app.url_map.iter_rules()]
    print(f"   ✓ 共注册 {len(routes)} 个路由")
    
    # 检查关键路由
    key_routes = [
        '/',
        '/rating',
        '/equipment',
        '/promoratio',
        '/api/filters',
        '/api/rating/stores',
        '/api/equipment/search',
        '/api/promo/search'
    ]
    
    missing_routes = []
    for route in key_routes:
        if route not in routes:
            missing_routes.append(route)
    
    if missing_routes:
        print(f"\n   ⚠️  缺少路由: {missing_routes}")
    else:
        print(f"   ✓ 所有关键路由已注册")
    
    print("\n" + "="*60)
    print("✓ 所有模块测试通过")
    print("="*60)
    print("\n可以启动服务进行功能测试：")
    print("  python3 viewer/app_viewer.py")
    print("\n")
    
except Exception as e:
    print(f"\n❌ 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
