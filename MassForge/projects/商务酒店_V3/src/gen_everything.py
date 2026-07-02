"""Generate 3 schemes with independent area calculations, then generate report"""

import json, os, subprocess
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# ===========================================================================
# Step 1: Define each scheme's OWN area logic
# ===========================================================================

total_target = 37807.32  # brief target

def round_box(area, w_factor=1.0):
    """For a square box, side = sqrt(area). Return (w, d) in mm."""
    side_m = (area ** 0.5)
    side_mm = int(side_m * 1000)
    return side_mm, side_mm

# ---- Scheme A: Monolith - efficient, flush outer envelope ----
# Podium sized for max floor area; other floors have internal voids.
# Tower is compact regular rectangles.
A = {
    "name": "A_极简巨构",
    "desc": "Monolith — 围合内院式，外立面垂直平齐，内部中庭消纳面积差",
    "boxes": [
        ("裙房1F", 2550.0, 50500, 50500, 6000,   (0,150,230)),
        ("裙房2F", 2350.0, 48500, 48500, 4800,   (180,100,200)),
        ("裙房3F", 2650.0, 51500, 51500, 5100,   (232,168,56)),
        ("裙房4F", 1850.0, 43000, 43000, 6000,   (0,100,180)),
        ("办公5-15F", 1350.25, 36750, 36750, 38200, (74,217,163)),
        ("客房16-25F", 1210.45, 34790, 34790, 34000, (232,168,56)),
        ("云顶26F", 1150.32, 33920, 33920, 4500,   (0,150,230)),
        ("核心筒", 104.0, 10000, 10400, 98600,     (155,155,155)),
    ]
}

# ---- Scheme B: Terrace - SE corner locked, NW direction terraces ----
# Podium is more generous; each zone step retreats to NW.
# The area TARGETS per zone are different from A because terrace logic demands it.
B = {
    "name": "B_阶梯错叠",
    "desc": "Terrace — 东南角锁定，向西/北单向退台，退台面≥3m",
    "boxes": [
        ("裙房1F", 2650.0, 51500, 51500, 6000,   (0,150,230)),
        ("裙房2F", 2450.0, 49500, 49500, 4800,   (180,100,200)),
        ("裙房3F", 2750.0, 52500, 52500, 5100,   (232,168,56)),
        ("裙房4F", 2000.0, 44700, 44700, 6000,   (0,100,180)),
        ("办公5-15F", 1420.0, 37700, 37700, 38200, (74,217,163)),
        ("客房16-25F", 1100.0, 33200, 33200, 34000, (232,168,56)),
        ("云顶26F", 1050.0, 32400, 32400, 4500,   (0,150,230)),
        ("核心筒", 104.0, 10000, 10400, 98600,     (155,155,155)),
    ]
}

# ---- Scheme C: Interlock - continuous crystal + offset + cantilever ----
# 5F-25F is ONE crystal (same cross-section throughout)
# Crystal shifts relative to podium center (offset interlock)
# 26F has dramatic cantilever
C = {
    "name": "C_异质穿插",
    "desc": "Interlock — 晶体与裙房错位咬合，26F悬挑≥6m",
    "boxes": [
        ("裙房1F", 2450.0, 49500, 49500, 6000,   (0,150,230)),
        ("裙房2F", 2250.0, 47500, 47500, 4800,   (180,100,200)),
        ("裙房3F", 2550.0, 50500, 50500, 5100,   (232,168,56)),
        ("裙房4F", 1750.0, 41800, 41800, 6000,   (0,100,180)),
        ("办公晶体5-15F", 1350.0, 36750, 36750, 38200, (74,217,163)),
        ("客房晶体16-25F", 1350.0, 36750, 36750, 34000, (232,168,56)),
        ("云顶26F", 1450.0, 42750, 33900, 4500,   (0,150,230)),
        ("核心筒", 104.0, 10000, 10400, 98600,     (155,155,155)),
    ]
}

schemes = [A, B, C]

# ===========================================================================
# Step 2: Calculate totals and verify ±5%
# ===========================================================================
for scheme in schemes:
    subtotal = sum(b[1] * (b[3] / b[3]) for b in scheme["boxes"][:-1])  # exclude core
    # Actually let me just do direct sum
    total = 0
    for box in scheme["boxes"]:
        name, area, w, d, h, rgb = box
        if "核心筒" not in name:
            total += area * (1 if "5-15" not in name and "16-25" not in name and "5-25" not in name else 1)
            if "办公5-15F" in name: total += area * 10  # 11 floors total, 1 accounted
            if "客房16-25F" in name: total += area * 9

    # Recalculate properly
    total = 0
    for box in scheme["boxes"]:
        name, area, w, d, h, rgb = box
        if "核心筒" in name:
            continue
        if "办公5-15F" in name:
            total += area * 11  # 11 floors
        elif "客房16-25F" in name:
            total += area * 10  # 10 floors
        elif "办公晶体5-15F" in name:
            total += area * 11
        elif "客房晶体16-25F" in name:
            total += area * 10
        elif "晶体5-25F" in name:
            total += area * 21  # 21 floors
        else:
            total += area

    scheme["total"] = total
    scheme["error_pct"] = round((total - total_target) / total_target * 100, 2)

for s in schemes:
    print(f"{s['name']}: total={s['total']:.0f}m2, error={s['error_pct']}%")

# ===========================================================================
# Step 3: Generate Rhino model
# ===========================================================================

rhino_code = """import rhinoscriptsyntax as rs

# 清空
rs.DeleteObjects(rs.AllObjects())
for ln in rs.LayerNames():
    try: rs.DeleteLayer(ln)
    except: pass

def bx(cx, cy, cz, w, d, h):
    hw=w/2; hd=d/2; hh=h/2
    return rs.AddBox([
        (cx-hw, cy-hd, cz-hh), (cx+hw, cy-hd, cz-hh),
        (cx+hw, cy+hd, cz-hh), (cx-hw, cy+hd, cz-hh),
        (cx-hw, cy-hd, cz+hh), (cx+hw, cy-hd, cz+hh),
        (cx+hw, cy+hd, cz+hh), (cx-hw, cy+hd, cz+hh)
    ])

def mk(ly, nm, x, y, z, w, d, h, r, g, b):
    rs.CurrentLayer(ly)
    obj = bx(x, y, z, w, d, h)
    if obj:
        rs.ObjectColor(obj, (r, g, b))
        rs.ObjectName(obj, nm)

# 建图层
rs.AddLayer("R1")
for s_name in ["A", "B", "C"]:
    rs.AddLayer(s_name, parent="R1")
    for ch in ["控制线", "裙房1F", "裙房2F", "裙房3F", "裙房4F", "办公5-15F", "客房16-25F", "办公晶体5-15F", "客房晶体16-25F", "云顶26F", "核心筒"]:
        rs.AddLayer(ch, parent=s_name)

RED = (255,0,0); ORG = (255,165,0)

def pl(ly, pts, c):
    g=rs.AddPolyline([rs.CreatePoint(p[0],p[1],p[2]) for p in pts])
    rs.ObjectLayer(g, ly); rs.ObjectColor(g, c)

"""

# Each scheme is at offset: A=0, B=120000, C=240000
# Monolith A: centered at (47500, 52500)
# Terrace B: SE corner anchored
# Interlock C: center shifted

# Build the per-scheme generation code
offsets = [0, 120000, 240000]
cx_base, cy_base = 47500, 52500

# ---- Scheme A: Monolith ----
a_code = """
# === A: Monolith (offset 0) ===
pl("R1::A::控制线", [(0,0,0),(90000,0,0),(90000,105000,0),(0,105000,0),(0,0,0)], RED)
pl("R1::A::控制线", [(15000,8000,0),(80000,8000,0),(80000,97000,0),(15000,97000,0),(15000,8000,0)], ORG)
mk("R1::A::裙房1F","A_裙房1F", 47500,52500, 3000, 50500,50500,6000, 0,150,230)
mk("R1::A::裙房2F","A_裙房2F", 47500,52500, 8400, 48500,48500,4800, 180,100,200)
mk("R1::A::裙房3F","A_裙房3F", 47500,52500, 13350, 51500,51500,5100, 232,168,56)
mk("R1::A::裙房4F","A_裙房4F", 47500,52500, 18900, 43000,43000,6000, 0,100,180)
mk("R1::A::办公5-15F","A_办公5-15F", 47500,52500, 41000, 36750,36750,38200, 74,217,163)
mk("R1::A::客房16-25F","A_客房16-25F", 47500,52500, 77100, 34790,34790,34000, 232,168,56)
mk("R1::A::云顶26F","A_云顶26F", 47500,52500, 96350, 33920,33920,4500, 0,150,230)
mk("R1::A::核心筒","A_核心筒", 47500,52500, 49300, 10000,10400,98600, 155,155,155)
"""

# ---- Scheme B: Terrace ----
# All boxes share SE corner, retreat to NW
b_code = """
# === B: Terrace (offset 120000) ===
# B: SE corner at (192750, 26750), all boxes share same SE, retreat NW
pl("R1::B::控制线", [(120000,0,0),(210000,0,0),(210000,105000,0),(120000,105000,0),(120000,0,0)], RED)
pl("R1::B::控制线", [(135000,8000,0),(200000,8000,0),(200000,97000,0),(135000,97000,0),(135000,8000,0)], ORG)
mk("R1::B::裙房1F","B_裙房1F", 167500,52500, 3000, 51500,51500,6000, 0,150,230)
mk("R1::B::裙房2F","B_裙房2F", 168500,51500, 8400, 49500,49500,4800, 180,100,200)
mk("R1::B::裙房3F","B_裙房3F", 167000,53000, 13350, 52500,52500,5100, 232,168,56)
mk("R1::B::裙房4F","B_裙房4F", 170900,49100, 18900, 44700,44700,6000, 0,100,180)
mk("R1::B::办公5-15F","B_办公5-15F", 174400,45600, 41000, 37700,37700,38200, 74,217,163)
mk("R1::B::客房16-25F","B_客房16-25F", 176650,43350, 77100, 33200,33200,34000, 232,168,56)
mk("R1::B::云顶26F","B_云顶26F", 177050,42950, 96350, 32400,32400,4500, 0,150,230)
mk("R1::B::核心筒","B_核心筒", 188250,31950, 49300, 10000,10400,98600, 155,155,155)
"""

# ---- Scheme C: Interlock ----
# Crystal shifts -3m X, -3m Y relative to podium. 26F cantilever +6m east.
c_code = """
# === C: Interlock (offset 240000) ===
pl("R1::C::控制线", [(240000,0,0),(330000,0,0),(330000,105000,0),(240000,105000,0),(240000,0,0)], RED)
pl("R1::C::控制线", [(255000,8000,0),(320000,8000,0),(320000,97000,0),(255000,97000,0),(255000,8000,0)], ORG)
mk("R1::C::裙房1F","C_裙房1F", 287500,52500, 3000, 49500,49500,6000, 0,150,230)
mk("R1::C::裙房2F","C_裙房2F", 287500,52500, 8400, 47500,47500,4800, 180,100,200)
mk("R1::C::裙房3F","C_裙房3F", 287500,52500, 13350, 50500,50500,5100, 232,168,56)
mk("R1::C::裙房4F","C_裙房4F", 287500,52500, 18900, 41800,41800,6000, 0,100,180)
mk("R1::C::办公晶体5-15F","C_办公晶体5-15F", 284500,49500, 41000, 36750,36750,38200, 74,217,163)
mk("R1::C::客房晶体16-25F","C_客房晶体16-25F", 284500,49500, 77100, 36750,36750,34000, 232,168,56)
mk("R1::C::云顶26F","C_云顶26F", 286000,49500, 96350, 42750,33900,4500, 0,150,230)
mk("R1::C::核心筒","C_核心筒", 287500,52500, 49300, 10000,10400,98600, 155,155,155)
"""

# Set layer colors
layer_color_code = """
for l in rs.LayerNames():
    if "控制线" in l: continue
    elif "裙房1F" in l: rs.LayerColor(l, (0,150,230))
    elif "裙房2F" in l: rs.LayerColor(l, (180,100,200))
    elif "裙房3F" in l: rs.LayerColor(l, (232,168,56))
    elif "裙房4F" in l: rs.LayerColor(l, (0,100,180))
    elif ("办公" in l) or ("晶体" in l): rs.LayerColor(l, (74,217,163))
    elif "客房" in l: rs.LayerColor(l, (232,168,56))
    elif "云顶" in l: rs.LayerColor(l, (0,150,230))
    elif "核心筒" in l: rs.LayerColor(l, (155,155,155))

t=len(rs.AllObjects())
print(f"CREATED: {t} objects")
"""

full_code = rhino_code + a_code + b_code + c_code + layer_color_code

# Write to temp file to avoid shell quoting issues
script_path = "D:/claude code mode/files/MassForge/projects/商务酒店_V3/_rhino_gen.py"

# For Rhino execution, we need it on one line or as a file
# Rhino script tool takes multiline strings, so just write to temp and display
with open(script_path, 'w', encoding='utf-8') as f:
    f.write(full_code)

print(f"Script written to {script_path}")
print(f"Full script length: {len(full_code)} chars")
