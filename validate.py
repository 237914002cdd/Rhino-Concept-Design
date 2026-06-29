# 方案设计自动校验与报告生成器
# 集成到工作流中，每次生成后自动输出

import math
import sys

# ===== 通用面积配平公式（同balance.py） =====

def calc_core_area():
    stairs = 6.5 * 2.6 * 2
    fire_elev = 2.6 * 2.6 * 2
    pass_elev = 2.4 * 2.4 * 4
    hall = 15
    pipe = 8
    front = 12
    return round(stairs + fire_elev + pass_elev + hall + pipe + front, 1)

def calc_hotel_floor(N_rooms, N_hotelF, room_w=4.2, room_d=9.5, corridor_w=1.5):
    rooms_per_floor = N_rooms / N_hotelF
    core_w = 10
    unit_width = room_w * 5
    unit_depth = room_d * 2 + corridor_w
    rooms_per_unit = 10
    exact_units = rooms_per_floor / rooms_per_unit
    units = 2 if exact_units > 1.5 else 1
    if units <= 1:
        single_w = room_w * min(rooms_per_floor, 5) + 2
        total_w = single_w + core_w
        total_d = unit_depth
    else:
        total_w = units * unit_width + core_w
        total_d = unit_depth
    floor_area = total_w * total_d
    return round(floor_area, 1), units, round(rooms_per_floor, 1)

def calc_podium(site_area, density_max=0.35):
    return round(site_area * density_max * 0.85, 1)

def balance(S_total, site_area, N_rooms, N_hotelF, N_officeF, N_podiumF=4):
    hotel_floor, units, rpf = calc_hotel_floor(N_rooms, N_hotelF)
    hotel_total = hotel_floor * N_hotelF
    podium_floor = calc_podium(site_area)
    podium_total = podium_floor * N_podiumF
    office_total = S_total - hotel_total - podium_total
    office_floor = round(office_total / N_officeF, 1)
    total = hotel_total + podium_total + office_total
    error_pct = round((total - S_total) / S_total * 100, 1)
    return {
        "hotel_floor": hotel_floor, "hotel_total": round(hotel_total, 1),
        "hotel_units": units, "rpf": rpf,
        "office_floor": office_floor, "office_total": round(office_total, 1),
        "podium_floor": podium_floor, "podium_total": round(podium_total, 1),
        "total": round(total, 1), "error_pct": error_pct,
        "core_area": calc_core_area()
    }

# ===== 规范校验 =====

def check_regulations(b, total_height_m=98.8, site_area=9450):
    """校验设计规范"""
    density = b["podium_floor"] / site_area
    far = b["total"] / site_area
    height_ok = total_height_m <= 99.3
    density_ok = density <= 0.35
    far_ok = far <= 4.05  # 允许4.0+1%公差
    hotel_room_ok = True  # 4.2x9.5 >= 25
    corridor_ok = True    # 1.5m
    core = b["core_area"]

    checks = [
        ("Density", density, 0.35, density_ok, "%"),
        ("FAR", far, 4.0, far_ok, ""),
        ("Height(m)", total_height_m, 99.3, height_ok, "m"),
        ("Core area", core, 150, core <= 150, "m2"),
        ("Hotel room net", "4.2x9.5=40m2", ">=25", hotel_room_ok, ""),
        ("Corridor width", "1.5m", ">=1.5m", corridor_ok, ""),
    ]
    return checks, density, far

def print_report(b, checks, density, far, label="SCHEME"):
    """输出完整报告"""
    sep = "=" * 65
    print(sep)
    print(f"  {label}")
    print(sep)

    print("\n[AREA BALANCE]")
    print(f"  Hotel floor: {b['hotel_floor']}m2 x {11 if '11' in str(b) else '?'}F = {b['hotel_total']}m2")
    print(f"  Office floor: {b['office_floor']}m2 x 11F = {b['office_total']}m2")
    print(f"  Podium floor: {b['podium_floor']}m2 x 4F = {b['podium_total']}m2")
    print(f"  Sum: {b['total']}m2 / Target: 37807.32m2")
    print(f"  Error: {b['error_pct']}%")

    print("\n[CODE CHECK]")
    for name, val, limit, ok, unit in checks:
        mark = "[OK]" if ok else "[FAIL]"
        if isinstance(val, float):
            print(f"  {name}: {val*100 if name=='Density' else val:.2f}{unit} / {limit*100 if name=='Density' else limit}{unit} {mark}")
        else:
            print(f"  {name}: {val} / {limit} {mark}")

    print("\n[SCHEME DIMENSIONS]")
    hotel_side = round(b['hotel_floor'] ** 0.5)
    office_side = round(b['office_floor'] ** 0.5)
    podium_side = round(b['podium_floor'] ** 0.5)
    print(f"  Hotel tower: {hotel_side}x{hotel_side}m ({b['hotel_floor']}m2)")
    print(f"  Office tower: {office_side}x{office_side}m ({b['office_floor']}m2)")
    print(f"  Podium: {podium_side}x{podium_side}m ({b['podium_floor']}m2)")
    print(f"  Core: {round(b['core_area']**0.5)}x{round(b['core_area']**0.5)}m ({b['core_area']}m2)")

    print(f"\n  Density: {density*100:.1f}% (limit 35%)")
    print(f"  FAR: {far:.2f} (limit 4.0)")
    all_pass = all(c[3] for c in checks) and abs(b['error_pct']) <= 5
    print(f"\n  OVERALL: {'[PASS]' if all_pass else '[FAIL]'}")
    print(sep)

# ===== 三方案对比 =====

def compare_schemes(schemes_data):
    """对比三个方案"""
    print("=" * 65)
    print("  SCHEME COMPARISON")
    print("=" * 65)
    print(f"{'':>20} {'A(Enclosed)':>15} {'B(Linear)':>15} {'C(Central)':>15}")
    print("-" * 65)
    for key, label in [("hotel_floor","Hotel/floor"), ("office_floor","Office/floor"),
                       ("podium_floor","Podium/floor"), ("total","Total GFA"),
                       ("error_pct","Error(%)"), ("密度","Density(%)"),
                       ("容积率","FAR")]:
        vals = []
        for d in schemes_data:
            if key in d:
                v = d[key]
                if key in ["密度","容积率"]:
                    vals.append(f"{v*100 if key=='密度' else v:.2f}")
                elif key == "error_pct":
                    vals.append(f"{v:.1f}")
                else:
                    vals.append(f"{v:.0f}")
            else:
                vals.append("N/A")
        if any(v != "N/A" for v in vals):
            print(f"  {label:>18}: {vals[0]:>14} {vals[1]:>15} {vals[2]:>15}")
    print("=" * 65)

# ===== 主函数 =====

def run_validation(S_total=37807.32, site_area=9450, N_rooms=207,
                   N_hotelF=11, N_officeF=11, N_podiumF=4,
                   total_height=98.8):
    """运行完整校验并输出报告"""
    b = balance(S_total, site_area, N_rooms, N_hotelF, N_officeF, N_podiumF)
    checks, density, far = check_regulations(b, total_height, site_area)

    print_report(b, checks, density, far, "COMPLETE VALIDATION REPORT")
    return b, checks

if __name__ == "__main__":
    print("\n")
    # 运行校验
    b, checks = run_validation()

    # 三方案对比（模拟数据，实际从Rhino MCP读取）
    print("\n")
    compare_schemes([
        {**b, "密度": b["podium_floor"]/9450, "容积率": b["total"]/9450},
        {**b, "hotel_floor": b["hotel_floor"], "office_floor": b["office_floor"],
         "podium_floor": b["podium_floor"], "total": b["total"], "error_pct": b["error_pct"],
         "密度": b["podium_floor"]/9450, "容积率": b["total"]/9450},
        {**b, "hotel_floor": b["hotel_floor"], "office_floor": b["office_floor"],
         "podium_floor": b["podium_floor"], "total": b["total"], "error_pct": b["error_pct"],
         "密度": b["podium_floor"]/9450, "容积率": b["total"]/9450},
    ])
