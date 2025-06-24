import requests
import json
import sseclient
import threading
from typing import Dict, Any, Callable, List

class MCPDockerClient:
    def __init__(self, server_host="docker_xiyan_mcp_server", server_port=8000):
        """
        初始化MCP Docker客户端
        
        Args:
            server_host: MCP服务器的主机名或IP (Docker容器名称或网络别名)
            server_port: MCP服务器端口
        """
        self.server_url = f"http://{server_host}:{server_port}/sse"
        self.message_url = f"http://{server_host}:{server_port}/message"
        self.request_id = 0
        self.response_handlers = {}
        self.connected = False
        self.sse_thread = None
        
    def connect(self):
        """启动SSE连接"""
        if self.sse_thread is not None:
            return
            
        self.sse_thread = threading.Thread(target=self._sse_listener)
        self.sse_thread.daemon = True
        self.sse_thread.start()
        
    def _sse_listener(self):
        """SSE监听线程"""
        try:
            print(f"正在连接到SSE服务器: {self.server_url}")
            response = requests.get(self.server_url, stream=True)
            print(f"SSE连接状态码: {response.status_code}")
            print(f"SSE响应头: {dict(response.headers)}")
            
            # 先设置连接状态为True
            self.connected = True
            
            # 打印响应头中的Content-Type
            content_type = response.headers.get('Content-Type', '未知')
            print(f"Content-Type: {content_type}")
            
            # 检查是否为SSE流
            if 'text/event-stream' not in content_type:
                print(f"警告: 响应不是SSE流，Content-Type: {content_type}")
            
            print("开始处理SSE事件流...")
            # 自己解析SSE事件，不使用SSEClient
            event_data = ""
            event_name = "message"  # 默认事件名
            
            # 读取响应流
            for line in response.iter_lines(decode_unicode=True):
                if not self.connected:
                    break
                    
                if not line:
                    # 空行表示事件结束
                    if event_data:
                        print(f"接收到事件: {event_name}, 数据: {event_data}")
                        try:
                            # 解析JSON数据
                            data = json.loads(event_data)
                            print(f"解析的JSON数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
                            
                            # 处理jsonrpc响应
                            request_id = data.get("id")
                            if request_id and request_id in self.response_handlers:
                                print(f"处理请求ID: {request_id}")
                                handler = self.response_handlers.pop(request_id)
                                handler(data)
                            else:
                                print(f"未找到请求ID的处理器: {request_id if request_id else '无ID'}")
                        except json.JSONDecodeError:
                            print(f"无效的JSON响应: {event_data}")
                        
                        # 重置事件数据
                        event_data = ""
                        event_name = "message"
                else:
                    # 解析事件行
                    line = line.strip()
                    if line.startswith('data:'):
                        # 提取data字段内容
                        data_content = line[5:].strip()
                        # 如果是空data:行，则忽略
                        if data_content:
                            event_data = data_content
                    elif line.startswith('event:'):
                        event_name = line[6:].strip()
                    elif line.startswith('id:'):
                        # 忽略事件ID
                        pass
                    elif line.startswith('retry:'):
                        # 忽略重试
                        pass
                    else:
                        print(f"未知的SSE行: {line}")
                    
        except Exception as e:
            print(f"SSE连接错误: {str(e)}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")
            self.connected = False
        finally:
            print("SSE监听线程结束")
            self.connected = False
    
    def _generate_request_id(self) -> str:
        """生成请求ID"""
        self.request_id += 1
        return f"req_{self.request_id}"
        
    def send_request(self, method: str, params: Dict[str, Any], 
                     callback: Callable[[Dict[str, Any]], None]):
        """
        发送MCP请求
        
        Args:
            method: MCP方法名
            params: 请求参数
            callback: 响应回调函数
        """
        request_id = self._generate_request_id()
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        # 注册回调处理器
        self.response_handlers[request_id] = callback
        
        # 发送HTTP请求
        try:
            print(f"发送请求: {json.dumps(request, ensure_ascii=False)}")
            response = requests.post(
                self.message_url,
                json=request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            print(f"请求发送成功，状态码: {response.status_code}")
        except Exception as e:
            print(f"发送请求失败: {str(e)}")
            if request_id in self.response_handlers:
                del self.response_handlers[request_id]
    
    def list_resources(self, callback: Callable[[List[str]], None]):
        """列出可用资源"""
        def handle_response(response):
            if "result" in response:
                callback(response["result"])
            else:
                callback([])
                
        self.send_request("mcp.list_resources", {}, handle_response)
    
    def list_tools(self, callback: Callable[[List[Dict[str, Any]]], None]):
        """列出可用工具"""
        def handle_response(response):
            if "result" in response:
                callback(response["result"])
            else:
                callback([])
                
        self.send_request("mcp.list_tools", {}, handle_response)
    
    def read_resource(self, resource_id: str, params: Dict[str, Any], 
                     callback: Callable[[str], None]):
        """读取资源"""
        def handle_response(response):
            if "result" in response:
                callback(response["result"])
            else:
                callback("")
                
        self.send_request("mcp.read_resource", {
            "resource_id": resource_id,
            "params": params
        }, handle_response)
    
    def call_tool(self, tool_name: str, params: Dict[str, Any], 
                 callback: Callable[[Any], None]):
        """调用工具"""
        def handle_response(response):
            if "result" in response:
                callback(response["result"])
            else:
                callback(None)
                
        self.send_request("mcp.call_tool", {
            "tool_name": tool_name,
            "params": params
        }, handle_response)