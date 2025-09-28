"""
抽取服务
"""
import os
import json
import time

import PyPDF2
import pandas as pd
import requests
from typing import Callable, Optional
import config
import unstruct

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


def extract(text, filename, progress_callback: Optional[Callable[[int, str], None]] = None):
    """
    执行知识抽取

    Args:
        text: 原文文本
        filename: 文件名
        progress_callback: 进度回调函数，接收进度百分比和消息
    """
    if progress_callback:
        progress_callback(1, "抽取开始")

    # 无文本处理
    if not text:
        logger.warning(f"{filename} 没有提取到文本内容")
        columns = ["entity", "property", "value", "entityTag", "valueTag", "level"]
        if progress_callback:
            progress_callback(100, f"没有提取到文本，抽取结束")
        return pd.DataFrame(columns=columns)
    start_time = time.time()
    # 1.文档布局分析
    layout_dict = unstruct.layout_analyze(text, filename, progress_callback)
    logger.info(f"=={filename}文档布局分析完成==")
    # 2.核心内容分析
    core_dict = unstruct.core_analyze(layout_dict['core'] , filename, progress_callback)
    logger.info(f"=={filename}核心内容分析完成==")
    # 3.边缘信息处理
    edge_text = layout_dict['base'] + "\n" + layout_dict['evidence'] + '\n' + layout_dict['other'] + '\n' + layout_dict['reference']
    edge_extract_info = unstruct.edge_extract(edge_text, filename, progress_callback)
    logger.info(f"=={filename}边缘信息抽取完成==")
    # 4.核心内容处理
    core_extract_info = ""
    logger.info(f"{filename}核心内容抽取准备，共{core_dict['total']}个问题，准备抽取")
    # 记录步长和初始进度
    step = 70/core_dict['total']
    progress = 31
    if progress_callback:
        progress_callback(31, f"开始核心内容抽取，共{core_dict['total']}个问题")
    for i, atom_item in enumerate(core_dict['atom']):
        # 循环处理每个临床问题原子
        temp_info = unstruct.core_extract(atom_item, layout_dict['reference'], layout_dict['evidence'], filename, progress_callback)
        core_extract_info += temp_info
        if progress_callback:
            progress += step
            progress_callback(progress, f"已完成第{i+1}个问题抽取")
    logger.info(f"=={filename}核心内容抽取完成==")
    #5.汇总结果
    full_response = edge_extract_info + '\n' + core_extract_info

    # 解析完整结果并返回DataFrame
    result_df = parse_text_result(full_response)
    extract_time = time.time() - start_time
    if progress_callback:
        progress_callback(100, f"已完成抽取，耗时：{extract_time}")
    logger.info(f"=={filename}解析完成，耗时：{extract_time}s==")

    # 进度汇报
    if progress_callback:
        progress_callback(100, f"解析完成")

    return result_df

# 主函数
def process_pdfs(pdf_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    # 检测pdf_dir文件夹下的pdf文件，执行知识抽取
    for filename in os.listdir(pdf_dir):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(pdf_dir, filename)
            print(f"开始处理: {filename}")
            # 提取PDF文本
            text = extract_text_from_pdf(pdf_path)
            # 流式提取信息并实时打印
            df = extract(text, filename)
            # 保存为Excel
            output_filename = os.path.splitext(filename)[0] + '.xlsx'
            output_path = os.path.join(output_dir, output_filename)
            df.to_excel(output_path, index=False)
            print(f"=={filename} 处理完成，结果已保存至: {output_path}==\n")

if __name__ == "__main__":
    # 配置路径
    PDF_DIRECTORY = r"/home/ontoweb2025/czm2025/pytest"  # 替换为PDF文件夹路径
    OUTPUT_DIRECTORY = r"/home/ontoweb2025/czm2025/pytest"  # 替换为输出文件夹路径

    # 执行处理
    process_pdfs(PDF_DIRECTORY, OUTPUT_DIRECTORY)
