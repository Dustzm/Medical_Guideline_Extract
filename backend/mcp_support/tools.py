from mcp.server.fastmcp import FastMCP
from .tool_service import judge_content
from .tool_service import knowledge_extract

mcp = FastMCP(
    name="medical_guideline_extract",
    host="0.0.0.0",
    port=8998,
    sse_path="/medicalGuideLine/knowledgeExtract/sse",
    streamable_http_path="/medicalGuideLine/knowledgeExtract/mcp"
)

@mcp.tool()
def get_content_type(content: str) -> bool:
    """
    文本内容类型判断，判断文本是否为医疗指南内容
    Args:
        content: 文本内容

    Returns:
        bool: 是否为医疗指南内容

    """
    print(f"接收参数：{content}")
    return judge_content(content)

@mcp.tool()
def get_knowledge_extract(content: str, content_type: bool) -> str:
    """
    实现文本的知识抽，抽取为结构化知识，分为六列，entity、property、value、entityTag、valueTag、level
    本方法耗时较长，应使用户知晓，抽取消耗时长在10分钟左右
    Args:
        content: 医疗指南文本
        content_type: 文本类型

    Returns: 结构化知识，通过制表符\t分隔每列，大模型应根据结果自主优化为markdown格式展示6列数据，禁止省略，禁止输出其他无关内容

    """
    if not content_type:
        return "文本不是医疗指南内容"
    result = knowledge_extract(content)
    print(f"抽取结果：\n{result}\n==================")
    return result