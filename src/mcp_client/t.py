from mcp.client.sse import sse_client
from mcp import ClientSession
import asyncio
import logging
import argparse
import httpx
import json

# 设置日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mcp_client")

# 默认配置参数 - 修改这些变量而不是命令行参数，方便调试
DEFAULT_HOST = "docker_xiyan_mcp_server"  # 服务器主机名
DEFAULT_PORT = 8012                       # 服务器端口
DEFAULT_MODE = "tool"                     # 测试模式: tool, resource, health, all
DEFAULT_TOOL = "get_data"                 # 要测试的工具名称
DEFAULT_QUERY = "查询公司有多少人？"       # 查询语句
DEFAULT_RESOURCE = "mysql://ruoyi-vue-pro"             # 要测试的资源URI

async def test_tool(session, tool_name, **params):
    """测试MCP工具"""
    print(f"\n测试工具: {tool_name}")
    print(f"参数: {params}")
    
    result = await session.call_tool(tool_name, params)
    
    print("结果:")
    print(result)
    return result

async def test_resource(session, resource_uri):
    """测试MCP资源"""
    print(f"\n测试资源: {resource_uri}")
    
    # 列出可用资源
    resources = await session.list_resources()
    print("可用资源:")
    for resource in resources:
        print(f"  - {resource}")
    
    # 读取指定资源
    result = await session.read_resource(resource_uri)
    
    print("资源内容:")
    print(result)
    return result

async def test_health(host, port):
    """测试健康检查端点"""
    print("\n测试健康检查端点")
    
    url = f"http://{host}:{port}/health"
    print(f"请求URL: {url}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            result = response.json()
            print("健康状态:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return result
        except Exception as e:
            print(f"健康检查失败: {e}")
            return None

async def main():
    # 解析命令行参数 - 使用全局默认值
    parser = argparse.ArgumentParser(description="MCP客户端测试工具")
    parser.add_argument("--host", default=DEFAULT_HOST, help="服务器主机名")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="服务器端口")
    parser.add_argument("--mode", choices=["tool", "resource", "health", "all"], default=DEFAULT_MODE, 
                        help="测试模式: tool(工具), resource(资源), health(健康检查), all(全部)")
    parser.add_argument("--tool", default=DEFAULT_TOOL, help="要测试的工具名称")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="查询语句")
    parser.add_argument("--resource", default=DEFAULT_RESOURCE, help="要测试的资源URI")
    
    args = parser.parse_args()
    
    try:
        # 设置服务器的host和port
        server_host = args.host
        server_port = args.port
        
        # 使用正确的URL格式
        server_url = f"http://{server_host}:{server_port}/sse"
        
        print(f"尝试连接到: {server_url}")
        
        # 如果只测试健康检查，不需要建立MCP连接
        if args.mode == "health":
            await test_health(server_host, server_port)
            return
            
        # 使用sse_client上下文管理器
        async with sse_client(server_url) as (read_stream, write_stream):
            print("成功创建SSE连接")
            
            # 创建会话并使用上下文管理器
            async with ClientSession(read_stream, write_stream) as session:
                print("成功创建客户端会话")
                
                # 初始化连接
                print("正在初始化连接...")
                await session.initialize()
                print("连接初始化成功")
                
                # 列出所有可用工具
                print("\n获取可用工具列表:")
                tools = await session.list_tools()
                for tool in tools:
                    # 直接打印工具信息，不依赖特定属性
                    print(f"  - {tool}")
                
                # 根据模式执行不同的测试
                if args.mode == "tool" or args.mode == "all":
                    if args.tool == "get_data":
                        await test_tool(session, "get_data", query=args.query)
                    elif args.tool == "check_server_status":
                        await test_tool(session, "check_server_status")
                    else:
                        await test_tool(session, args.tool)
                
                if args.mode == "resource" or args.mode == "all":
                    await test_resource(session, args.resource)
                
                if args.mode == "all":
                    await test_health(server_host, server_port)
                
    except Exception as e:
        print(f"错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

# 运行异步主函数
if __name__ == "__main__":
    asyncio.run(main())