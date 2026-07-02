"""Generate token usage spreadsheet with Claude Code aesthetic via WPS"""
import pythoncom, os
pythoncom.CoInitialize()
import win32com.client as wc

# ── Claude Code brand palette ──
DARK_BG    = 0x002B36  # deep navy
HEADER_BG  = 0x004466  # teal blue
ALT_ROW    = 0x003344  # subtle alt
ACCENT     = 0x33A1C9  # bright teal
ACCENT2    = 0xE6C384  # warm gold accent
WHITE      = 0xFFFFFF
LIGHT_GRAY = 0xBBBBBB
GREEN      = 0x8BC34A
RED        = 0xEF5350

data = {
    'total_input': 666545038,
    'total_cc': 0,
    'total_cr': 31719331200,
    'total_output': 62580282,
    'total_all': 32448456520,
    'msgs': 126539,
    'sessions': 172,
}

# ── Open WPS ──
app = wc.Dispatch('Ket.Application')
app.Visible = False  # will set True at end
wb = app.Workbooks.Add()

def style_range(rng, font_color=WHITE, font_size=10, bold=False, interior=None, font_name='微软雅黑'):
    rng.Font.Color = font_color
    rng.Font.Size = font_size
    rng.Font.Bold = bold
    rng.Font.Name = font_name
    if interior is not None:
        rng.Interior.Color = interior

def set_header(ws, row, cols, values):
    for i, v in enumerate(values, 1):
        c = ws.Cells(row, i)
        c.Value = v
        style_range(c, WHITE, 11, True, HEADER_BG)
    # merge header row?
    rng = ws.Range(ws.Cells(row, 1), ws.Cells(row, len(values)))
    rng.HorizontalAlignment = -4108  # xlCenter

def add_row(ws, row, values, alt=False, formats=None):
    """formats: list of (font_color, bold) per col or None"""
    bg = ALT_ROW if alt else DARK_BG
    for i, v in enumerate(values, 1):
        c = ws.Cells(row, i)
        c.Value = v
        fc = WHITE
        bd = False
        if formats and i <= len(formats) and formats[i-1]:
            fc = formats[i-1].get('color', WHITE)
            bd = formats[i-1].get('bold', False)
        style_range(c, fc, 10, bd, bg)

def set_col_widths(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.Columns(i).ColumnWidth = w

def add_section(ws, row, title, span=4):
    ws.Range(ws.Cells(row,1), ws.Cells(row,span)).Merge()
    c = ws.Cells(row, 1)
    c.Value = title
    style_range(c, ACCENT, 12, True, DARK_BG)
    return row + 1

# ════════════════════════════════════════
# Sheet 1: Overview
# ════════════════════════════════════════
ws1 = wb.Worksheets(1)
ws1.Name = 'Overview'

# Title
ws1.Range('A1:F1').Merge()
c = ws1.Cells(1,1)
c.Value = 'Token Usage Report  |  Claude Code'
style_range(c, ACCENT, 18, True, DARK_BG)
ws1.Rows(1).RowHeight = 35

ws1.Range('A2:F2').Merge()
c = ws1.Cells(2,1)
c.Value = '2026-05-25 ~ 2026-07-01  |  36.8 days  |  172 sessions  |  126,539 messages'
style_range(c, LIGHT_GRAY, 10, False, DARK_BG)

r = 4
r = add_section(ws1, r, 'Key Metrics')
metrics = [
    ('Total Tokens Consumed', f'{data["total_all"]:,}', WHITE, False),
    ('Est. Cost (Haiku pricing)', '$12,454.14', ACCENT2, True),
    ('Avg Tokens per Message', f'{data["total_all"]//data["msgs"]:,}', LIGHT_GRAY, False),
    ('Avg Tokens per Session', f'{data["total_all"]//data["sessions"]:,}', LIGHT_GRAY, False),
]
for i, (label, val, *_) in enumerate(metrics, r):
    ws1.Cells(i,1).Value = label; style_range(ws1.Cells(i,1), LIGHT_GRAY, 10, False, DARK_BG if (i-r)%2==0 else ALT_ROW)
    ws1.Cells(i,2).Value = val;   style_range(ws1.Cells(i,2), metrics[i-r][2], 11, metrics[i-r][3], DARK_BG if (i-r)%2==0 else ALT_ROW)
r += len(metrics) + 1

r = add_section(ws1, r, 'Token Breakdown')
set_header(ws1, r, 3, ['Category', 'Tokens', '%'])
r += 1
rows = [
    ('Input tokens',           f'{data["total_input"]:,}',  f'{data["total_input"]/data["total_all"]*100:.1f}%'),
    ('Cache creation (write)', f'{data["total_cc"]:,}',     f'{data["total_cc"]/data["total_all"]*100:.1f}%'),
    ('Cache read (hit)',       f'{data["total_cr"]:,}',     f'{data["total_cr"]/data["total_all"]*100:.1f}%'),
    ('Output tokens',          f'{data["total_output"]:,}', f'{data["total_output"]/data["total_all"]*100:.1f}%'),
]
for i, (cat, tok, pct) in enumerate(rows, r):
    alt = (i - r) % 2 == 1
    fmt_h = [{'color': ACCENT if 'Cache read' in cat else WHITE}, {}, {}]
    add_row(ws1, i, [cat, tok, pct], alt)
r += len(rows)
# Total row
for c in [1,2,3]:
    cell = ws1.Cells(r, c)
    style_range(cell, ACCENT2, 11, True, ALT_ROW)
ws1.Cells(r,1).Value = 'TOTAL'; ws1.Cells(r,2).Value = f'{data["total_all"]:,}'; ws1.Cells(r,3).Value = '100%'

r += 2
r = add_section(ws1, r, 'Cost Breakdown')
set_header(ws1, r, 3, ['Category', 'Rate', 'Cost'])
r += 1
cost_rows = [
    ('Input',          '$3.00/M',  f'${data["total_input"]/1_000_000*3:.2f}'),
    ('Output',         '$15.00/M', f'${data["total_output"]/1_000_000*15:.2f}'),
    ('Cache creation', '$3.75/M',  f'${data["total_cc"]/1_000_000*3.75:.2f}'),
    ('Cache read',     '$0.30/M',  f'${data["total_cr"]/1_000_000*0.30:.2f}'),
]
for i, (cat, rate, cost) in enumerate(cost_rows, r):
    add_row(ws1, i, [cat, rate, cost], (i-r)%2==1)
r += len(cost_rows)
for c in [1,2,3]:
    cell = ws1.Cells(r, c)
    style_range(cell, ACCENT2, 11, True, ALT_ROW)
ws1.Cells(r,1).Value = 'TOTAL'; ws1.Cells(r,2).Value = ''; ws1.Cells(r,3).Value = '$12,454.14'

set_col_widths(ws1, [35, 25, 15])

# ════════════════════════════════════════
# Sheet 2: Models
# ════════════════════════════════════════
ws2 = wb.Worksheets.Add(None, ws1)
ws2.Name = 'By Model'
ws2.Cells(1,1).Value = 'Token Usage by Model'
ws2.Range('A1:E1').Merge()
style_range(ws2.Cells(1,1), ACCENT, 16, True, DARK_BG)

model_data = [
    ('deepseek-v4-flash', 141, 104022, 29387155609, 90.6),
    ('deepseek-v4-pro', 80, 22512, 3060966024, 9.4),
    ('mimo-v2.5-pro', 1, 5, 334887, 0.0),
]
set_header(ws2, 3, 5, ['Model', 'Sessions', 'Messages', 'Total Tokens', '% of Total'])
for i, (m, sess, msgs, tot, pct) in enumerate(model_data, 4):
    add_row(ws2, i, [m, sess, f'{msgs:,}', f'{tot:,}', f'{pct:.1f}%'], (i-4)%2==1)
set_col_widths(ws2, [30, 12, 14, 20, 14])

# ════════════════════════════════════════
# Sheet 3: Time
# ════════════════════════════════════════
ws3 = wb.Worksheets.Add(None, ws2)
ws3.Name = 'Time'
ws3.Cells(1,1).Value = 'Time Dimensions'
ws3.Range('A1:E1').Merge()
style_range(ws3.Cells(1,1), ACCENT, 16, True, DARK_BG)

time_data = [
    ('Today', 2133, 7861183, 1431168, 240129664, 249422015),
    ('This Week', 21866, 158443910, 14151980, 5052304384, 5224900274),
    ('This Month', 2133, 7861183, 1431168, 240129664, 249422015),
    ('All Time', 126539, 666545038, 62580282, 31719331200, 32448456520),
]
set_header(ws3, 3, 6, ['Period', 'Messages', 'Input (incl Cache)', 'Output', 'Cache Read', 'Total'])
for i, row in enumerate(time_data, 4):
    vals = [row[0], f'{row[1]:,}'] + [f'{v:,}' for v in row[2:]]
    is_total = row[0] == 'All Time'
    add_row(ws3, i, vals, (i-4)%2==1)
    if is_total:
        for c in range(1, 7):
            style_range(ws3.Cells(i, c), ACCENT2, 10, True, ALT_ROW)
set_col_widths(ws3, [16, 12, 22, 16, 18, 18])

# ════════════════════════════════════════
# Sheet 4: Top Sessions
# ════════════════════════════════════════
ws4 = wb.Worksheets.Add(None, ws3)
ws4.Name = 'Top Sessions'
ws4.Cells(1,1).Value = 'Top 10 Sessions by Token Consumption'
ws4.Range('A1:D1').Merge()
style_range(ws4.Cells(1,1), ACCENT, 16, True, DARK_BG)

top_sessions = [
    ('a6f35fda-407b-458c-ad8e-e583f0fe7679', 'd--claude-code-mode-files', 4697, 2012367946),
    ('2669da63-59e9-4d35-a55b-343ab4283ae7', 'd--claude-code-mode-files', 2951, 1607352461),
    ('a5c5d506-99ea-4df7-ad63-904b23d33239', 'd--claude-code-mode-files', 2905, 1564552588),
    ('b4d08bba-544c-4c1d-9616-427ccfac305d', 'd--claude-code-mode-files', 2955, 1431871747),
    ('7ce8af71-7a8c-4904-9063-9f93300cdddd', 'd--claude-code-mode-files', 1898, 774927006),
    ('7b5923df-e35f-4dcb-a817-862b44a4e1c1', 'd--claude-code-mode-files', 1823, 726065469),
    ('d9fc6bf9-f15d-468a-a983-a1205f943489', 'd--claude-code-mode-files', 1781, 698552247),
    ('a8e8cade-9713-410c-9b64-5f43bfac0813', 'd--claude-code-mode-files', 1762, 686433175),
    ('0f19e0af-ad42-44a6-845f-9ec72a451c91', 'd--claude-code-mode-files', 1483, 632214251),
    ('be48742c-e9d3-43bb-bfd1-ff8c45ad623a', 'd--claude-code-mode-files', 1470, 627936102),
]
set_header(ws4, 3, 5, ['#', 'Session ID', 'Project', 'Messages', 'Total Tokens'])
for i, (sid, proj, msgs, tot) in enumerate(top_sessions, 4):
    add_row(ws4, i, [i-3, sid[:36], proj, f'{msgs:,}', f'{tot:,}'], (i-4)%2==1)
set_col_widths(ws4, [6, 40, 30, 12, 18])

# ════════════════════════════════════════
# Sheet 5: Cache Efficiency
# ════════════════════════════════════════
ws5 = wb.Worksheets.Add(None, ws4)
ws5.Name = 'Cache'
ws5.Cells(1,1).Value = 'Cache Efficiency Analysis'
ws5.Range('A1:C1').Merge()
style_range(ws5.Cells(1,1), ACCENT, 16, True, DARK_BG)

set_header(ws5, 3, 2, ['Metric', 'Value'])
cache_rows = [
    ('Cache creation (write)', f'{data["total_cc"]:,} tokens'),
    ('Cache read (hit)', f'{data["total_cr"]:,} tokens'),
    ('Hit rate', '100.0%'),
    ('Cost saved (hits @ $0.30/M)', f'${data["total_cr"]/1_000_000*0.30:.2f}'),
    ('Cost incurred (write @ $3.75/M)', f'${data["total_cc"]/1_000_000*3.75:.2f}'),
    ('Net benefit from cache', f'${abs(data["total_cr"]*0.30 - data["total_cc"]*3.75)/1_000_000:.2f}'),
]
for i, (metric, val) in enumerate(cache_rows, 4):
    add_row(ws5, i, [metric, val], (i-4)%2==1)
    if 'Net benefit' in metric:
        style_range(ws5.Cells(i,1), ACCENT2, 10, True, DARK_BG if (i-4)%2==0 else ALT_ROW)
        style_range(ws5.Cells(i,2), GREEN, 11, True, DARK_BG if (i-4)%2==0 else ALT_ROW)
set_col_widths(ws5, [35, 25])

# ════════════════════════════════════════
# Global styling: dark background for all sheets
# ════════════════════════════════════════
for ws in [ws1, ws2, ws3, ws4, ws5]:
    rng = ws.Range('A1', ws.Cells(200, 50))
    rng.Interior.Color = DARK_BG
    rng.Font.Color = WHITE
    ws.Application.ActiveWindow.DisplayGridlines = False

# ════════════════════════════════════════
# Save
# ════════════════════════════════════════
out_dir = r'd:\claude code mode\files\WPS文档'
out_path = os.path.join(out_dir, 'TokenUsage-ClaudeCode.xlsx')
wb.SaveAs(out_path)
wb.Close()
app.Quit()
pythoncom.CoUninitialize()

print(f'Saved: {out_path}')
