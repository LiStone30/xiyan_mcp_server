from mcp_docker_client import MCPDockerClient
import time
import json

def main():
    # 初始化客户端 (使用Docker服务名作为主机名)
    client = MCPDockerClient(server_host="docker_xiyan_mcp_server", server_port=8012)
    
    # 连接到服务器
    client.connect()
    print("正在连接到MCP服务器...")
    
    # 等待连接建立，最多等待5秒
    max_wait = 5
    for i in range(max_wait):
        if client.connected:
            print(f"成功连接到MCP服务器（用时{i+1}秒）")
            break
        time.sleep(1)
        print(f"等待连接... ({i+1}/{max_wait})")
    
    if not client.connected:
        print("无法连接到MCP服务器，请检查服务器状态和网络连接")
        return
    
    # 列出可用工具
    def on_tools_listed(tools):
        print(f"可用工具列表:")
        for tool in tools:
            print(f"  - {tool.get('name', '未知')}: {tool.get('description', '无描述')}")
        
        # 检查服务器状态
        client.call_tool("check_server_status", {}, on_status_checked)
    
    def on_status_checked(result):
        if result:
            print("\n服务器状态信息:")
            print(result[0].get('text', '无状态信息'))
        
        # 继续列出可用资源
        client.list_resources(on_resources_listed)
    
    def on_resources_listed(resources):
        print(f"\n可用资源列表:")
        for resource in resources:
            print(f"  - {resource}")
        
        # 选择一个资源进行读取
        if resources:
            print(f"\n读取第一个资源: {resources[0]}")
            client.read_resource(resources[0], {}, on_resource_read)
        else:
            execute_query()
    
    def on_resource_read(content):
        print(f"资源内容: {content[:200]}...")  # 只显示前200个字符
        execute_query()
    
    def execute_query():
        query = "查询用户表中的所有管理员用户"
        print(f"\n执行自然语言查询: {query}")
        
        client.call_tool("get_data", {"query": query}, on_query_result)
    
    def on_query_result(result):
        if result and len(result) > 0:
            print(f"查询结果:\n{result[0].get('text', '')}")
        else:
            print("查询没有返回结果")
        print("查询完成，程序退出")
    
    # 开始执行 - 获取工具列表
    print("\n获取MCP工具列表...")
    client.list_tools(on_tools_listed)
    
    # 保持主线程运行
    try:
        while client.connected:
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序被用户中断")

if __name__ == "__main__":
    main()