from openai import OpenAI


def call_openai_sdk(**args):
    key = args.pop('key')      # 使用pop移除并获取key
    base_url = args.pop('url') # 使用pop移除并获取url
    
    client = OpenAI(
        api_key=key,
        base_url=base_url,
    )
    
    # 现在args中已经没有key和url参数了
    completion = client.chat.completions.create(
        **args
    )
    return completion

