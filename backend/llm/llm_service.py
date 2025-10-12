"""
LLM调用服务模块
"""
import backend.config as config
import requests

# 大模型API配置
API_KEY = config.settings.api_key
API_URL = config.settings.api_url
MODEL_ID = config.settings.model_id

def chatStream(prompt:str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    data = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": "你是专业的医学信息提取工具，严格按照用户要求输出结果"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "stream": True  # 启用流式响应
    }
    # 发送流式请求
    response = requests.post(
        API_URL,
        headers=headers,
        json=data,
        stream=True  # 保持连接打开，接收流式数据
    )
    return response