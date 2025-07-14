#模型下载
from modelscope import snapshot_download
model_dir = snapshot_download('XGenerationLab/XiYanSQL-QwenCoder-7B-2502',
    cache_dir='/app/src/local_model/model',  # 设置本地保存路径
)