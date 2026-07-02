# Generate all 3 schemes in Rhino with independent area calculations
import json, os, subprocess, shutil
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

total_target = 37807.32

ALL_OBJECTS = []
ALL_DATA = []  # for report

# ===================================================================
# Scheme A: Monolith - centered, flush outer envelope, internal void
# ===================================================================
def add_scheme(scheme_letter, name_cn, desc, offset_x, boxes, is_crystal=False, crystal_name=""):
    """boxes: list of (name, target_area, w_mm, d_mm, h_mm, rgb, layer_name)"""
    subtotal = 0
    all_objs = []
    for b in boxes:
        name, target_area, w, d, h, rgb, layer = b
        obj = {
            "type": "BOX",
            "name": name,
            "color": list(rgb),
            "params": {"width": w, "length": d, "height": h},
            "translation": [offset_x, 0, 0],
            "layer": f"R1::{name_cn}::{layer}"
        }
        all_objs.append(obj)
        # calc area
        area_per_floor = (w/1000) * (d/1000)

        if is_crystal and name == crystal_name:
            # crystal covers floors 5-25F = 21 floors
            floor_count = 21
        elif "核心筒" in name:
            floor_count = 0
        elif "5-15F" in name:
            floor_count = 11
        elif "16-25F" in name:
            floor_count = 10
        else:
            floor_count = 1

        if "核心筒" in name:
            subtotal += 0  # core doesn't count as GFA
        else:
            subtotal += area_per_floor * floor_count

        ALL_DATA.append({
            "scheme": scheme_letter,
            "scheme_name": name_cn,
            "name": name,
            "target": target_area,
            "area": round(area_per_floor, 1),
            "w_m": round(w/1000, 2),
            "d_m": round(d/1000, 2),
            "h_mm": h,
            "rgb": rgb,
            "layer": layer
        })

    error_pct = round((subtotal - total_target) / total_target * 100, 2)
    ALL_OBJECTS.extend(all_objs)
    print(f"{name_cn}: total={subtotal:.0f}m2, error={error_pct}%")
    return subtotal, error_pct

# A: Monolith - all centered at site center
cx_A, cy_A = 22250 + 25250, 27250 + 25250  # = 47500, 52500
# Actually let me compute from the buildable zone
# Buildable X: 15000-80000, center=47500
# Buildable Y: 8000-97000, center=52500

A_boxes = [
    ("A_裙房1F", 2550.00, 50500, 50500, 6000,  (0,150,230), "裙房1F"),
    ("A_裙房2F", 2350.00, 48500, 48500, 4800,  (180,100,200), "裙房2F"),
    ("A_裙房3F", 2650.00, 51500, 51500, 5100,  (232,168,56), "裙房3F"),
    ("A_裙房4F", 1850.00, 43000, 43000, 6000,  (0,100,180), "裙房4F"),
    ("A_办公5-15F", 1350.25, 36750, 36750, 38200, (74,217,163), "办公5-15F"),
    ("A_客房16-25F", 1210.45, 34790, 34790, 34000, (232,168,56), "客房16-25F"),
    ("A_云顶26F", 1150.32, 33920, 33920, 4500,  (0,150,230), "云顶26F"),
    ("A_核心筒", 104.00, 10000, 10400, 98600,  (155,155,155), "核心筒"),
]

# B: Terrace - SE corner anchored
# SE corner at (72750, 26750) in local = (192750, 26750) in absolute (offset=120000)
# This gives P1F at center (167500, 52500) — same relative pos as A
# For each box at (se_x, se_y), center_x = se_x - w/2, center_y = se_y + d/2
se_x, se_y = 72750, 26750
b_off = 120000
B_boxes_raw = [
    ("B_裙房1F", 2650.00, 51500, 51500, 6000,  (0,150,230), "裙房1F"),
    ("B_裙房2F", 2450.00, 49500, 49500, 4800,  (180,100,200), "裙房2F"),
    ("B_裙房3F", 2750.00, 52500, 52500, 5100,  (232,168,56), "裙房3F"),
    ("B_裙房4F", 2000.00, 44700, 44700, 6000,  (0,100,180), "裙房4F"),
    ("B_办公5-15F", 1420.00, 37700, 37700, 38200, (74,217,163), "办公5-15F"),
    ("B_客房16-25F", 1100.00, 33200, 33200, 34000, (232,168,56), "客房16-25F"),
    ("B_云顶26F", 1050.00, 32400, 32400, 4500,  (0,150,230), "云顶26F"),
    ("B_核心筒", 104.00, 10000, 10400, 98600,  (155,155,155), "核心筒"),  # cx,cy computed from SE corner = Guest center
]

B_boxes = []
for name, area, w, d, h, rgb, layer in B_boxes_raw:
    cx = se_x - w/2 + b_off
    cy = se_y + d/2
    obj = {
        "type": "BOX",
        "name": name,
        "color": list(rgb),
        "params": {"width": w, "length": d, "height": h},
        "translation": [int(cx - w/2), int(cy - d/2), 0],
        "layer": f"R1::B::{layer}"
    }
    ALL_OBJECTS.append(obj)
    area_per = (w/1000)*(d/1000)
    fc = 11 if "5-15F" in name else (10 if "16-25F" in name else (0 if "核心筒" in name else 1))
    ALL_DATA.append({"scheme":"B","scheme_name":"B_阶梯错叠","name":name,"target":area,
        "area":round(area_per,1),"w_m":round(w/1000,2),"d_m":round(d/1000,2),"h_mm":h,"rgb":rgb,"layer":layer})

# C: Interlock - podium centered, crystal offset -3m, 26F cantilever +6m
c_off = 240000
C_boxes_raw = [
    ("C_裙房1F", 2450.00, 49500, 49500, 6000,  (0,150,230), "裙房1F"),
    ("C_裙房2F", 2250.00, 47500, 47500, 4800,  (180,100,200), "裙房2F"),
    ("C_裙房3F", 2550.00, 50500, 50500, 5100,  (232,168,56), "裙房3F"),
    ("C_裙房4F", 1750.00, 41800, 41800, 6000,  (0,100,180), "裙房4F"),
    ("C_办公晶体5-15F", 1350.00, 36750, 36750, 38200, (74,217,163), "办公晶体5-15F"),
    ("C_客房晶体16-25F", 1350.00, 36750, 36750, 34000, (232,168,56), "客房晶体16-25F"),
    ("C_云顶26F", 1450.00, 42750, 33900, 4500,  (0,150,230), "云顶26F"),
    ("C_核心筒", 104.00, 10000, 10400, 98600,  (155,155,155), "核心筒"),
]

# Podium centered at same as A but shifted to 240000
# Crystal shifted -3m in X, -3m in Y
# 26F extended +6m in X (east side)
for name, area, w, d, h, rgb, layer in C_boxes_raw:
    if "晶体" in name:
        cx = 47500 - 3000 + c_off
        cy = 52500 - 3000
    elif "云顶" in name:
        cx = 47500 + 3000 + c_off
        cy = 52500 - 3000
    else:
        cx = 47500 + c_off
        cy = 52500
    fc = 21 if "晶体" in name else 0 if "核心筒" in name else 1
    obj = {
        "type": "BOX",
        "name": name,
        "color": list(rgb),
        "params": {"width": w, "length": d, "height": h},
        "translation": [int(cx - w/2), int(cy - d/2), 0],
        "layer": f"R1::C::{layer}"
    }
    ALL_OBJECTS.append(obj)
    area_per = (w/1000)*(d/1000)
    ALL_DATA.append({"scheme":"C","scheme_name":"C_异质穿插","name":name,"target":area,
        "area":round(area_per,1),"w_m":round(w/1000,2),"d_m":round(d/1000,2),"h_mm":h,"rgb":rgb,"layer":layer})

# Now for A boxes, position them centered
for name, area, w, d, h, rgb, layer in A_boxes:
    cx = 47500
    cy = 52500
    fc = 11 if "5-15F" in name else (10 if "16-25F" in name else (0 if "核心筒" in name else 1))
    obj = {
        "type": "BOX",
        "name": name,
        "color": list(rgb),
        "params": {"width": w, "length": d, "height": h},
        "translation": [int(cx - w/2), int(cy - d/2), 0],
        "layer": f"R1::A::{layer}"
    }
    ALL_OBJECTS.append(obj)

json.dump({"objects": ALL_OBJECTS}, open(
    "D:/claude code mode/files/MassForge/projects/商务酒店_V3/output/_rhino_objects.json","w",encoding="utf-8"),ensure_ascii=False,indent=2)
print(f"Wrote {len(ALL_OBJECTS)} objects to JSON")
