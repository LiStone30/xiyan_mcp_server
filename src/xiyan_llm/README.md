# XiYan模型API服务

这是一个基于FastAPI的服务，使用vLLM加载本地XiYan模型并提供与OpenAI兼容的API接口。

## 功能特点

- 使用FastAPI作为服务端框架
- 通过vLLM加载本地XiYan模型
- 提供与OpenAI兼容的API接口
- 支持聊天完成接口(/v1/chat/completions)

## 如何启动

```bash
# 启动服务
python src/server.py
```

服务将在 http://localhost:8000 运行

## API使用示例

### 聊天完成接口

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
     -H "Content-Type: application/json" \
     -d '{
           "model": "xiyan-sql",
           "messages": [
             {"role": "user", "content": "请帮我编写一个SQL查询，查找用户表中年龄大于25且注册时间在过去6个月内的用户"}
           ],
           "temperature": 0.1,
           "top_p": 0.8,
           "max_tokens": 1024
         }'
```

### Python示例

```python
import openai

# 配置客户端指向本地服务
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "任意字符串" # API密钥在本地服务中不会被检查

# 发送请求
response = openai.ChatCompletion.create(
    model="xiyan-sql",
    messages=[
        {"role": "user", "content": "请帮我编写一个SQL查询，查找用户表中年龄大于25且注册时间在过去6个月内的用户"}
    ],
    temperature=0.1,
    top_p=0.8,
    max_tokens=1024
)

print(response.choices[0].message.content)
```

## API文档

服务启动后，可以通过访问 http://localhost:8000/docs 查看完整的API文档。

