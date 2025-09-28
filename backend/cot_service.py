"""
旧版思维链方式抽取，当前版本弃用
"""
import os
import json
import PyPDF2
import pandas as pd
import requests
from cot_prompt import build_text_prompt
from typing import Callable, Optional
import config

logger = config.setup_logging()

# 大模型API配置
API_KEY = config.settings.api_key
API_URL = config.settings.api_url
MODEL_ID = config.settings.model_id


# 提取PDF文本内容
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        print(f"读取PDF出错 {pdf_path}: {e}")
        return ""

# 解析纯文本结果为六列数据结构
def parse_text_result(text):
    columns = ["entity", "property", "value", "entityTag", "valueTag", "level"]
    data = []

    lines = [line.strip() for line in text.split('\n') if line.strip()]

    for line in lines:
        parts = line.split('\t')
        if len(parts) >= 6:
            row = parts[:6]
        else:
            row = parts + [''] * (6 - len(parts))
        data.append(row)

    return pd.DataFrame(data, columns=columns)


# 调用API获取流式输出并实时打印
def extract_info_streaming(text, filename, progress_callback: Optional[Callable[[int, str], None]] = None):
    """
    调用API获取流式输出并实时打印

    Args:
        text: 输入文本
        filename: 文件名
        progress_callback: 进度回调函数，接收进度百分比和消息
    """
    if progress_callback:
        progress_callback(15, "开始处理文本")

    if not text:
        logger.warning(f"{filename} 没有提取到文本内容")
        columns = ["entity", "property", "value", "entityTag", "valueTag", "level"]
        return pd.DataFrame(columns=columns)

    if progress_callback:
        progress_callback(20, "构建提示词")

    prompt = build_text_prompt(text)
    logger.info(f"构建提示词完成，开始调用大模型API: {filename}")

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        data = {
            "model": MODEL_ID,
            "messages": [
                {"role": "system", "content": "你是专业的医学信息提取工具，严格按照用户要求以纯文本格式输出提取结果"},
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
        response.raise_for_status()

        logger.info(f"开始流式处理 {filename} 的提取结果")
        logger.info("-" * 50)

        if progress_callback:
            progress_callback(20, "开始接收API响应")

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
        logger.info(f"完成 {filename} 的内容提取")

        if progress_callback:
            progress_callback(90, "API响应处理完成，正在解析结果")

        # 解析完整结果并返回DataFrame
        result_df = parse_text_result(full_response)
        logger.info(f"解析完成，共提取 {len(result_df)} 条记录")

        if progress_callback:
            progress_callback(95, f"解析完成，共提取 {len(result_df)} 条记录")

        return result_df

    except Exception as e:
        logger.error(f"API调用出错: {e}", exc_info=True)
        columns = ["entity", "property", "value", "entityTag", "valueTag", "level"]
        return pd.DataFrame(columns=columns)



# 主函数
def process_pdfs(pdf_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(pdf_dir):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(pdf_dir, filename)
            print(f"开始处理: {filename}")

            # 提取PDF文本
            text = extract_text_from_pdf(pdf_path)

            # 流式提取信息并实时打印
            df = extract_info_streaming(text, filename)

            # 保存为Excel
            output_filename = os.path.splitext(filename)[0] + '.xlsx'
            output_path = os.path.join(output_dir, output_filename)

            df.to_excel(output_path, index=False)

            print(f"{filename} 处理完成，结果已保存至: {output_path}\n")


if __name__ == "__main__":
    # 配置路径
    PDF_DIRECTORY = r"C:\Users\liuf3\Desktop\指南\思维链测试\原文"  # 替换为PDF文件夹路径
    OUTPUT_DIRECTORY = r"C:\Users\liuf3\Desktop\指南\思维链测试\测试结果"  # 替换为输出文件夹路径

    # 执行处理
    process_pdfs(PDF_DIRECTORY, OUTPUT_DIRECTORY)
