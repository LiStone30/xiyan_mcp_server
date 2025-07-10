"""
使用vLLM加载和推理本地xiyan模型的简单聊天demo
本地模型路径：/app/src/local_model/model/XGenerationLab/XiYanSQL-QwenCoder-3B-2502
支持聊天格式输入
"""

from vllm import LLM, SamplingParams
from transformers import AutoTokenizer
import time

def main():
    # 定义模型路径
    model_path = "/app/src/local_model/model/XGenerationLab/XiYanSQL-QwenCoder-3B-2502"
    
    print(f"开始加载模型: {model_path}")
    start_time = time.time()
    
    # 加载tokenizer以支持聊天模板
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    
    # 使用vLLM加载模型
    llm = LLM(
        model=model_path,
        tensor_parallel_size=1,
        trust_remote_code=True,
        dtype="float16",
    )
    
    load_time = time.time() - start_time
    print(f"模型加载完成，耗时: {load_time:.2f}秒")
    
    # 设置采样参数
    sampling_params = SamplingParams(
        temperature=0.1,
        top_p=0.8,
        max_tokens=1024,
    )
    
    # 准备聊天消息
    messages = [
        {"role": "user", "content": "请帮我编写一个SQL查询，查找用户表中年龄大于25且注册时间在过去6个月内的用户"}
    ]
    
    # 应用聊天模板
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    print("\n应用聊天模板后的提示：")
    print(prompt)
    
    # 进行推理
    print("\n开始进行模型推理...")
    start_time = time.time()
    
    outputs = llm.generate([prompt], sampling_params)
    
    inference_time = time.time() - start_time
    print(f"推理耗时: {inference_time:.2f}秒")
    
    # 打印结果
    for output in outputs:
        generated_text = output.outputs[0].text
        print(f"\n生成结果:\n{generated_text}")
    
    # 交互式对话
    print("\n\n开始交互式对话 (输入 'exit' 退出):")
    conversation = messages.copy()
    
    while True:
        user_input = input("\n请输入您的问题: ")
        if user_input.lower() == 'exit':
            break
        
        # 添加用户消息
        conversation.append({"role": "user", "content": user_input})
        
        # 应用聊天模板
        prompt = tokenizer.apply_chat_template(
            conversation,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # 推理
        start_time = time.time()
        outputs = llm.generate([prompt], sampling_params)
        inference_time = time.time() - start_time
        
        # 获取回复并添加到对话中
        response = outputs[0].outputs[0].text
        conversation.append({"role": "assistant", "content": response})
        
        # 打印结果
        print(f"\n模型回复 (耗时 {inference_time:.2f}秒):\n{response}")

if __name__ == "__main__":
    main() 