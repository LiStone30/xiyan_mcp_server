from flask import Flask, request, jsonify
# import torch # require torch==2.2.2,accelerate>=0.26.0,numpy=2.2.3,modelscope
import os
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

model_name = 'XGenerationLab/XiYanSQL-QwenCoder-3B-2502'
# 创建缓存目录（如果不存在）
os.makedirs("/app/src/local_model/model", exist_ok=True)

# 构建完整的本地模型路径
model_path = "/app/src/local_model/model/XGenerationLab/XiYanSQL-QwenCoder-3B-2502"

# 直接加载本地模型
local_model = LLM(
        model=model_path,
        tensor_parallel_size=1,
        trust_remote_code=True,
        dtype="float16",
    )

local_tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

# 设置采样参数
sampling_params = SamplingParams(
    temperature=0.1,
    top_p=0.8,
    max_tokens=1024,
)

app = Flask(__name__)

@app.route('/chat/completions', methods=['POST'])
def chat_completions():
    # 获取请求中的数据
    input_data = request.json

    # 提取提示（prompt）
    messages = input_data.get('messages', [])

    if not messages:
        return jsonify({'error': 'No messages provided'})

    text = local_tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    inputs = local_tokenizer([text], return_tensors="pt")

    # 编码输入并生成响应
    generated_text = local_model.generate(inputs, sampling_params)

    # 生成响应格式
    response = {
        'id': 'xiyan',
        'object': 'chat.completion',
        'created': 1234567890,
        'model': model_name,
        'choices': [{
            'index': 0,
            'message': {
                "content":generated_text
            },
            'finish_reason': 'length'
        }]
    }
    print(generated_text)
    return jsonify(response)


if __name__ == '__main__':
    # this flask server runs on http://localhost:5090
    app.run(host='0.0.0.0', port=5090)

