from typing import Optional, Callable
import backend.config as config
import PyPDF2
import pandas as pd
import requests
import os
import json
from backend.llm import chat
from backend.prompt import build_layout_prompt
from backend.utils import parse_json_result,remove_think_tag

logger = config.setup_logging()

# 大模型API配置
API_KEY = config.settings.api_key
API_URL = config.settings.api_url
MODEL_ID = config.settings.model_id

def extract_info_streaming(text, filename, progress_callback: Optional[Callable[[int, str], None]] = None):
    """
    文档布局分析，流式输出

    Args:
        text: 输入文本
        filename: 文件名
        progress_callback: 进度回调函数，接收进度百分比和消息
    """
    if progress_callback:
        progress_callback(5, f"文档布局分析开始")

    if not text:
        logger.warning(f"{filename} 没有提取到文本内容")
        return ""

    prompt = build_layout_prompt(text)
    logger.info(f"文档布局分析准备，开始调用大模型: {filename}")

    try:
        response = chat(prompt)
        response.raise_for_status()

        logger.info(f"文档布局分析开始，流式处理 {filename} 的提取结果")
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
        # 去除<think>推理内容
        response_body = remove_think_tag(full_response)
        logger.info(f"文档布局分析完成，完成 {filename} 的内容提取")

        if progress_callback:
            progress_callback(10, f"文档布局分析完成")

        res = parse_json_result(response_body)
        return res
    except Exception as e:
        logger.error(f"文档布局分析抛出异常: {e}", exc_info=True)
        raise