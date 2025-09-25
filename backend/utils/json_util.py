import json

import backend.config as config

logger = config.setup_logging()

def parse_json_result(content):
    """
   解析JSON格式的结果为字典对象

   Args:
       content: 包含JSON内容的字符串

   Returns:
       dict: 解析后的字典对象
   """
    try:
        #json格式清洗
        json_text = content.strip()
        if json_text.startswith('```json'):
            json_text = json_text[7:]
        if json_text.endswith('```'):
            json_text = json_text[:-3]
        json_text = json_text.strip()
        #解析json
        result_dict = json.loads(json_text)
        return result_dict
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        return None
