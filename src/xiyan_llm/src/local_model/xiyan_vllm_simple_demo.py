"""
使用vLLM加载和推理本地xiyan模型的最简单demo
本地模型路径：/app/src/local_model/model/XGenerationLab/XiYanSQL-QwenCoder-3B-2502
"""

from vllm import LLM, SamplingParams

# 定义模型路径
model_path = "/app/src/local_model/model/XGenerationLab/XiYanSQL-QwenCoder-3B-2502"

# 加载模型
print(f"正在加载模型: {model_path}")
llm = LLM(
    model=model_path,
    tensor_parallel_size=1,
    trust_remote_code=True,
    dtype="float16",
)
print("模型加载完成")

# 设置采样参数
sampling_params = SamplingParams(
    temperature=0.1,
    top_p=0.8,
    max_tokens=1024,
)

# 定义查询
query = "请为我编写一个SQL查询，查找商品表中价格低于100且库存大于50的商品"

# 进行推理
print(f"\n查询: {query}")
print("\n推理中...")

outputs = llm.generate([query], sampling_params)

# 打印结果
generated_text = outputs[0].outputs[0].text
print(f"\n生成结果:\n{generated_text}") 