"""测试 MCP Server (streamable-http) 接口"""
import requests
import json
import sys
import io

# 修复 Windows 控制台编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_URL = "http://localhost:8000/mcp"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
}

def call(method, params=None, session_id=None):
    """调用 MCP RPC"""
    body = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params:
        body["params"] = params
    if session_id:
        headers = {**HEADERS, "Mcp-Session-Id": str(session_id)}
    else:
        headers = HEADERS
    
    resp = requests.post(BASE_URL, json=body, headers=headers)
    print(f"\n>>> {method}")
    print(f"Status: {resp.status_code}")
    
    # 获取 session id
    sid = resp.headers.get("Mcp-Session-Id")
    if sid:
        print(f"Session-ID: {sid}")
    
    # 尝试解析 JSON 或 SSE
    content_type = resp.headers.get("Content-Type", "")
    try:
        if "event-stream" in content_type or not resp.text.startswith("{"):
            # SSE 格式: data: {...}\n\n
            for line in resp.text.split("\n"):
                line = line.strip()
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    return data, sid
        else:
            data = resp.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data, sid
    except Exception as e:
        print(f"Parse error: {e}")
        print(resp.text[:500])
        return None, sid

def main():
    print("=" * 60)
    print("MCP Server Test")
    print("=" * 60)

    # 1. Initialize
    print("\n[1] Initialize")
    result, session_id = call("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0.0"}
    })

    if not session_id:
        print("Error: No Session ID")
        return

    # 2. List Tools
    print("\n[2] List Tools")
    call("tools/list", session_id=session_id)

    # 3. Call get_joblist_by_expect_job
    print("\n[3] Call get_joblist_by_expect_job")
    call("tools/call", {
        "name": "get_joblist_by_expect_job",
        "arguments": {"job": "AI应用开发"}
    }, session_id=session_id)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()
