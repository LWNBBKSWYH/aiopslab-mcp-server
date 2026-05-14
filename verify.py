#!/usr/bin/env python3
"""Quick verification of MCP tools"""
import requests, json

MCP_URL = "http://localhost:8765/mcp"
s = requests.Session()
h = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}

print("=== 1. Initialize ===")
r = s.post(MCP_URL, json={"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"0.1.0","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}, headers=h, stream=True, timeout=30)
sid = r.headers.get('mcp-session-id')
print(f"Session: {sid}")

print("\n=== 2. initialized notification ===")
s.post(MCP_URL, json={"jsonrpc":"2.0","method":"notifications/initialized","params":{}}, headers={**h, 'mcp-session-id': sid}, stream=True, timeout=30)
print("OK")

print("\n=== 3. List tools ===")
r = s.post(MCP_URL, json={"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}, headers={**h, 'mcp-session-id': sid}, stream=True, timeout=30)
tools = []
for line in r.iter_lines():
    if line:
        try:
            obj = json.loads(line.decode('utf-8')[6:])
            if 'result' in obj and 'tools' in obj['result']:
                tools = obj['result']['tools']
        except: pass

print(f"Total tools: {len(tools)}")
for t in tools:
    print(f"  - {t['name']}")

print("\n=== 4. Test list_problems ===")
r = s.post(MCP_URL, json={"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_problems","arguments":{}}}, headers={**h, 'mcp-session-id': sid}, stream=True, timeout=30)
for line in r.iter_lines():
    if line:
        try:
            obj = json.loads(line.decode('utf-8')[6:])
            if 'result' in obj:
                result = obj['result']
                if isinstance(result, dict) and 'content' in result:
                    for c in result['content']:
                        if c.get('type') == 'text':
                            print(f"Problems: {c['text'][:300]}")
                elif isinstance(result, list):
                    print(f"Found {len(result)} problems: {result[:5]}...")
                else:
                    print(f"Result: {result}")
        except Exception as e:
            print(f"Parse error: {e}")

print("\n=== DONE ===")