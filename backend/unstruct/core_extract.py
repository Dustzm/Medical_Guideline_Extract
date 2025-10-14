"""
核心内容抽取
"""
import os
import json
import PyPDF2
import pandas as pd
import requests
from backend.llm import chat
from backend.prompt import build_core_prompt
from typing import Callable, Optional
import backend.config as config
from backend.utils import remove_think_tag

logger = config.setup_logging()

# 大模型API配置
API_KEY = config.settings.api_key
API_URL = config.settings.api_url
MODEL_ID = config.settings.model_id

def extract_info_streaming(core_text, reference, ev_definition, filename, progress_callback: Optional[Callable[[int, str], None]] = None):
    """
    核心信息抽取

    Args:
        core_text: 核心内容文本
        reference: 参考文献文本
        ev_definition: 推荐强度与证据质量定义文本
        filename: 文件名
        progress_callback: 进度回调函数，接收进度百分比和消息
    """
    prompt = build_core_prompt(core_text, reference, ev_definition)
    logger.info(f"核心内容抽取准备: {filename}")

    try:
        response = chat(prompt)
        response.raise_for_status()

        logger.info(f"核心内容抽取： {filename}")
        logger.info("-" * 50)

        # 累积完整结果的变量
        full_response = ""
        # 迭代处理流式响应
        for line in response.iter_lines():
            if line:
                # 解析SSE格式（去除"data:"前缀）
                line = line.decode('utf-8').lstrip('data: ')
                if line == '[DONE]':  # 流式结束标记
                    logger.info("流式响应处理完成")
                    break
                try:
                    chunk = json.loads(line)
                    # 提取当前片段的内容
                    content = chunk["choices"][0]["delta"].get("content", "")
                    if content:
                        print(content, end='', flush=True)  # 实时打印
                        full_response += content  # 累积内容
                except json.JSONDecodeError:
                    continue
                except KeyError:
                    continue
        logger.info("-" * 50)
        response_body = remove_think_tag(full_response)
        logger.info(f"核心内容完成抽取： {filename} ")
        return response_body + "\n"
    except Exception as e:
        logger.error(f"核心内容抽取抛出异常: {e}", exc_info=True)
        raise
