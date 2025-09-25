import re

def remove_think_tag(text):
    """
        去除指定标签及其内容，只保留标签之后的内容

        Args:
            text: 原始字符串
            tag: 要去除的标签名，默认为't'

        Returns:
            处理后的字符串
        """
    # 使用正则表达式匹配标签及其内容，并替换为空字符串
    pattern = '<think>.*?</think>'
    result = re.sub(pattern, '', text, flags=re.DOTALL)
    return result.strip()  # 去除可能的前后空格