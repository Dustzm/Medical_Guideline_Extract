"""
边缘信息抽取
"""
import os
import json
import PyPDF2
import pandas as pd
import requests
from backend.llm import chatStream
from backend.prompt import build_others_prompt
from typing import Callable, Optional
import backend.config as config
from backend.utils import remove_think_tag

logger = config.setup_logging()

# 大模型API配置
API_KEY = config.settings.api_key
API_URL = config.settings.api_url
MODEL_ID = config.settings.model_id

def extract_info_streaming(text, filename, progress_callback: Optional[Callable[[int, str], None]] = None):
    """
    边缘信息抽取

    Args:
        text: 边缘信息文本
        filename: 文件名
        progress_callback: 进度回调函数，接收进度百分比和消息
    """
    if progress_callback:
        progress_callback(25, f"边缘信息文本抽取开始")

    prompt = build_others_prompt(text)
    logger.info(f"边缘信息抽取准备: {filename}")

    try:
        response = chatStream(prompt)
        response.raise_for_status()

        logger.info(f"开始流式处理 {filename} 的提取结果")
        logger.info("-" * 50)

        # 累积完整结果的变量
        full_response = ""
        line_count = 0

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
                        line_count += 1
                        # 每处理10行更新一次进度（模拟）
                        if line_count % 10 == 0 and progress_callback:
                            progress = min(10 + (line_count // 10), 80)  # 10-80%之间
                            progress_callback(progress, f"已处理 {line_count} 行响应数据")
                except json.JSONDecodeError:
                    continue
                except KeyError:
                    continue

        logger.info("-" * 50)
        response_body = remove_think_tag(full_response)
        if progress_callback:
            progress_callback(30,f"边缘信息抽取完成")
        logger.info(f"边缘信息完成抽取： {filename} ")
        return response_body

    except Exception as e:
        logger.error(f"边缘信息抽取抛出异常: {e}", exc_info=True)
        raise
