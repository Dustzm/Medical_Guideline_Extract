from backend.extract_service import parse_text_result
from backend.llm import chat
from backend.config import setup_logging
from backend.utils import parse_llm_response
from backend.unstruct import edge_extract

logger = setup_logging()

def judge_content(content:str) -> bool:
    logger.info("调用开始")
    prompt = build_judge_prompt(content)
    response = chat(prompt, False)
    result = parse_llm_response(response)
    logger.info("大模型返回：" + result)
    return result

def knowledge_extract(content:str) -> str:
    edge_extract_info = edge_extract(content)
    return edge_extract_info


def build_judge_prompt(text:str) -> str:
    prompt = f"""
            你是一个医疗指南分析助手，你的工作是判断用户提供的文本内容是否为专业医疗指南的内容，输出时你只需要返回bool值即可，是则返回True，不是则返回False
            """
    result = f"""
            {prompt}
            判断以下文本：
            {text}
            """
    return result