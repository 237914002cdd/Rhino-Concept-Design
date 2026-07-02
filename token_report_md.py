"""Token Usage Report - generates markdown"""
import json, os, glob
from datetime import datetime, timezone, timedelta

beijing = timezone(timedelta(hours=8))
projects_dir = r'C:\Users\23791\.claude\projects'
all_sessions = glob.glob(os.path.join(projects_dir, '*', '*.jsonl'))
all_sessions.sort(key=os.path.getmtime, reverse=True)

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
                            ts = dt.strftime('%Y-%m-%d %H:%M')
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
        pass

sessions = len(set(r['session_file'] for r in records))
msgs = len(records)

total_input = sum(r['input_tokens'] for r in records)
total_output = sum(r['output_tokens'] for r in records)
total_cc = sum(r['cache_create'] for r in records)
total_cr = sum(r['cache_read'] for r in records)
total_all = total_input + total_cc + total_cr + total_output

# Per-session totals (NOT cumulative-sum over all messages)
# Each message's input_tokens is the billed amount for that API call
# Even with cumulative context, the API bills each call's input separately
# So summing IS the total billing amount

lines = []
lines.append("# Token Usage Report")
lines.append("")
lines.append(f"Period: {records[-1]['timestamp']} ~ {records[0]['timestamp']}")
oldest = datetime.fromtimestamp(min(r['mtime'] for r in records))
newest = datetime.fromtimestamp(max(r['mtime'] for r in records))
days = (newest - oldest).total_seconds() / 86400
lines.append(f"Span: {days:.1f} days | Sessions: {sessions} | Messages: {msgs}")
lines.append("")

lines.append("## 1. Summary")
lines.append("")
lines.append("| Category | Tokens | % |")
lines.append("|---|---|---|")
lines.append(f"| Input tokens | {total_input:,} | {total_input/total_all*100:.1f}% |")
lines.append(f"| Cache creation (write) | {total_cc:,} | {total_cc/total_all*100:.1f}% |")
lines.append(f"| Cache read (hit) | {total_cr:,} | {total_cr/total_all*100:.1f}% |")
lines.append(f"| Output tokens | {total_output:,} | {total_output/total_all*100:.1f}% |")
lines.append(f"| **Total** | **{total_all:,}** | **100%** |")
lines.append("")

cost_in = total_input / 1_000_000 * 3
cost_out = total_output / 1_000_000 * 15
cost_cc = total_cc / 1_000_000 * 3.75
cost_cr = total_cr / 1_000_000 * 0.30
cost_total = cost_in + cost_out + cost_cc + cost_cr
lines.append(f"| Avg input/msg | {total_input//msgs:,} |")
lines.append(f"| Avg output/msg | {total_output//msgs:,} |")
lines.append(f"| Est. cost | ${cost_total:.2f} (Haiku pricing) |")
lines.append("")

# Model distribution
lines.append("## 2. By Model")
lines.append("")
lines.append("| Model | Sessions | Messages | Total Tokens | % |")
lines.append("|---|---|---|---|---|")
models = {}
for r in records:
    m = r['model']
    if m not in models:
        models[m] = {'count':0, 'total':0, 'sessions':set()}
    models[m]['count'] += 1
    models[m]['total'] += r['input_tokens'] + r['cache_create'] + r['cache_read'] + r['output_tokens']
    models[m]['sessions'].add(r['session_file'])
for m, d in sorted(models.items(), key=lambda x: -x[1]['total']):
    lines.append(f"| {m} | {len(d['sessions'])} | {d['count']:,} | {d['total']:,} | {d['total']/total_all*100:.1f}% |")
lines.append("")

# Project distribution
lines.append("## 3. By Project")
lines.append("")
lines.append("| Project | Sessions | Messages | Total Tokens | % |")
lines.append("|---|---|---|---|---|")
projects = {}
for r in records:
    p = r['project']
    if p not in projects:
        projects[p] = {'count':0, 'total':0, 'sessions':set()}
    projects[p]['count'] += 1
    projects[p]['total'] += r['input_tokens'] + r['cache_create'] + r['cache_read'] + r['output_tokens']
    projects[p]['sessions'].add(r['session_file'])
for p, d in sorted(projects.items(), key=lambda x: -x[1]['total']):
    lines.append(f"| {p} | {len(d['sessions'])} | {d['count']:,} | {d['total']:,} | {d['total']/total_all*100:.1f}% |")
lines.append("")

# Time dimension
now = datetime.now(beijing)
today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
week_start = today_start - timedelta(days=today_start.weekday())
month_start = today_start.replace(day=1)

def time_report(label, cutoff):
    f = [r for r in records if datetime.fromtimestamp(r['mtime'], tz=beijing) >= cutoff]
    if not f:
        return None
    fi = sum(r['input_tokens'] for r in f)
    fo = sum(r['output_tokens'] for r in f)
    fcc = sum(r['cache_create'] for r in f)
    fcr = sum(r['cache_read'] for r in f)
    return {
        'label': label,
        'msgs': len(f),
        'cache_hit': fcr,
        'cache_miss': fcc,
        'input_raw': fi,
        'output': fo,
        'total': fi+fcc+fcr+fo
    }

lines.append("## 4. Time Dimensions")
lines.append("")
lines.append("| Period | Messages | Input | Output | Cache Read | Total |")
lines.append("|---|---|---|---|---|---|")
for label, cutoff in [('Today', today_start), ('This Week', week_start), ('This Month', month_start)]:
    tr = time_report(label, cutoff)
    if tr:
        lines.append(f"| {tr['label']} | {tr['msgs']:,} | {tr['input_raw']+tr['cache_miss']:>12,} | {tr['output']:>12,} | {tr['cache_hit']:>12,} | {tr['total']:>12,} |")
lines.append("")

# Top sessions
lines.append("## 5. Top 10 Sessions by Token Consumption")
lines.append("")
lines.append("| # | Session | Project | Messages | Total Tokens |")
lines.append("|---|---|---|---|---|")
session_totals = {}
for r in records:
    sf = r['session_file']
    if sf not in session_totals:
        session_totals[sf] = {'total':0, 'count':0, 'project':r['project']}
    session_totals[sf]['total'] += r['input_tokens'] + r['cache_create'] + r['cache_read'] + r['output_tokens']
    session_totals[sf]['count'] += 1

for i, (sf, d) in enumerate(sorted(session_totals.items(), key=lambda x: -x[1]['total'])[:10], 1):
    lines.append(f"| {i} | {sf[:36]} | {d['project']} | {d['count']:,} | {d['total']:,} |")
lines.append("")

gt = sum(d['total'] for d in session_totals.values())
lines.append(f"**All {len(session_totals)} sessions total: {gt:,} tokens**")
lines.append(f"**Avg per session: {gt//len(session_totals):,} tokens**")
lines.append("")

# Cache
lines.append("## 6. Cache Efficiency")
lines.append("")
lines.append(f"| Metric | Value |")
lines.append("|---|---|")
lines.append(f"| Cache creation (write) | {total_cc:,} tokens |")
lines.append(f"| Cache read (hit) | {total_cr:,} tokens |")
lines.append(f"| Hit rate | {total_cr/(total_cr+total_cc)*100:.1f}% |" if (total_cr+total_cc)>0 else "| Hit rate | N/A |")
lines.append(f"| Cost saved (hits @ $0.30/M) | ${total_cr/1_000_000*0.30:.2f} |")
lines.append(f"| Cost incurred (write @ $3.75/M) | ${total_cc/1_000_000*3.75:.2f} |")
lines.append(f"| Net benefit | ${(total_cr*0.30 - total_cc*3.75)/1_000_000:.2f} |")
lines.append("")

lines.append("---")
lines.append(f"Report generated: {now.strftime('%Y-%m-%d %H:%M')}")

result = '\n'.join(lines)

# Write to file
out_path = r'd:\claude code mode\files\token_usage_report.md'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(result)
print(f"Report saved to: {out_path}")
print(f"Summary: {msgs} messages across {sessions} sessions, {total_all:,} total tokens")
