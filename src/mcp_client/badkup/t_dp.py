import uuid
import requests
import json

# 配置参数（根据实际修改）
MCP_SERVER_URL = "http://localhost:8000/sse"  # xiyan_mcp_server 的 SSE 地址
TOOL_NAME = "get_data"
PARAMETERS = {  # 示例参数，需按工具文档调整
    "query": "SELECT * FROM orders WHERE status='completed'",
    "limit": 10
}

def call_mcp_tool():
    # 1. 构建 MCP 协议请求体
    request_id = str(uuid.uuid4())
    payload = {
        "type": "ToolCall",
        "id": request_id,
        "tool": {
            "name": TOOL_NAME,
            "parameters": PARAMETERS
        }
    }
    
    # 2. 发送 SSE 请求
    headers = {"Accept": "text/event-stream"}
    try:
        response = requests.post(
            MCP_SERVER_URL,
            json=payload,
            headers=headers,
            stream=True
        )
        response.raise_for_status()
        
        # 3. 解析流式响应
        print(f"🚀 工具调用成功 (Request ID: {request_id})")
        for line in response.iter_lines():
            if line:
                # 提取 JSON 数据部分（跳过 "data: " 前缀）
                event_data = json.loads(line.decode('utf-8').replace('data: ', '', 1))
                if event_data.get("type") == "ToolResponse":
                    result = event_data["content"]["result"]
                    print(f"✅ 返回数据:\n{json.dumps(result, indent=2)}")
                elif event_data.get("type") == "Error":
                    print(f"❌ 错误信息: {event_data['message']}")

    except requests.exceptions.RequestException as e:
        print(f"🔌 连接失败: {e}")

if __name__ == "__main__":
    call_mcp_tool()