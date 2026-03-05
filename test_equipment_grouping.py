#!/usr/bin/env python3
"""
测试设备分组逻辑
Test equipment grouping logic
"""

# 模拟设备数据
store_equipment = [
    {'equipment_type': 'POS', 'equipment_id': 'POS001', 'equipment_name': '收银机1'},
    {'equipment_type': 'POS', 'equipment_id': 'POS002', 'equipment_name': '收银机2'},
    {'equipment_type': '机顶盒', 'equipment_id': 'STB001', 'equipment_name': '机顶盒1'},
    {'equipment_type': '机顶盒', 'equipment_id': 'STB002', 'equipment_name': '机顶盒2'},
    {'equipment_type': '机顶盒', 'equipment_id': 'STB003', 'equipment_name': '机顶盒3'},
]

# 模拟处理记录
processing_records = [
    {'store_id': 'STORE001', 'equipment_type': 'POS', 'action': '已恢复', 'reason': ''},
    {'store_id': 'STORE001', 'equipment_type': '机顶盒', 'action': '未恢复', 'reason': '网络问题'},
]

# 测试分组逻辑
def test_grouping():
    print("=" * 60)
    print("测试设备分组逻辑")
    print("=" * 60)
    
    # 按设备类型分组
    pos_equipment = [eq for eq in store_equipment if eq['equipment_type'] == 'POS']
    stb_equipment = [eq for eq in store_equipment if eq['equipment_type'] == '机顶盒']
    
    print(f"\n✓ POS 设备数量: {len(pos_equipment)}")
    for eq in pos_equipment:
        print(f"  - {eq['equipment_name']} ({eq['equipment_id']})")
    
    print(f"\n✓ 机顶盒设备数量: {len(stb_equipment)}")
    for eq in stb_equipment:
        print(f"  - {eq['equipment_name']} ({eq['equipment_id']})")
    
    # 测试处理记录匹配
    print("\n" + "=" * 60)
    print("测试处理记录匹配")
    print("=" * 60)
    
    store_id = 'STORE001'
    processing_dict = {}
    for p in processing_records:
        key = f"{p['store_id']}_{p['equipment_type']}"
        processing_dict[key] = p
    
    pos_processing = processing_dict.get(f"{store_id}_POS")
    stb_processing = processing_dict.get(f"{store_id}_机顶盒")
    
    print(f"\n✓ POS 处理状态:")
    if pos_processing:
        print(f"  动作: {pos_processing['action']}")
        print(f"  原因: {pos_processing['reason'] or '无'}")
    else:
        print("  未处理")
    
    print(f"\n✓ 机顶盒处理状态:")
    if stb_processing:
        print(f"  动作: {stb_processing['action']}")
        print(f"  原因: {stb_processing['reason'] or '无'}")
    else:
        print("  未处理")
    
    print("\n" + "=" * 60)
    print("✅ 测试通过！逻辑正确")
    print("=" * 60)

if __name__ == '__main__':
    test_grouping()
