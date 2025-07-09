from flask import Flask, request, jsonify
from modelscope import AutoModelForCausalLM, AutoTokenizer
import torch # require torch==2.2.2,accelerate>=0.26.0,numpy=2.2.3,modelscope
import os


model_name = 'XGenerationLab/XiYanSQL-QwenCoder-3B-2502'
# 创建缓存目录（如果不存在）
os.makedirs("/app/src/local_model/model", exist_ok=True)

# 构建完整的本地模型路径
local_model_path = "/app/src/local_model/model/XGenerationLab/XiYanSQL-QwenCoder-3B-2502"

# 直接加载本地模型
local_model = AutoModelForCausalLM.from_pretrained(
    local_model_path,  # 使用本地路径代替模型ID
    device_map='cuda:0',
    torch_dtype=torch.float32,
    local_files_only=True  # 确保只使用本地文件
)

local_tokenizer = AutoTokenizer.from_pretrained(
    local_model_path,
    local_files_only=True
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
    generated_ids = local_model.generate(inputs['input_ids'], max_new_tokens=1024,
    temperature=0.1,
    top_p=0.8,
    do_sample=True)

    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, generated_ids)
    ]
    generated_text = local_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]


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

