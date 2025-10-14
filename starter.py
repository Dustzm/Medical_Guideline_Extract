# starter.py
import threading
import uvicorn
from backend import app
from backend.mcp_support import mcp
from backend.config import setup_logging
logger = setup_logging()

class ProjectStarter:
    """项目启动管理类"""

    @staticmethod
    def start_fastapi_service():
        """启动FastAPI服务"""
        logger.info("fastAPI服务启动")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8999
        )


    @staticmethod
    def start_mcp_service():
        """启动MCP服务"""
        logger.info("mcp服务启动")
        mcp.run(transport='sse')


    def start_all_services(self):
        """启动所有服务"""
        # 在单独线程中启动MCP服务
        mcp_thread = threading.Thread(target=self.start_mcp_service)
        mcp_thread.daemon = True
        mcp_thread.start()
        # 在主线程中启动FastAPI服务
        self.start_fastapi_service()


if __name__ == "__main__":
    starter = ProjectStarter()
    starter.start_all_services()