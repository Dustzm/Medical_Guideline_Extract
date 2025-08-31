import secrets
from datetime import datetime
from typing import List, Dict

from fastapi import HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

# 存储API密钥的字典（实际项目中应该使用数据库）
api_keys: Dict[str, str] = {}

# API密钥头部名称
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


# API密钥请求模型
class APIKeyRequest(BaseModel):
    name: str  # API密钥使用者名称


# API密钥响应模型
class APIKeyResponse(BaseModel):
    api_key: str
    name: str
    created_at: str


# API密钥信息模型
class APIKeyInfo(BaseModel):
    name: str
    created_at: str


# API密钥列表响应模型
class APIKeyListResponse(BaseModel):
    keys: List[APIKeyInfo]
    total: int


def get_api_key(api_key_header: str = Depends(api_key_header)):
    """
    验证API密钥依赖函数

    参数:
    - api_key_header: 请求头中的API密钥

    返回:
    - 验证通过返回API密钥，否则抛出异常
    """
    if api_key_header in api_keys:
        return api_key_header
    else:
        raise HTTPException(
            status_code=401,
            detail="无效的API密钥",
            headers={"WWW-Authenticate": "API Key"}
        )
