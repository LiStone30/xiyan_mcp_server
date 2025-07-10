"""
使用vLLM加载和推理本地xiyan模型的简单demo
本地模型路径：/app/src/local_model/model/XGenerationLab/XiYanSQL-QwenCoder-3B-2502
"""

from vllm import LLM, SamplingParams
import time

def main():
    # 定义模型路径
    model_path = "/app/src/local_model/model/XGenerationLab/XiYanSQL-QwenCoder-3B-2502"
    
    print(f"开始加载模型: {model_path}")
    start_time = time.time()
    
    # 使用vLLM加载模型
    llm = LLM(
        model=model_path,
        tensor_parallel_size=1,  # 根据可用GPU数量调整
        trust_remote_code=True,
        dtype="float16",  # 可以根据需要设置为"float16"或"bfloat16"以节省显存
    )
    
    load_time = time.time() - start_time
    print(f"模型加载完成，耗时: {load_time:.2f}秒")
    
    # 设置采样参数
    sampling_params = SamplingParams(
        temperature=0.1,
        top_p=0.8,
        max_tokens=1024,
    )
    
    # 定义几个测试查询
    test_queries = [
        "以下是一个SQL查询问题：如何查询所有年龄大于30岁的用户？",
        "请编写一个SQL查询，查找销售额最高的前5个产品",
        "如何优化以下SQL查询：SELECT * FROM users WHERE age > 18;"
    ]
    
    # 进行推理
    print("\n开始进行模型推理...")
    for i, query in enumerate(test_queries):
        print(f"\n测试查询 {i+1}: {query}")
        start_time = time.time()
        
        outputs = llm.generate([query], sampling_params)
        
        inference_time = time.time() - start_time
        print(f"推理耗时: {inference_time:.2f}秒")
        
        # 打印结果
        for output in outputs:
            generated_text = output.outputs[0].text
            print(f"\n生成结果:\n{generated_text}")
            print("-" * 50)

if __name__ == "__main__":
    main() 