"""
API密钥数据库操作模块
"""
import json
import sqlite3
from typing import Optional, List, Dict
from .init_db import get_db_connection


def insert_api_key(api_key: str, name: str, created_at: str) -> bool:
    """
    创建新的API密钥记录

    Args:
        api_key (str): API密钥
        name (str): 密钥名称/用途
        created_at (str): 创建时间

    Returns:
        bool: 创建成功返回True，否则返回False
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO api_keys (api_key, name, created_at)
            VALUES (?, ?, ?)
        ''', (api_key, name, created_at))

        conn.commit()
        conn.close()
        return True

    except sqlite3.IntegrityError:
        # API密钥已存在
        conn.close()
        return False
    except Exception as e:
        # 其他数据库错误
        conn.close()
        print(f"创建API密钥时出错: {e}")
        return False


def query_api_key(api_key: str) -> Optional[Dict]:
    """
    根据API密钥获取密钥信息

    Args:
        api_key (str): API密钥

    Returns:
        Optional[Dict]: 密钥信息字典，如果未找到返回None
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT api_key, name, created_at
            FROM api_keys
            WHERE api_key = ?
        ''', (api_key,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "api_key": row["api_key"],
                "name": row["name"],
                "created_at": row["created_at"]
            }
        return None

    except Exception as e:
        print(f"查询API密钥时出错: {e}")
        return None


def query_all_api_keys() -> List[Dict]:
    """
    获取所有API密钥

    Returns:
        List[Dict]: API密钥列表
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT api_key, name, created_at
            FROM api_keys
            ORDER BY created_at DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "api_key": row["api_key"],
                "name": row["name"],
                "created_at": row["created_at"]
            }
            for row in rows
        ]

    except Exception as e:
        print(f"查询所有API密钥时出错: {e}")
        return []


def delete_api_key(api_key: str) -> bool:
    """
    删除指定的API密钥

    Args:
        api_key (str): 要删除的API密钥

    Returns:
        bool: 删除成功返回True，否则返回False
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM api_keys
            WHERE api_key = ?
        ''', (api_key,))

        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return changed

    except Exception as e:
        print(f"删除API密钥时出错: {e}")
        return False


def api_key_exists(api_key: str) -> bool:
    """
    检查API密钥是否存在

    Args:
        api_key (str): API密钥

    Returns:
        bool: 存在返回True，否则返回False
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 1
            FROM api_keys
            WHERE api_key = ?
            LIMIT 1
        ''', (api_key,))

        result = cursor.fetchone()
        conn.close()

        return result is not None

    except Exception as e:
        print(f"检查API密钥存在性时出错: {e}")
        return False
