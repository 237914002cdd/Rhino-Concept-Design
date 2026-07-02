const { spawn } = require('child_process');

const proc = spawn('D:/claude code mode/Python312/Scripts/uvx.exe', ['rhinomcp'], {
  stdio: ['pipe', 'pipe', 'pipe'],
  encoding: 'utf-8'
});

let buf = '';
proc.stdout.on('data', (data) => {
  buf += data.toString();
  const lines = buf.split('\n');
  buf = lines.pop();
  for (const line of lines) {
    if (!line.trim()) continue;
    try {
      const msg = JSON.parse(line.trim());
      handleMessage(msg);
    } catch (e) {}
  }
});

proc.stderr.on('data', (data) => {
  // drain stderr silently
});

let id = 1;
function send(method, params = {}) {
  const msg = { jsonrpc: '2.0', id: id++, method, params };
  proc.stdin.write(JSON.stringify(msg) + '\n');
}

let pending = {};

function handleMessage(msg) {
  if (msg.id) {
    const handler = pending[msg.id];
    if (handler) {
      handler(msg);
      delete pending[msg.id];
    }
  }
}

// Wait for connection, then initialize
setTimeout(() => {
  // Step 1: Initialize
  send('initialize', {
    protocolVersion: '2024-11-05',
    client: { name: 'test', version: '1.0' },
    capabilities: {}
  });
  pending[1] = (resp) => {
    console.log('INIT:', JSON.stringify(resp).substring(0, 200));

    // Step 2: Send initialized notification
    proc.stdin.write(JSON.stringify({
      jsonrpc: '2.0',
      method: 'notifications/initialized',
      params: {}
    }) + '\n');

    setTimeout(() => {
      // Step 3: List tools
      send('tools/list', {});
      pending[2] = (resp2) => {
        const tools = resp2.result?.tools || [];
        console.log(`\nTools (${tools.length}):`);
        tools.slice(0, 10).forEach(t => console.log(`  - ${t.name}`));

        // Step 4: Create box
        send('tools/call', {
          name: 'create_object',
          arguments: {
            type: 'BOX',
            params: { width: 20, length: 10, height: 5 },
            translation: [0, 0, 0],
            color: [0, 150, 230],
            name: 'TestBox'
          }
        });
        pending[3] = (resp3) => {
          console.log('\nBOX:', JSON.stringify(resp3).substring(0, 300));

          // Step 5: Screenshot
          send('tools/call', {
            name: 'capture_viewport',
            arguments: { viewport: 'perspective', width: 1200, height: 800, zoom_to_fit: true }
          });
          pending[4] = (resp4) => {
            console.log('\nSCREENSHOT:', JSON.stringify(resp4).substring(0, 200));
            proc.kill();
            process.exit(0);
          };
        };
      };
    }, 1000);
  };
}, 2000);

setTimeout(() => {
  console.log('TIMEOUT');
  proc.kill();
  process.exit(1);
}, 15000);
