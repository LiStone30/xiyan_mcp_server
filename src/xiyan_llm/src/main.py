"""
使用 fast api 作为 服务端框架
参考 /app/src/local_model/xiyan_vllm_chat_demo.py 这个文件中 LLM模型加载和推理的逻辑；进行模型推理
使用 openai定义的 接口 作为 服务端接口
"""

import os
import uvicorn
from api import app
from dotenv import load_dotenv

# 加载.env文件
load_dotenv("/app/src/.env")

# 从环境变量中获取端口，如果不存在则使用默认值8000
port = int(os.getenv("port", 8014))

if __name__ == "__main__":
    print(f"启动XiYan模型API服务，端口: {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)