"""
使用FastAPI作为服务端框架
参考xiyan_vllm_chat_demo.py中的模型加载和推理逻辑
实现与OpenAI兼容的接口
"""

import os
import time
from typing import List, Dict, Any, Optional, Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

# 模型路径
MODEL_PATH = "/app/src/local_model/model/XGenerationLab/XiYanSQL-QwenCoder-3B-2502"

# 初始化FastAPI应用
app = FastAPI(title="XiYan模型API服务", description="兼容OpenAI接口的本地XiYan模型服务")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义模型和tokenizer
llm = None
tokenizer = None

# 定义请求模型
class Message(BaseModel):
    role: Literal["system", "user", "assistant"] = "user"
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = Field(default="xiyan-sql")
    messages: List[Message]
    temperature: Optional[float] = 0.1
    top_p: Optional[float] = 0.8
    max_tokens: Optional[int] = 1024
    stream: Optional[bool] = False

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str = "stop"

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Usage

# 加载模型和tokenizer
@app.on_event("startup")
async def startup_event():
    global llm, tokenizer
    print(f"开始加载模型: {MODEL_PATH}")
    gpu_mem_util = os.getenv("gpu_mem_util", 0.8)
    start_time = time.time()
    
    # 加载tokenizer以支持聊天模板
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    
    # 使用vLLM加载模型
    llm = LLM(
        model=MODEL_PATH,
        tensor_parallel_size=1,
        gpu_memory_utilization=float(gpu_mem_util),
        trust_remote_code=True,
        dtype="float16",
    )
    
    load_time = time.time() - start_time
    print(f"模型加载完成，耗时: {load_time:.2f}秒")

# OpenAI兼容的聊天补全接口
@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    global llm, tokenizer
    
    if llm is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="模型尚未加载完成")
    
    try:
        # 设置采样参数
        temperature = request.temperature if request.temperature is not None else 0.1
        top_p = request.top_p if request.top_p is not None else 0.8
        max_tokens = request.max_tokens if request.max_tokens is not None else 1024
        sampling_params = SamplingParams(
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
        
        # 应用聊天模板
        # messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        messages = request.messages
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # 进行推理
        start_time = time.time()
        outputs = llm.generate([prompt], sampling_params)
        inference_time = time.time() - start_time
        
        # 获取生成的文本
        generated_text = outputs[0].outputs[0].text
        
        # 计算token数量
        input_tokens = len(tokenizer.encode(prompt))
        output_tokens = len(tokenizer.encode(generated_text))
        total_tokens = input_tokens + output_tokens
        
        # 构造响应
        response = ChatCompletionResponse(
            id=f"chatcmpl-{int(time.time())}",
            created=int(time.time()),
            model=request.model,
            choices=[
                Choice(
                    index=0,
                    message=Message(
                        role="assistant",
                        content=generated_text
                    ),
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=total_tokens
            )
        )
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推理过程出错: {str(e)}")

# 健康检查接口
@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": llm is not None}

# 主函数
if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 