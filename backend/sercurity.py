"""
API安全认证模块
"""
import secrets
from datetime import datetime
from typing import List, Dict, Optional

from fastapi import HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
# 导入数据库操作模块
from database.api_key_db import (
    insert_api_key as db_create_api_key,
    query_all_api_keys as db_get_all_api_keys,
    delete_api_key as db_delete_api_key,
    query_api_key as db_get_api_key
)
import config

logger = config.setup_logging() 

# API密钥头部名称
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
# 内存中的API密钥缓存
api_key_cache: Dict[str, Dict] = {}

class APIKeyManager:
    """API密钥管理器"""

    @staticmethod
    def load_api_keys_to_cache() -> int:
        """
        从数据库加载所有API密钥到内存缓存

        Returns:
            int: 加载的API密钥数量
        """
        global api_key_cache
        try:
            # 从数据库获取所有API密钥
            api_keys = db_get_all_api_keys()

            # 清空当前缓存，但不改变引用
            api_key_cache.clear()

            # 将API密钥加载到内存缓存
            for api_key_info in api_keys:
                api_key_cache[api_key_info["api_key"]] = {
                    "name": api_key_info["name"],
                    "created_at": api_key_info["created_at"]
                }

            logger.info(f"已加载 {len(api_key_cache)} 个API密钥到内存缓存")
            return len(api_key_cache)

        except Exception as e:
            logger.error(f"加载API密钥到缓存时出错: {e}")
            return 0

    @staticmethod
    def add_api_key_to_cache(api_key: str, name: str, created_at: str) -> None:
        """
        将API密钥添加到内存缓存

        Args:
            api_key (str): API密钥
            name (str): 密钥名称
            created_at (str): 创建时间
        """
        api_key_cache[api_key] = {
            "name": name,
            "created_at": created_at
        }

    @staticmethod
    def remove_api_key_from_cache(api_key: str) -> bool:
        """
        从内存缓存中删除API密钥

        Args:
            api_key (str): 要删除的API密钥

        Returns:
            bool: 删除成功返回True，否则返回False
        """
        if api_key in api_key_cache:
            del api_key_cache[api_key]
            return True
        return False

    @staticmethod
    def is_api_key_valid(api_key: str) -> bool:
        """
        验证API密钥是否有效（从内存缓存中检查）

        Args:
            api_key (str): API密钥

        Returns:
            bool: 有效返回True，否则返回False
        """
        return api_key in api_key_cache

    @staticmethod
    def get_api_key_info(api_key: str) -> Optional[Dict]:
        """
        获取API密钥信息

        Args:
            api_key (str): API密钥

        Returns:
            Optional[Dict]: API密钥信息，无效返回None
        """
        return api_key_cache.get(api_key)


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

def validate_from_header(api_key_header: str = Depends(api_key_header)):
    """
    验证API密钥依赖函数

    参数:
    - api_key_header: 请求头中的API密钥

    返回:
    - 验证通过返回API密钥，否则抛出异常
    """
    if api_key_header and APIKeyManager.is_api_key_valid(api_key_header):
        return api_key_header
    else:
        raise HTTPException(
            status_code=401,
            detail="无效的API密钥",
            headers={"WWW-Authenticate": "API Key"}
        )


def create_new_api_key(name: str) -> Optional[Dict]:
    """
    创建新的API密钥并同步到数据库和内存缓存

    Args:
        name (str): API密钥名称

    Returns:
        Optional[Dict]: 创建成功的API密钥信息，失败返回None
    """
    api_key = secrets.token_urlsafe(32)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 保存到数据库
    if db_create_api_key(api_key, name, created_at):
        # 同步到内存缓存
        APIKeyManager.add_api_key_to_cache(api_key, name, created_at)
        return {
            "api_key": api_key,
            "name": name,
            "created_at": created_at
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="API密钥创建失败",
            headers={"WWW-Authenticate": "API Key"}
        )

def list_all_api_keys() -> List[APIKeyInfo]:
    """
    获取所有API密钥列表（从内存缓存中获取）

    Returns:
        List[Dict]: API密钥列表
    """
    return [
        APIKeyInfo(
            name=value["name"],
            created_at=value["created_at"]
        )
        for key, value in api_key_cache.items()
    ]


def remove_api_key(api_key: str) -> bool:
    """
    删除API密钥（同时删除数据库和内存缓存中的记录）

    Args:
        api_key (str): 要删除的API密钥

    Returns:
        bool: 删除成功返回True，否则返回False
    """
    # 从数据库删除
    db_success = db_delete_api_key(api_key)

    # 从内存缓存删除
    cache_success = APIKeyManager.remove_api_key_from_cache(api_key)

    # 数据库操作失败则抛出异常
    return db_success and cache_success

def reload_api_keys() -> int:
    """
    重新从数据库加载所有API密钥到内存缓存

    Returns:
        int: 加载的API密钥数量
    """
    return APIKeyManager.load_api_keys_to_cache()


def get_api_key_cache_size() -> int:
    """
    获取内存中API密钥缓存的数量

    Returns:
        int: 缓存中的API密钥数量
    """
    return len(api_key_cache)