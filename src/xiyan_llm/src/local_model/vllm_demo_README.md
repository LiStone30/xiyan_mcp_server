# XiYanSQL-QwenCoder 模型使用vLLM加载推理演示

此目录包含了使用vLLM加载和推理本地XiYanSQL-QwenCoder-3B模型的几个示例脚本。

## 环境要求

- vllm==0.6.1
- vllm-flash-attn==2.6.1
- transformers==4.53.1
- torch (推荐2.2以上版本)

## 模型路径

本地模型路径：`/app/src/local_model/model/XGenerationLab/XiYanSQL-QwenCoder-3B-2502`

## 示例脚本说明

### 1. 简单演示 (xiyan_vllm_simple_demo.py)

最简单的单次推理演示，加载模型并执行单个SQL查询。

```bash
python src/local_model/xiyan_vllm_simple_demo.py
```

### 2. 批量推理演示 (xiyan_vllm_demo.py)

包含多个SQL查询样例的批量推理演示，同时展示了推理耗时。

```bash
python src/local_model/xiyan_vllm_demo.py
```

### 3. 聊天对话演示 (xiyan_vllm_chat_demo.py)

支持聊天格式的交互式对话演示，使用transformers的聊天模板。

```bash
python src/local_model/xiyan_vllm_chat_demo.py
```

## 常见参数调整

在脚本中可调整以下参数以满足不同需求：

- **tensor_parallel_size**: 根据可用GPU数量调整，默认为1
- **dtype**: 可设置为"float16"或"bfloat16"以节省显存
- **temperature**: 控制生成文本的随机性，值越低越确定性
- **top_p**: 控制生成文本的多样性
- **max_tokens**: 控制生成文本的最大长度

## 注意事项

- 首次加载模型可能需要较长时间
- 确保有足够的GPU内存运行模型
- 对于更复杂的应用场景，可以基于这些示例进行扩展 