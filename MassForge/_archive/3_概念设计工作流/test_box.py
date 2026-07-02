"""Test rhino MCP box creation - simple line by line"""
import json
import subprocess
import time

CMD = ["D:/claude code mode/Python312/Scripts/uvx.exe", "rhinomcp"]

proc = subprocess.Popen(
    CMD,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

def send(msg):
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()

def recv():
    line = proc.stdout.readline()
    if line:
        try:
            return json.loads(line.strip())
        except:
            return {"raw": line.strip()}
    return None

# Initialize
send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","client":{"name":"test","version":"1.0"},"capabilities":{}}})
r = recv()
print("INIT:", json.dumps(r, ensure_ascii=False)[:200] if r else "NO RESPONSE")

# Initialized notification
send({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
time.sleep(1)

# List tools
send({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
r = recv()
if r and "result" in r:
    tools = r["result"].get("tools", [])
    print(f"\nTools ({len(tools)}):")
    for t in tools[:15]:
        print(f"  - {t['name']}")
else:
    print(f"\nTools response: {json.dumps(r, ensure_ascii=False)[:500] if r else 'TIMEOUT'}")

# Create box
send({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"create_object","arguments":{"type":"BOX","params":{"width":20,"length":10,"height":5},"translation":[0,0,0],"color":[0,150,230],"name":"测试Box"}}})
r = recv()
print(f"\nBOX: {json.dumps(r, ensure_ascii=False)[:500] if r else 'TIMEOUT'}")

time.sleep(1)

proc.terminate()
proc.wait()
