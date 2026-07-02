"""
rhino_gen.py — RhinoMCP 方案体块自动生成

读取 project_config.json → 计算组团体块 → 按方案规则调整 → 通过 RhinoMCP 创建体块

用法:
    python rhino_gen.py                  # 生成全部三个方案
    python rhino_gen.py --scheme B       # 仅生成方案 B
    python rhino_gen.py --dry-run        # 仅输出坐标，不连接 Rhino

依赖: Rhino 8 须已运行并执行 mcpstart 命令
"""

import json
import os
import sys
import subprocess
import time

# ── 项目路径 ──
SCRIPT_DIR = os.path.dirname(__file__)
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, "项目模板", "AI_Consultant_Project_Template")
CONFIG_PATH = os.path.join(TEMPLATE_DIR, "project_config.json")

# ── 导入验证模块的组团体块计算 ──
sys.path.insert(0, SCRIPT_DIR)
from validate import read_project_config, expand_floor_targets, compute_block_dimensions


# ── 颜色映射（RGB） ──
COLORS = {
    "lobby":       (0, 150, 230),    # 蓝
    "recreation":  (180, 100, 200),  # 紫
    "dining":      (232, 168, 56),   # 橙
    "conference":  (0, 100, 180),    # 深蓝
    "office":      (74, 217, 163),   # 绿
    "guestroom_entertainment": (180, 100, 200),  # 紫
    "guestroom":   (232, 168, 56),   # 橙
    "sky_lounge":  (180, 100, 200),  # 紫
    "core":        (155, 155, 155),  # 灰
    "site_redline":   (255, 0, 0),   # 红
    "site_setback":   (255, 165, 0), # 橙
}


def load_blocks():
    """从 project_config.json 计算组团体块"""
    config = read_project_config(CONFIG_PATH)
    if not config:
        print("[ERROR] project_config.json not found.")
        return None, None
    blocks = compute_block_dimensions(config)
    return config, blocks


def build_site_objects(ox, oy, config):
    """生成场地信息：红线 + 退线 + 标注"""
    site = config.get("site", {})
    sx = site.get("site_width_m", 80)
    sy = site.get("site_depth_m", 120)
    # 退线
    se = site.get("setback_east_m", 15)
    sw = site.get("setback_west_m", 10)
    sn = site.get("setback_north_m", 8)
    ss = site.get("setback_south_m", 8)

    objects = []

    # 红线（假设矩形场地）
    redline = [
        [ox, oy, 0],
        [ox + (sx or 80), oy, 0],
        [ox + (sx or 80), oy + (sy or 120), 0],
        [ox, oy + (sy or 120), 0],
        [ox, oy, 0],
    ]
    objects.append({
        "type": "POLYLINE",
        "name": "红线",
        "color": COLORS["site_redline"],
        "params": {"points": [[p[0]*1000, p[1]*1000, 0] for p in redline]},  # m→mm
    })

    # 退线
    bline = [
        [ox + se, oy + ss, 0],
        [ox + (sx or 80) - sw, oy + ss, 0],
        [ox + (sx or 80) - sw, oy + (sy or 120) - sn, 0],
        [ox + se, oy + (sy or 120) - sn, 0],
        [ox + se, oy + ss, 0],
    ]
    objects.append({
        "type": "POLYLINE",
        "name": "退线",
        "color": COLORS["site_setback"],
        "params": {"points": [[p[0]*1000, p[1]*1000, 0] for p in bline]},
    })

    return objects


def build_scheme_A(blocks, ox, oy):
    """方案 A：围合内院式（基线方案，直接使用 block dimensions 值）"""
    objs = []
    core_w, core_d = 10, 10.4  # 核心筒

    for b in blocks:
        w_m = b["width_m"]
        d_m = b["depth_m"]
        z0 = b["z_base_m"]
        z1 = b["z_top_m"]
        h = b["height_m"]

        color = COLORS.get(b["function"], (200, 200, 200))

        objs.append({
            "type": "BOX",
            "name": f"A_{b['function']}_{b['floor_count']}F",
            "color": color,
            "params": {
                "width": w_m * 1000,
                "length": d_m * 1000,
                "height": h * 1000,
            },
            "translation": [ox * 1000, oy * 1000, z0 * 1000],
        })

        # 核心筒（仅加在塔楼组团上）
        if b["function"] in ("office", "guestroom", "guestroom_entertainment", "sky_lounge"):
            objs.append({
                "type": "BOX",
                "name": f"A_核心筒_{b['function']}",
                "color": COLORS["core"],
                "params": {
                    "width": core_w * 1000,
                    "length": core_d * 1000,
                    "height": h * 1000,
                },
                "translation": [
                    (ox + w_m / 2 - core_w / 2) * 1000,
                    (oy + d_m / 2 - core_d / 2) * 1000,
                    z0 * 1000,
                ],
            })

    return objs


def build_scheme_B(blocks, ox, oy, config):
    """方案 B：Terrace 城市绿毯（V3.0 规则十）

    规则:
    - 东南角锁定，东/南 1F-26F 垂直平齐
    - 塔楼长宽比 ≥1.6:1
    - 4F 顶向西深退台 ≥15m（组团叠落）
    """
    objs = []
    core_w, core_d = 10, 10.4
    site = config.get("site", {})

    # 东/南退线作为锁定边界
    se = site.get("setback_east_m", 15)

    for b in blocks:
        w_m = b["width_m"]
        d_m = b["depth_m"]
        z0 = b["z_base_m"]
        z1 = b["z_top_m"]
        h = b["height_m"]
        func = b["function"]
        color = COLORS.get(func, (200, 200, 200))

        # 东南角锁定：体块东南角对齐退线交点
        # 裙房（1F-4F）保持原尺寸
        # 办公/客房（5F-25F）西侧缩进，使长宽比≥1.6:1
        if func in ("office", "guestroom", "guestroom_entertainment"):
            # 塔楼：压缩宽度使长宽比≥1.6
            new_w = d_m / 1.6  # w = d / aspect_ratio
            offset_x = w_m - new_w  # 东侧不动，西侧缩进
            w_use = new_w
        elif func == "sky_lounge":
            w_use = w_m * 0.92
            offset_x = w_m - w_use
        else:
            w_use = w_m
            offset_x = 0

        objs.append({
            "type": "BOX",
            "name": f"B_{func}_{b['floor_count']}F",
            "color": color,
            "params": {
                "width": w_use * 1000,
                "length": d_m * 1000,
                "height": h * 1000,
            },
            "translation": [
                (ox + offset_x) * 1000,
                oy * 1000,
                z0 * 1000,
            ],
        })

        # 核心筒
        if func in ("office", "guestroom", "guestroom_entertainment", "sky_lounge"):
            objs.append({
                "type": "BOX",
                "name": f"B_核心筒_{func}",
                "color": COLORS["core"],
                "params": {
                    "width": core_w * 1000,
                    "length": core_d * 1000,
                    "height": h * 1000,
                },
                "translation": [
                    (ox + offset_x + w_use / 2 - core_w / 2) * 1000,
                    (oy + d_m / 2 - core_d / 2) * 1000,
                    z0 * 1000,
                ],
            })

    return objs


def build_scheme_C(blocks, ox, oy, config):
    """方案 C：Interlock 极简双折体（V3.0 规则十）

    规则:
    - 5F-25F（含16F）完全合并为完整晶体
    - 晶体与 1F-4F 基座错位咬合
    - 26F 沿主干道单向悬挑 ≥6.0m
    """
    objs = []
    core_w, core_d = 10, 10.4
    site = config.get("site", {})

    # 把 5F-25F 合并为一个晶体
    crystal_w = 0
    crystal_d = 0
    crystal_z0 = 1000
    crystal_z1 = 0
    crystal_color = COLORS.get("office", (74, 217, 163))

    for b in blocks:
        func = b["function"]
        w_m = b["width_m"]
        d_m = b["depth_m"]
        z0 = b["z_base_m"]
        z1 = b["z_top_m"]
        h = b["height_m"]
        color = COLORS.get(func, (200, 200, 200))

        if func in ("office", "guestroom", "guestroom_entertainment"):
            # 合并到晶体：取最大宽/深
            crystal_w = max(crystal_w, w_m)
            crystal_d = max(crystal_d, d_m)
            crystal_z0 = min(crystal_z0, z0)
            crystal_z1 = max(crystal_z1, z1)
            continue  # 跳过单独生成

        if func == "sky_lounge":
            # 26F 云顶：悬挑 ≥6m
            cantilever = 6.0
            w_use = w_m + cantilever
            offset_base = -cantilever / 2  # 向主干道方向偏移
        else:
            w_use = w_m
            offset_base = 0

        objs.append({
            "type": "BOX",
            "name": f"C_{func}_{b['floor_count']}F",
            "color": color,
            "params": {
                "width": w_use * 1000,
                "length": d_m * 1000,
                "height": h * 1000,
            },
            "translation": [
                (ox + offset_base) * 1000,
                oy * 1000,
                z0 * 1000,
            ],
        })

        if func == "sky_lounge":
            core_h = h
        elif func in ("lobby", "recreation", "dining", "conference"):
            core_h = h
        else:
            core_h = 0

    # 生成合并晶体
    if crystal_z1 > crystal_z0:
        crystal_h = crystal_z1 - crystal_z0
        # 晶体与基座错位：向西南方向偏移 3m
        offset_x = -3.0
        offset_y = -3.0
        objs.append({
            "type": "BOX",
            "name": "C_晶体塔楼_5-25F",
            "color": crystal_color,
            "params": {
                "width": crystal_w * 1000,
                "length": crystal_d * 1000,
                "height": crystal_h * 1000,
            },
            "translation": [
                (ox + offset_x) * 1000,
                (oy + offset_y) * 1000,
                crystal_z0 * 1000,
            ],
        })
        # 晶体的核心筒
        objs.append({
            "type": "BOX",
            "name": "C_核心筒_晶体",
            "color": COLORS["core"],
            "params": {
                "width": core_w * 1000,
                "length": core_d * 1000,
                "height": crystal_h * 1000,
            },
            "translation": [
                (ox + offset_x + crystal_w / 2 - core_w / 2) * 1000,
                (oy + offset_y + crystal_d / 2 - core_d / 2) * 1000,
                crystal_z0 * 1000,
            ],
        })

    return objs


def generate(ox_base=0, oy_base=0, schemes=("A", "B", "C"), dry_run=False):
    """主生成函数"""
    config, blocks = load_blocks()
    if not blocks:
        return

    print(f"Loaded {len(blocks)} blocks from {config.get('project_name', 'project')}")
    print(f"Scheme offsets: X={ox_base}m (per scheme spacing 120m)")
    print(f"Dry run: {dry_run}")
    print()

    all_objects = []
    scheme_spacing = 120  # 方案间距 120m

    for i, scheme in enumerate(schemes):
        ox = ox_base + i * scheme_spacing
        oy = oy_base
        print(f"── Scheme {scheme} @ X={ox}m ──")

        # 场地信息（红线+退线）
        site_objs = build_site_objects(ox, oy, config)
        all_objects.extend(site_objs)
        print(f"  Site objects: {len(site_objs)}")

        # 方案体块
        if scheme == "A":
            objs = build_scheme_A(blocks, ox, oy)
        elif scheme == "B":
            objs = build_scheme_B(blocks, ox, oy, config)
        elif scheme == "C":
            objs = build_scheme_C(blocks, ox, oy, config)

        all_objects.extend(objs)
        print(f"  Massing blocks: {len(objs)}")

        # 汇总每个组块的面积
        for o in objs:
            if o["type"] == "BOX":
                w = o["params"]["width"] / 1000
                d = o["params"]["length"] / 1000
                area = w * d
                print(f"    {o['name']}: {w:.1f}m x {d:.1f}m = {area:.1f}㎡")

        print()

    print(f"Total objects: {len(all_objects)}")

    if dry_run:
        return all_objects

    # 连接 RhinoMCP 并生成
    send_to_rhino(all_objects)
    return all_objects


def send_to_rhino(objects):
    """通过 RhinoMCP JSON-RPC 协议创建体块"""
    # uvx 路径
    uvx_path = "D:/claude code mode/Python312/Scripts/uvx.exe"
    if not os.path.exists(uvx_path):
        uvx_path = "uvx"
    cmd = [uvx_path, "rhinomcp"]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    msg_id = 1

    def send(method, params=None):
        nonlocal msg_id
        msg = {"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params or {}}
        msg_id += 1
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()

    def recv(timeout_s=5):
        import select
        import socket
        start = time.time()
        while time.time() - start < timeout_s:
            line = proc.stdout.readline()
            if line:
                try:
                    return json.loads(line.strip())
                except:
                    return {"raw": line.strip()}
        return None

    # Initialize
    send("initialize", {
        "protocolVersion": "2024-11-05",
        "client": {"name": "rhino_gen", "version": "1.0"},
        "capabilities": {},
    })
    r = recv()
    if not r:
        print("[ERROR] RhinoMCP not responding. Is Rhino 8 running with mcpstart?")
        proc.terminate()
        return

    print(f"Connected: {json.dumps(r, ensure_ascii=False)[:100]}")

    # Initialized notification
    send("notifications/initialized")
    time.sleep(1)

    # Batch create all objects
    # 由于 create_objects 一次接收多个，分批发送（每批最多 50 个）
    batch_size = 50
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i + batch_size]
        send("tools/call", {
            "name": "create_objects",
            "arguments": {"objects": batch},
        })
        r = recv()
        if r:
            print(f"  Batch {i//batch_size + 1}: {len(batch)} objects -> OK")
        else:
            print(f"  Batch {i//batch_size + 1}: {len(batch)} objects -> TIMEOUT")

    # Screenshot
    send("tools/call", {
        "name": "capture_viewport",
        "arguments": {"viewport": "perspective", "width": 1600, "height": 1000, "zoom_to_fit": True},
    })
    r = recv()
    if r:
        print(f"Screenshot captured")

    print(f"\n[DONE] {len(objects)} objects created in Rhino.")
    proc.terminate()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="RhinoMCP 方案体块自动生成")
    parser.add_argument("--scheme", choices=["A", "B", "C", "all"], default="all",
                        help="生成指定方案（默认 all）")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅输出坐标，不连接 Rhino")
    parser.add_argument("--ox", type=float, default=0,
                        help="起始 X 偏移（m）")
    parser.add_argument("--oy", type=float, default=0,
                        help="起始 Y 偏移（m）")
    args = parser.parse_args()

    schemes = ("A", "B", "C") if args.scheme == "all" else (args.scheme,)
    generate(ox_base=args.ox, oy_base=args.oy, schemes=schemes, dry_run=args.dry_run)
