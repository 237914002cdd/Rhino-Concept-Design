# 通用面积配平公式 - 可执行版本
# 适用于任何商务酒店/综合体项目
# 输入任务书数据，输出各标准层面积

import math

def calc_core_area():
    """核心筒面积计算（1-26F贯通）"""
    stairs = 6.5 * 2.6 * 2          # 楼梯2座
    fire_elev = 2.6 * 2.6 * 2       # 消防电梯2台
    # 客梯数量取决于建筑规模
    pass_elev = 2.4 * 2.4 * 4       # 4台客梯
    hall = 15                         # 电梯厅
    pipe = 8                          # 管井
    front = 12                        # 防烟前室
    total = stairs + fire_elev + pass_elev + hall + pipe + front
    return round(total, 1)

def calc_hotel_floor(N_rooms, N_hotelF, room_w=4.2, room_d=9.5, corridor_w=1.5):
    """酒店标准层面积推导

    输入:
        N_rooms: 客房总数（间）
        N_hotelF: 酒店客房层数（层）
        room_w: 客房开间（m, 默认4.2）
        room_d: 客房进深（m, 默认9.5）
        corridor_w: 走廊净宽（m, 默认1.5）

    输出:
        酒店标准层面积（㎡/层）
    """
    rooms_per_floor = N_rooms / N_hotelF  # 每层间数
    core_w = 10  # 核心筒宽度 ≈10m

    # 单元定义（5间/单元，双侧布房+中廊）
    unit_width = room_w * 5              # 5间×4.2m
    unit_depth = room_d * 2 + corridor_w # 双侧进深+走廊
    unit_area = unit_width * unit_depth  # 单元面积

    # 需要几个单元
    rooms_per_unit = 10  # 一个完整单元10间（5+5两侧）

    # 精确计算：最小1个单元，按实际间数决定
    # 每单元10间
    exact_units = rooms_per_floor / rooms_per_unit
    units = max(1, round(exact_units + 0.1))  # 向上取整但保留整数

    # 小体量处理：不足1.5单元用1单元
    if exact_units <= 1.5:
        units = 1

    # 如果房间数很少，核心筒不按完整单元宽度算
    # 小体量时核心筒占比更高
    if units <= 1:
        # 单边布房或一侧布房一侧走道
        single_w = room_w * min(rooms_per_floor, 5) + 2  # 走道余量
        total_w = single_w + core_w
        total_d = unit_depth
        floor_area = total_w * total_d
    else:
        # 多单元
        total_w = units * unit_width + core_w
        total_d = unit_depth
        floor_area = total_w * total_d

    return round(floor_area, 1), {
        "每层客房数": round(rooms_per_floor, 1),
        "单元数": units,
        "单元尺寸": f"{round(unit_width)}m×{round(unit_depth)}m",
        "总尺寸": f"{round(total_w)}m×{round(total_d)}m",
        "核心筒面积": calc_core_area()
    }

def calc_podium(site_area, density_max=0.35, N_podiumF=4):
    """裙房标准层面积推导

    输入:
        site_area: 用地面积（㎡）
        density_max: 最大建筑密度（默认0.35）
        N_podiumF: 裙房层数（默认4）

    输出:
        裙房标准层面积（㎡/层）
    """
    max_footprint = site_area * density_max
    # 裙房基底取密度的85-100%，留余地给塔楼基底
    podium_base = round(max_footprint * 0.85, 1)
    return podium_base

def balance(S_total, site_area, N_rooms, N_hotelF, N_officeF, N_podiumF=4,
            room_w=4.2, room_d=9.5):
    """通用面积配平主函数

    输入:
        S_total: 地上总面积（㎡）     ← 任务书
        site_area: 用地面积（㎡）    ← 任务书
        N_rooms: 酒店客房总数       ← 任务书
        N_hotelF: 酒店客房层数      ← 任务书（如16-26F=11层）
        N_officeF: 办公层数         ← 任务书（如5-15F=11层）
        N_podiumF: 裙房层数         ← 任务书（通常4层）

    输出:
        dict: 各标准层面积+总体验证
    """
    # 1. 酒店面积
    hotel_floor, hotel_detail = calc_hotel_floor(N_rooms, N_hotelF, room_w, room_d)
    hotel_total = hotel_floor * N_hotelF

    # 2. 裙房面积（受密度约束）
    podium_floor = calc_podium(site_area, N_podiumF=N_podiumF)
    podium_total = podium_floor * N_podiumF

    # 3. 办公面积（剩余分配）
    office_total = S_total - hotel_total - podium_total
    office_floor = round(office_total / N_officeF, 1)

    # 4. 总体验证
    total = hotel_total + podium_total + office_total
    error_pct = round((total - S_total) / S_total * 100, 1)

    return {
        "hotel": {
            "per_floor": hotel_floor,
            "size": f"{round(hotel_floor**0.5)}m×{round(hotel_floor**0.5)}m" if hotel_floor>0 else "N/A",
            "floors": N_hotelF,
            "total": round(hotel_total, 1),
            "detail": hotel_detail
        },
        "office": {
            "per_floor": office_floor,
            "size": f"{round(office_floor**0.5)}m×{round(office_floor**0.5)}m" if office_floor>0 else "N/A",
            "floors": N_officeF,
            "total": round(office_total, 1)
        },
        "podium": {
            "per_floor": podium_floor,
            "size": f"{round(podium_floor**0.5)}m×{round(podium_floor**0.5)}m",
            "floors": N_podiumF,
            "total": round(podium_total, 1)
        },
        "total": round(total, 1),
        "target": S_total,
        "error_pct": error_pct,
        "core_area": calc_core_area()
    }

def print_report(result):
    """Print area balance report in English for encoding safety"""
    print("=" * 60)
    print("  AREA BALANCE REPORT")
    print("=" * 60)
    print(f"\n[Input]")
    print(f"  Total above ground: {result['target']}m2")
    if '每层客房数' in result['hotel']['detail']:
        rpf = result['hotel']['detail']['每层客房数']
    else:
        rpf = '?'
    print(f"  Hotel rooms: {rpf}/floor x {result['hotel']['floors']}F")
    print(f"  Office: {result['office']['floors']}F")
    print(f"  Podium: {result['podium']['floors']}F")

    print(f"\n[Output]")
    print(f"  Hotel floor: {result['hotel']['per_floor']}m2 -> {result['hotel']['size']}")
    print(f"    Units: {result['hotel']['detail'].get('单元数','?')}, Core: {result['core_area']}m2")
    print(f"    Total: {result['hotel']['total']}m2")
    print(f"  Office floor: {result['office']['per_floor']}m2 -> {result['office']['size']}")
    print(f"    Total: {result['office']['total']}m2")
    print(f"  Podium floor: {result['podium']['per_floor']}m2 -> {result['podium']['size']}")
    print(f"    Total: {result['podium']['total']}m2")

    print(f"\n  Sum: {result['total']}m2 / Target: {result['target']}m2")
    print(f"  Error: {result['error_pct']}%")
    status = "[PASS]" if abs(result['error_pct']) <= 5 else "[FAIL]"
    print(f"  {status}")
    print("=" * 60)


# ===== 测试用例 =====
if __name__ == "__main__":
    print("\n【测试1：当前商务酒店项目】")
    r1 = balance(
        S_total=37807.32,
        site_area=9450,
        N_rooms=207,
        N_hotelF=11,
        N_officeF=11,
        N_podiumF=4
    )
    print_report(r1)

    print("\n【测试2：假设小型精品酒店】")
    r2 = balance(
        S_total=12000,
        site_area=5000,
        N_rooms=80,
        N_hotelF=5,
        N_officeF=5,
        N_podiumF=3
    )
    print_report(r2)

    print("\n【测试3：假设大型综合体】")
    r3 = balance(
        S_total=80000,
        site_area=20000,
        N_rooms=400,
        N_hotelF=15,
        N_officeF=20,
        N_podiumF=4
    )
    print_report(r3)
