import os
import json
import PyPDF2
import pandas as pd
import requests
from cot_prompt import build_text_prompt

# 智谱大模型API配置
QIANWEN_API_KEY = "1e6fd966e7394d3288716f3c9479ab36.PFlsdw63m06751cI"
QIANWEN_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"


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
def extract_info_streaming(text, filename):
    if not text:
        print(f"{filename} 没有提取到文本内容")
        columns = ["entity", "property", "value", "entityTag", "valueTag", "level"]
        return pd.DataFrame(columns=columns)

    prompt = build_text_prompt(text)

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {QIANWEN_API_KEY}"
        }

        data = {
            "model": "glm-4.5",
            "messages": [
                {"role": "system", "content": "你是专业的医学信息提取工具，严格按照用户要求以纯文本格式输出提取结果"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "stream": True  # 启用流式响应
        }

        # 发送流式请求
        response = requests.post(
            QIANWEN_API_URL,
            headers=headers,
            json=data,
            stream=True  # 保持连接打开，接收流式数据
        )
        response.raise_for_status()

        print(f"\n{filename} 实时提取结果：")
        print("-" * 50)

        # 累积完整结果的变量
        full_response = ""

        # 迭代处理流式响应
        for line in response.iter_lines():
            if line:
                # 解析SSE格式（去除"data:"前缀）
                line = line.decode('utf-8').lstrip('data: ')
                if line == '[DONE]':  # 流式结束标记
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

        print("\n" + "-" * 50 + "\n")

        # 解析完整结果并返回DataFrame
        return parse_text_result(full_response)

    except Exception as e:
        print(f"API调用出错: {e}")
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