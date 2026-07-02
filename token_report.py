"""Token 用量分析报告"""
import json, os, glob
from datetime import datetime, timezone, timedelta

beijing = timezone(timedelta(hours=8))
projects_dir = r'C:\Users\23791\.claude\projects'
all_sessions = glob.glob(os.path.join(projects_dir, '*', '*.jsonl'))
all_sessions.sort(key=os.path.getmtime, reverse=True)

print(f"找到 {len(all_sessions)} 个会话文件\n")

# Collect all usage data
records = []
for sf in all_sessions:
    fname = os.path.basename(sf)
    proj_dir = os.path.basename(os.path.dirname(sf))
    mtime = os.path.getmtime(sf)
    try:
        with open(sf, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                obj = json.loads(line)
                if obj.get('type') == 'assistant':
                    msg = obj.get('message', {})
                    usage = msg.get('usage', {})
                    if not usage or not usage.get('input_tokens', 0):
                        continue
                    ts = obj.get('timestamp', '')
                    if ts:
                        try:
                            dt = datetime.fromisoformat(ts.replace('Z','+00:00')).astimezone(beijing)
                            ts = dt.strftime('%m/%d %H:%M')
                        except: pass
                    records.append({
                        'session_file': fname,
                        'project': proj_dir,
                        'timestamp': ts,
                        'model': msg.get('model', '?'),
                        'input_tokens': usage.get('input_tokens', 0),
                        'cache_create': usage.get('cache_creation_input_tokens', 0),
                        'cache_read': usage.get('cache_read_input_tokens', 0),
                        'output_tokens': usage.get('output_tokens', 0),
                        'mtime': mtime,
                    })
    except Exception as e:
        print(f"  跳过 {fname}: {e}")

print(f"共收集 {len(records)} 条助手消息记录\n")

# ===== 汇总 =====
total_input = sum(r['input_tokens'] for r in records)
total_output = sum(r['output_tokens'] for r in records)
total_cache_create = sum(r['cache_create'] for r in records)
total_cache_read = sum(r['cache_read'] for r in records)
total_all_input = total_input + total_cache_create + total_cache_read
total = total_all_input + total_output

print("=" * 65)
print("            Token 使用总报告 （全量历史）")
print("=" * 65)
if records:
    oldest_dt = datetime.fromtimestamp(min(r['mtime'] for r in records))
    newest_dt = datetime.fromtimestamp(max(r['mtime'] for r in records))
    days = (newest_dt - oldest_dt).total_seconds() / 86400
    print(f"  统计区间: {records[-1]['timestamp']} ~ {records[0]['timestamp']}")
    print(f"  跨度: {days:.1f} 天\n")

print(f"{'类别':<25} {'Tokens':>12} {'比例':>8}")
print("-" * 45)
if total > 0:
    print(f"{'Input tokens':<25} {total_input:>12,} {total_input/total*100:>7.1f}%")
    print(f"{'  + Cache 创建':<25} {total_cache_create:>12,} {total_cache_create/total*100:>7.1f}%")
    print(f"{'  + Cache 读取':<25} {total_cache_read:>12,} {total_cache_read/total*100:>7.1f}%")
    print(f"{'  = Input 小计':<25} {total_all_input:>12,} {total_all_input/total*100:>7.1f}%")
    print(f"{'Output tokens':<25} {total_output:>12,} {total_output/total*100:>7.1f}%")
    print("-" * 45)
    print(f"{'总计 （Input+Output）':<25} {total:>12,} {'100.0%'}")
    if records:
        msg_count = len(records)
        print(f"{'助手消息数':<25} {msg_count:>12}")
        print(f"{'平均每条输入':<25} {total_all_input//msg_count:>12,}")
        print(f"{'平均每条输出':<25} {total_output//msg_count:>12,}")
        cost_input = total_input / 1_000_000 * 3
        cost_output = total_output / 1_000_000 * 15
        cost_cache_create = total_cache_create / 1_000_000 * 3.75
        cost_cache_read = total_cache_read / 1_000_000 * 0.30
        cost_total = cost_input + cost_output + cost_cache_create + cost_cache_read
        print(f"{'估算成本 （Haiku $3/$15/M）':<25} ${cost_total:.2f}")
        print(f"{'  其中 Input ':<25} ${cost_input:.2f}")
        print(f"{'  其中 Output':<25} ${cost_output:.2f}")
        print(f"{'  其中 Cache 创建':<25} ${cost_cache_create:.2f}")
        print(f"{'  其中 Cache 读取':<25} ${cost_cache_read:.2f}")

# 按模型
print(f"\n{'='*65}")
print("            按模型分布")
print("="*65)
models = {}
for r in records:
    m = r['model']
    if m not in models:
        models[m] = {'count':0, 'input':0, 'cache_c':0, 'cache_r':0, 'output':0}
    models[m]['count'] += 1
    models[m]['input'] += r['input_tokens']
    models[m]['cache_c'] += r['cache_create']
    models[m]['cache_r'] += r['cache_read']
    models[m]['output'] += r['output_tokens']

print(f"{'模型':<35} {'消息':>6} {'输入':>10} {'输出':>10} {'总计':>10} {'占比':>8}")
print("-"*79)
for m, d in sorted(models.items(), key=lambda x: -x[1]['count']):
    t = d['input'] + d['cache_c'] + d['cache_r'] + d['output']
    pct = t / total * 100 if total > 0 else 0
    inp = d['input'] + d['cache_c'] + d['cache_r']
    print(f"{m:<35} {d['count']:>6} {inp:>10,} {d['output']:>10,} {t:>10,} {pct:>7.1f}%")

# 按项目
print(f"\n{'='*65}")
print("            按项目分布")
print("="*65)
projects = {}
for r in records:
    p = r['project']
    if p not in projects:
        projects[p] = {'count':0, 'input':0, 'cache_c':0, 'cache_r':0, 'output':0, 'sessions':set()}
    projects[p]['count'] += 1
    projects[p]['input'] += r['input_tokens']
    projects[p]['cache_c'] += r['cache_create']
    projects[p]['cache_r'] += r['cache_read']
    projects[p]['output'] += r['output_tokens']
    projects[p]['sessions'].add(r['session_file'])

print(f"{'项目':<50} {'会话':>5} {'消息':>6} {'总计':>10} {'占比':>8}")
print("-"*79)
for p, d in sorted(projects.items(), key=lambda x: -x[1]['count']):
    t = d['input'] + d['cache_c'] + d['cache_r'] + d['output']
    pct = t / total * 100 if total > 0 else 0
    print(f"{p:<50} {len(d['sessions']):>5} {d['count']:>6} {t:>10,} {pct:>7.1f}%")

# 按日期（今日 / 本周 / 本月）
print(f"\n{'='*65}")
print("            时间维度")
print("="*65)
now = datetime.now(beijing)
today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
week_start = today_start - timedelta(days=today_start.weekday())
month_start = today_start.replace(day=1)

time_buckets = {
    '今日': today_start,
    '本周': week_start,
    '本月': month_start,
    '全部': datetime.fromtimestamp(0, tz=beijing),
}

for label, cutoff in time_buckets.items():
    filtered = [r for r in records if datetime.fromtimestamp(r['mtime'], tz=beijing) >= cutoff]
    if not filtered:
        continue
    fi = sum(r['input_tokens'] for r in filtered)
    fo = sum(r['output_tokens'] for r in filtered)
    fcc = sum(r['cache_create'] for r in filtered)
    fcr = sum(r['cache_read'] for r in filtered)
    ft = fi + fcc + fcr + fo
    print(f"  {label:<8} {len(filtered):>4} 条消息 | 输入 {fi+fcc+fcr:>10,} | 输出 {fo:>10,} | 总计 {ft:>10,}")

# Top 10 会话
print(f"\n{'='*65}")
print("            消费最高会话 Top 10")
print("="*65)
session_totals = {}
curr_session = os.path.basename(r'C:\Users\23791\.claude\projects\D--claude-code-mode\a781b561-d763-4b0c-894e-e3c2b3c573f2.jsonl')
for r in records:
    sf = r['session_file']
    if sf not in session_totals:
        session_totals[sf] = {'total':0, 'input':0, 'output':0, 'count':0, 'project':r['project'], 'curr':(sf == curr_session)}
    session_totals[sf]['total'] += r['input_tokens'] + r['cache_create'] + r['cache_read'] + r['output_tokens']
    session_totals[sf]['input'] += r['input_tokens'] + r['cache_create'] + r['cache_read']
    session_totals[sf]['output'] += r['output_tokens']
    session_totals[sf]['count'] += 1

print(f"{'#':<4} {'会话（前40字符）':<40} {'项目':<22} {'消息':>5} {'总计':>10}")
print("-"*81)
for i, (sf, d) in enumerate(sorted(session_totals.items(), key=lambda x: -x[1]['total'])[:10], 1):
    marker = " <-当前" if d.get('curr') else ""
    print(f"{i:<4} {sf[:40]:<40} {d['project']:<22} {d['count']:>5} {d['total']:>10,}{marker}")

if records:
    print("-"*81)
    gt = sum(d['total'] for d in session_totals.values())
    print(f"{'':<4} {'全部 {len(session_totals)} 个会话总计':<62} {gt:>10,}")
    avg = gt / len(session_totals) if session_totals else 0
    print(f"{'':<4} {'平均每会话':<62} {avg:>10,.0f}")

# Cache 效率
print(f"\n{'='*65}")
print("            Cache 效率分析")
print("="*65)
if total_input > 0:
    cache_saved = total_cache_read
    cache_wasted = total_cache_create
    cache_ratio = total_cache_read / (total_cache_read + total_cache_read)  # meaningless
    actual_input_pct = total_input / (total_input + total_output) * 100
    cache_read_pct = total_cache_read / (total_input + total_cache_read) * 100 if total_input + total_cache_read > 0 else 0
    print(f"  Cache 创建（写入）: {total_cache_create:>12,} tokens")
    print(f"  Cache 读取（命中）: {total_cache_read:>12,} tokens")
    print(f"  Cache 命中率:       {total_cache_read/(total_cache_read+total_cache_create)*100:>10.1f}%")
    print(f"  Cache 节省（按 $0.30/M 计）: ${total_cache_read/1_000_000*0.30:.2f}")
    print(f"  Cache 创建成本:     ${total_cache_create/1_000_000*3.75:.2f}")
    print(f"  净 Cache 效益:      ${(total_cache_read*0.30 - total_cache_create*3.75)/1_000_000:.2f}")

print("\n报告生成完毕。")
