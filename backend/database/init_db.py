import sqlite3
import os
from typing import Optional

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "knowledge_extract.db")

def init_database() -> bool:
    """
    初始化数据库，创建必要的表

    Returns:
        bool: 初始化是否成功
    """
    try:
        # 确保数据库目录存在
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 创建任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                message TEXT,
                result TEXT,  -- JSON格式存储
                start_time REAL,
                end_time REAL,
                start_time_str TEXT,
                end_time_str TEXT,
                duration REAL,
                filename TEXT
            )
        ''')

        # 创建API密钥表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                api_key TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')

        # 提交更改并关闭连接
        conn.commit()
        conn.close()

        print(f"数据库初始化成功: {DB_PATH}")
        return True

    except Exception as e:
        print(f"数据库初始化失败: {e}")
        return False

def get_db_connection():
    """
    获取数据库连接

    Returns:
        sqlite3.Connection: 数据库连接对象
    """
    conn = sqlite3.connect(DB_PATH)
    # 设置行工厂，使查询结果可以通过列名访问
    conn.row_factory = sqlite3.Row
    return conn

def check_database_exists() -> bool:
    """
    检查数据库文件是否存在

    Returns:
        bool: 数据库文件是否存在
    """
    return os.path.exists(DB_PATH)

def get_database_path() -> str:
    """
    获取数据库文件路径

    Returns:
        str: 数据库文件路径
    """
    return DB_PATH

if __name__ == "__main__":
    # 如果直接运行此脚本，则初始化数据库
    success = init_database()
    if success:
        print("数据库初始化完成")
    else:
        print("数据库初始化失败")
