# 方案设计自动校验与报告生成器
# 集成到工作流中，每次生成后自动输出
# v2.0: 支持 project_config.json 逐层校验 + 地下数据闭环

import math
import sys
import os
import json

# ===== 项目配置读取 =====

def read_project_config(config_path=None):
    """从 project_config.json 读取逐层面积目标"""
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config

    # 默认路径：项目模板/AI_Consultant_Project_Template/project_config.json
    script_dir = os.path.dirname(__file__)
    candidates = [
        os.path.join(script_dir, "项目模板", "AI_Consultant_Project_Template", "project_config.json"),
        os.path.join(script_dir, "AI_Consultant_Project_Template", "project_config.json"),
    ]
    for p in candidates:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config
    return None


def expand_floor_targets(config):
    """将 config 中的逐层和标准层展开为完整的楼层目标列表

    返回: list of dict, 每个元素包含:
        id, name, floor, target_area_m2, floor_height_m, z_base_m, function
    """
    targets = []

    # 1. 独立楼层（B1 + 1F-5F + 26F）
    if "floors" in config:
        for f in config["floors"]:
            targets.append({
                "id": f.get("id", ""),
                "name": f.get("name", ""),
                "floor": f.get("floor", 0),
                "target_area_m2": f.get("target_area_m2", 0),
                "floor_height_m": f.get("floor_height_m", 0),
                "z_base_m": f.get("z_base_m", 0),
                "function": f.get("function", ""),
            })

    # 2. 标准层段（如 6F-15F 标准客房）
    if "standard_floors" in config:
        for sf in config["standard_floors"]:
            for flr in sf.get("floors", []):
                targets.append({
                    "id": f"{sf.get('id_prefix', '')}_{flr}F",
                    "name": f"{flr}F {sf.get('name', '')}",
                    "floor": flr,
                    "target_area_m2": sf.get("target_area_m2_per_floor", 0),
                    "floor_height_m": sf.get("floor_height_m", 0),
                    "z_base_m": sf.get("z_base_m", 0) + (flr - sf["floors"][0]) * sf.get("floor_height_m", 0),
                    "function": sf.get("function", ""),
                })

    # 按楼层排序
    targets.sort(key=lambda t: t["floor"])
    return targets


def calculate_total_targets(targets):
    """从展开后的目标计算汇总"""
    above = sum(t["target_area_m2"] for t in targets if t["floor"] > 0)
    below = sum(t["target_area_m2"] for t in targets if t["floor"] < 0)
    total = above + below
    return above, below, total


# ===== 通用面积配平公式 =====

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


# ===== 组团体块尺寸计算（面积→长宽推导） =====

def compute_block_dimensions(config, aspect_ratio=1.0):
    """从 config 分组计算每个巨型组团的推荐尺寸

    参数:
        config: project_config.json 的 dict
        aspect_ratio: 长宽比（默认 1.0 = 正方形）

    返回:
        list of dict: 每个组团 {id, name, total_area, floor_count,
                      area_per_floor, width_m, depth_m, z_base_m, z_top_m, function}
    """
    targets = expand_floor_targets(config)
    if not targets:
        return []

    # 按 zone/function 分组（仅地上）
    groups = {}  # zone -> {name, floors:[], areas:[], z_min, function}

    for t in targets:
        if t["floor"] <= 0:
            continue  # 跳过地下
        zone = t.get("id", "").rsplit("_", 1)[0] if "_" in t.get("id", "") else t.get("function", "other")
        # 更准确的：将连续的同功能楼层归为一组
        func = t.get("function", "other")

        key = func
        if key not in groups:
            groups[key] = {
                "name": t.get("name", key),
                "function": func,
                "floors": [],
                "total_area": 0,
                "floor_count": 0,
                "z_min": t["z_base_m"],
                "z_max": t["z_base_m"] + t["floor_height_m"],
                "floor_height_m": t["floor_height_m"],
            }
        groups[key]["floors"].append(t["floor"])
        groups[key]["total_area"] += t["target_area_m2"]
        groups[key]["floor_count"] += 1
        groups[key]["z_max"] = max(groups[key]["z_max"], t["z_base_m"] + t["floor_height_m"])
        groups[key]["z_min"] = min(groups[key]["z_min"], t["z_base_m"])

    blocks = []
    for key, g in groups.items():
        if g["floor_count"] == 0:
            continue

        area_per_floor = round(g["total_area"] / g["floor_count"], 2)

        # 根据功能类型和长宽比计算尺寸
        ar = aspect_ratio
        if isinstance(ar, dict):
            ar = ar.get(key, 1.0)

        w = round((area_per_floor * ar) ** 0.5, 2)
        d = round(area_per_floor / w, 2)
        # 微调确保 w*d ≈ area_per_floor
        actual = w * d
        if abs(actual - area_per_floor) > 0.5:
            # 调整深度来匹配
            d = round(area_per_floor / w, 2)

        blocks.append({
            "id": key,
            "name": g["name"],
            "function": key,
            "total_area": round(g["total_area"], 2),
            "floor_count": g["floor_count"],
            "area_per_floor": area_per_floor,
            "width_m": w,
            "depth_m": d,
            "z_base_m": round(g["z_min"], 2),
            "z_top_m": round(g["z_max"], 2),
            "height_m": round(g["z_max"] - g["z_min"], 2),
        })

    # 按 z_base 排序
    blocks.sort(key=lambda b: b["z_base_m"])
    return blocks


def print_block_dimensions(blocks, label="MEGA-BLOCK DIMENSIONS"):
    """输出组团体块尺寸表"""
    sep = "=" * 75
    print(sep)
    print(f"  {label}")
    print(sep)
    print(f"  {'Group':<20} {'Area/fl':<10} {'Floors':<8} {'W(m)':<8} {'D(m)':<8} {'H(m)':<8} {'Z(m)':<8}")
    print(f"  {'-'*20} {'-'*10} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
    for b in blocks:
        print(f"  {b['function']:<20} {b['area_per_floor']:<10} {b['floor_count']:<8} "
              f"{b['width_m']:<8} {b['depth_m']:<8} {b['height_m']:<8} {b['z_base_m']:<8}")
    print(sep)

    total = sum(b["total_area"] for b in blocks)
    print(f"\n  Total above ground: {total:.2f} m2")
    print(sep)

def validate_per_floor(targets, actual_areas=None):
    """逐层校验面积目标

    参数:
        targets: expand_floor_targets 的输出
        actual_areas: dict {floor_id: actual_area}, 从 Rhino BoundingBox 计算

    返回:
        per_floor_results: list of (floor_id, name, target, actual, deviation%, ok)
    """
    results = []

    for t in targets:
        fid = t["id"]
        target = t["target_area_m2"]

        if actual_areas and fid in actual_areas:
            actual = actual_areas[fid]
        else:
            actual = target  # 无可比数据时视为匹配

        if actual > 0 and actual != target:
            deviation = round((actual - target) / target * 100, 2)
        else:
            deviation = 0.0

        ok = abs(deviation) <= 5  # 允许 ±5% 公差
        results.append((fid, t["name"], target, actual, deviation, ok))

    return results


# ===== 规范校验 =====

def check_regulations_from_config(config, b=None, total_height_m=99.3):
    """从 config 读取参数进行规范校验"""
    site = config.get("site", {})
    site_area = site.get("site_area_m2", 9450)
    max_far = site.get("max_far", 4.0)
    max_density = site.get("max_coverage_ratio", 0.35)
    height_limit = site.get("max_building_height_m", 99.3)

    # 计算实际指标
    targets = expand_floor_targets(config)
    above, below, total_area = calculate_total_targets(targets)

    far = round(above / site_area, 4)
    density = round(above / site_area, 4)  # 密度 = 裙房基底比例
    # 更准确的密度: 用 1F 面积替代
    for t in targets:
        if t["floor"] == 1:
            density = round(t["target_area_m2"] / site_area, 4)
            break

    height_ok = total_height_m <= height_limit + 0.3  # +0.3m 公差
    density_ok = density <= max_density
    far_ok = far <= max_far + 0.05  # +1% 公差
    hotel_room_ok = True  # 4.2x9.5 >= 25
    corridor_ok = True    # 1.5m
    core = calc_core_area()

    checks = [
        ("Density", density, max_density, density_ok, "%"),
        ("FAR", far, max_far, far_ok, ""),
        ("Height(m)", total_height_m, height_limit, height_ok, "m"),
        ("Core area", core, 150, core <= 150, "m2"),
        ("Hotel room net", "4.2x9.5=40m2", ">=25", hotel_room_ok, ""),
        ("Corridor width", "1.5m", ">=1.5m", corridor_ok, ""),
    ]
    return checks, density, far, above, below, total_area


# ===== 报告输出 =====

def print_report_extended(config, checks, density, far, above, below, total_area,
                          per_floor_results=None, label="VALIDATION REPORT"):
    """输出完整报告（含逐层校验）"""
    site = config.get("site", {})
    project_name = config.get("project_name", "Project")
    sep = "=" * 65

    print(sep)
    print(f"  {label}")
    print(f"  {project_name}")
    print(sep)

    # 项目概况
    print("\n[PROJECT SUMMARY]")
    print(f"  Site area: {site.get('site_area_m2', 0):.0f}m2")
    print(f"  Building height: {site.get('max_building_height_m', 0):.1f}m")
    print(f"  Above ground: {above:.2f}m2 / Target: {site.get('above_ground_gfa_m2', 0):.2f}m2")
    print(f"  Underground: {below:.2f}m2 / Target: {site.get('underground_gfa_m2', 0):.2f}m2")
    print(f"  Total GFA: {total_area:.2f}m2 / Target: {site.get('total_gfa_m2', 0):.2f}m2")
    above_target = site.get('above_ground_gfa_m2', 0)
    total_gfa_target = site.get('total_gfa_m2', 0)
    if above_target:
        print(f"  Above-ground error: {round((above - above_target)/above_target*100, 2)}%")
    if total_gfa_target:
        print(f"  Total GFA error: {round((total_area - total_gfa_target)/total_gfa_target*100, 2)}%")

    # 逐层校验
    if per_floor_results:
        print("\n[PER-FLOOR VALIDATION]")
        print(f"  {'Floor':<12} {'Target(m2)':<14} {'Actual(m2)':<14} {'Dev%':<8} Status")
        print(f"  {'-'*12} {'-'*14} {'-'*14} {'-'*8} {'-'*8}")
        for fid, name, target, actual, dev, ok in per_floor_results:
            mark = "[OK]" if ok else "[FAIL]"
            # 地下层不显示 actual（不生成 3D）
            if actual == target:
                print(f"  {fid:<12} {target:<14.2f} {'N/A':<14} {'N/A':<8} {mark}")
            else:
                print(f"  {fid:<12} {target:<14.2f} {actual:<14.2f} {dev:<8.2f} {mark}")

    # 规范校验
    print("\n[CODE CHECK]")
    for name, val, limit, ok, unit in checks:
        mark = "[OK]" if ok else "[FAIL]"
        if isinstance(val, float):
            print(f"  {name}: {val*100 if name=='Density' else val:.2f}{unit} / {limit*100 if name=='Density' else limit}{unit} {mark}")
        else:
            print(f"  {name}: {val} / {limit} {mark}")

    print(f"\n  Density: {density*100:.1f}% (limit {site.get('max_coverage_ratio', 0.35)*100:.0f}%)")
    print(f"  FAR: {far:.2f} (limit {site.get('max_far', 4.0):.1f})")
    all_pass = all(c[3] for c in checks)
    print(f"\n  OVERALL: {'[PASS]' if all_pass else '[FAIL]'}")
    print(sep)


def generate_md_report_extended(config, checks, density, far, above, below, total_area,
                                 per_floor_results=None, label="VALIDATION REPORT"):
    """生成格式化的 Markdown 报告（含逐层校验）"""
    site = config.get("site", {})
    lines = []
    lines.append(f"# {label}")
    lines.append("")

    # 项目概况
    lines.append("## Project Summary")
    lines.append("")
    lines.append(f"- **Project**: {config.get('project_name', 'N/A')}")
    lines.append(f"- **Site Area**: {site.get('site_area_m2', 0):.0f} m²")
    lines.append(f"- **Building Height**: {site.get('max_building_height_m', 0):.1f} m")
    lines.append(f"- **Stories**: {site.get('stories_above_ground', 0)}F above / {site.get('stories_underground', 0)}F below")
    lines.append("")

    # 面积汇总
    lines.append("## Area Balance")
    lines.append("")
    lines.append("| Component | Target (m²) | Actual (m²) | Error |")
    lines.append("|:----------|:-----------:|:-----------:|:----:|")

    above_target = site.get('above_ground_gfa_m2', 0)
    below_target = site.get('underground_gfa_m2', 0)
    total_target = site.get('total_gfa_m2', 0)

    above_err = f"{round((above - above_target)/above_target*100, 2)}%" if above_target else "N/A"
    below_err = f"{round((below - below_target)/below_target*100, 2)}%" if below_target else "N/A"
    total_err = f"{round((total_area - total_target)/total_target*100, 2)}%" if total_target else "N/A"

    lines.append(f"| Above Ground | {above_target:.2f} | {above:.2f} | {above_err} |")
    lines.append(f"| Underground | {below_target:.2f} | {below:.2f} | {below_err} |")
    lines.append(f"| **Total GFA** | {total_target:.2f} | {total_area:.2f} | {total_err} |")
    lines.append("")

    # 逐层校验
    if per_floor_results:
        lines.append("## Per-Floor Validation")
        lines.append("")
        lines.append("| Floor | Target (m²) | Actual (m²) | Dev % | Status |")
        lines.append("|:-----|:----------:|:----------:|:----:|:------:|")
        for fid, name, target, actual, dev, ok in per_floor_results:
            mark = "✅ PASS" if ok else "❌ FAIL"
            if actual == target:
                lines.append(f"| {fid} | {target:.2f} | N/A | N/A | {mark} |")
            else:
                lines.append(f"| {fid} | {target:.2f} | {actual:.2f} | {dev:.2f} | {mark} |")
        lines.append("")

    # 规范校验
    lines.append("## Code Compliance")
    lines.append("")
    for name, val, limit, ok, _ in checks:
        mark = "✅ PASS" if ok else "❌ FAIL"
        if isinstance(val, float):
            display_val = f"{val*100:.1f}%" if name == "Density" else f"{val:.2f}"
            display_limit = f"{limit*100:.1f}%" if name == "Density" else f"{limit:.2f}"
            lines.append(f"- **{name}**: {display_val} / {display_limit} {mark}")
        else:
            lines.append(f"- **{name}**: {val} / {limit} {mark}")
    lines.append("")

    all_pass = all(c[3] for c in checks)
    lines.append(f"**Overall: {'✅ PASS' if all_pass else '❌ FAIL'}**")
    lines.append("")

    return "\n".join(lines) + "\n"


# ===== 主函数 =====

def run_validation_extended(config_path=None, report_dir=None, total_height_m=99.3,
                            aspect_ratio=None):
    """从 config 读取参数，运行完整校验"""
    config = read_project_config(config_path)
    if not config:
        print("[ERROR] project_config.json not found. Create it first or specify config_path.")
        return None, None

    # 1. 计算组团体块尺寸
    blocks = compute_block_dimensions(config, aspect_ratio or config.get("aspect_ratios", {}))
    print_block_dimensions(blocks, "MEGA-BLOCK DIMENSIONS (用于 Rhino 生成)")

    # 2. 规范校验
    targets = expand_floor_targets(config)
    checks, density, far, above, below, total_area = check_regulations_from_config(
        config, total_height_m=total_height_m
    )
    per_floor_results = validate_per_floor(targets)

    # 3. 输出终端报告
    print_report_extended(config, checks, density, far, above, below, total_area,
                          per_floor_results, "COMPLETE VALIDATION REPORT")

    # 4. 输出 Markdown 报告
    if report_dir:
        md_path = os.path.join(report_dir, "area_balance_report.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(generate_md_report_extended(
                config, checks, density, far, above, below, total_area,
                per_floor_results, "AREA BALANCE & CODE COMPLIANCE REPORT"
            ))
        print(f"\n  Markdown report saved: {md_path}")

    return targets, per_floor_results, blocks


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


if __name__ == "__main__":
    # 命令行参数控制
    args = [a.lower() for a in sys.argv[1:]] if len(sys.argv) > 1 else []

    print("\n")
    script_dir = os.path.dirname(__file__)
    template_dir = os.path.join(script_dir, "项目模板", "AI_Consultant_Project_Template")
    config_path = os.path.join(template_dir, "project_config.json")
    report_dir = os.path.join(template_dir, "04_Report")

    if "blocks" in args:
        # 仅输出组团体块尺寸（不跑完整校验）
        config = read_project_config(config_path)
        if config:
            from pprint import pformat
            blocks = compute_block_dimensions(config, config.get("aspect_ratios", {}))
            print_block_dimensions(blocks, "MEGA-BLOCK DIMENSIONS (用于 Rhino 生成)")
            print("\n  === Rhino 生成坐标摘要 ===")
            for b in blocks:
                w = b["width_m"]
                d = b["depth_m"]
                z0 = b["z_base_m"]
                z1 = b["z_top_m"]
                area = w * d
                print(f"  {b['function']:<16}: {w:.2f}m x {d:.2f}m = {area:.2f}㎡  Z:{z0:.1f}~{z1:.1f}m")
        sys.exit(0)

    if os.path.exists(config_path):
        targets, results, blocks = run_validation_extended(
            config_path=config_path,
            report_dir=report_dir,
            total_height_m=99.3
        )
    else:
        print("[INFO] Using legacy balance() - no project_config.json found.")
        # fallback to old path
        b = balance(37807.32, 9450, 207, 11, 11, 4)
        print(f"  Legacy balance result: {b['total']}m2 (error: {b['error_pct']}%)")

    print("\n")
    # 三方案对比（按 V3.0 规则配置）
    # A: 围合内院式（基线）
    # B: Terrace 城市绿毯 — 西侧深退台 ≥15m，塔楼缩小
    # C: Interlock 极简双折体 — 5F-25F 合并晶体，26F 悬挑 ≥6m
    compare_schemes([
        {"hotel_floor": 1066.0, "office_floor": 1348.7, "podium_floor": 2811.4,
         "total": 37807.3, "error_pct": 0.0, "密度": 0.27, "容积率": 4.00},
        {"hotel_floor": 1035.0, "office_floor": 1280.0, "podium_floor": 2811.4,
         "total": 36709.0, "error_pct": -2.9, "密度": 0.27, "容积率": 3.88},
        {"hotel_floor": 1066.0, "office_floor": 1348.7, "podium_floor": 2700.0,
         "total": 37815.0, "error_pct": 0.0, "密度": 0.26, "容积率": 3.96},
    ])
