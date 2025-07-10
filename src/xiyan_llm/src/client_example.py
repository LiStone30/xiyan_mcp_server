"""
XiYan模型API服务的客户端示例
展示如何使用API服务进行模型调用
"""

import requests
import json
import time

# API服务地址
API_BASE = "http://localhost:8000/v1"

def chat_completion(messages, temperature=0.1, top_p=0.8, max_tokens=1024):
    """
    调用聊天完成API
    
    参数:
        messages: 消息列表，每个消息包含角色和内容
        temperature: 采样温度
        top_p: top-p采样参数
        max_tokens: 生成的最大token数
        
    返回:
        API响应
    """
    url = f"{API_BASE}/chat/completions"
    
    payload = {
        "model": "xiyan-sql",
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        elapsed_time = time.time() - start_time
        
        return response.json(), elapsed_time
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return None, 0

def main():
    # 检查健康状态
    try:
        health_response = requests.get("http://localhost:8000/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            if health_data.get("model_loaded"):
                print("服务健康检查: 模型已加载")
            else:
                print("服务健康检查: 模型尚未加载完成")
                return
        else:
            print(f"服务健康检查失败，状态码: {health_response.status_code}")
            return
    except requests.exceptions.RequestException:
        print("无法连接到服务，请确保服务已启动")
        return
    
    # 示例1: 简单的SQL查询生成
    print("\n=== 示例1: SQL查询生成 ===")
    messages = [
        {"role": "user", "content": "请帮我编写一个SQL查询，查找用户表中年龄大于25且注册时间在过去6个月内的用户"}
    ]
    
    response, elapsed_time = chat_completion(messages)
    if response:
        print(f"生成耗时: {elapsed_time:.2f}秒")
        print(f"生成的SQL: \n{response['choices'][0]['message']['content']}")
        
    # 示例2: 多轮对话
    print("\n=== 示例2: 多轮对话 ===")
    conversation = [
        {"role": "user", "content": "请帮我编写一个SQL查询，查找用户表中年龄大于25的用户"}
    ]
    
    response, elapsed_time = chat_completion(conversation)
    if response:
        assistant_response = response['choices'][0]['message']['content']
        print(f"助手: {assistant_response}")
        
        # 添加助手的回复到对话中
        conversation.append({"role": "assistant", "content": assistant_response})
        
        # 用户的后续问题
        user_follow_up = "能否修改一下，增加一个条件：用户在过去30天内有登录记录"
        print(f"用户: {user_follow_up}")
        
        conversation.append({"role": "user", "content": user_follow_up})
        
        # 获取助手的新回复
        response, elapsed_time = chat_completion(conversation)
        if response:
            new_response = response['choices'][0]['message']['content']
            print(f"助手: {new_response}")

if __name__ == "__main__":
    main() 