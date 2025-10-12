import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import tempfile
import threading
import time
import uuid
from datetime import datetime
from typing import Dict
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request, APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from extract_service import extract_text_from_pdf, extract
from database import init_db
from config import setup_logging
from sercurity import (
    api_key_cache as api_keys,
    APIKeyManager,
    APIKeyResponse,
    APIKeyRequest,
    APIKeyListResponse,
    APIKeyInfo,
    validate_from_header,
    create_new_api_key,
    list_all_api_keys,
    remove_api_key
)
# 设置日志
logger = setup_logging()
# 初始化数据库
init_db.init_database()
logger.info("-----数据库初始化完毕-----")
# 加载API密钥
APIKeyManager.load_api_keys_to_cache()
logger.info("-----令牌缓存加载完毕-----")


app = FastAPI(title="知识抽取API",
              description="将医学指南文档中的知识通过大模型抽取为结构化数据",
              version="1.0.0")

router = APIRouter(prefix="/medicalGuideLine/knowledgeExtract")

# 存储任务状态的字典
tasks: Dict[str, dict] = {}

# 多线程任务状态响应体
class TaskStatus(BaseModel):
    task_id: str
    tag: str # 通常为文件名称，用于标记当前任务
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: str
    result: Optional[dict] = None
    start_time: Optional[str] = None  # 任务开始时间
    end_time: Optional[str] = None  # 任务结束时间
    duration: Optional[float] = None  # 任务处理时长(秒)

# 任务列表响应
class TaskListResponse(BaseModel):
    tasks: List[TaskStatus]
    total: int

@app.middleware("http")
async def api_key_check(request: Request, call_next):
    """
    api令牌校验切片
    """
    # 白名单，路径为/public则免校验
    if request.url.path.startswith("/medicalGuildLine/knowledgeExtract/public"):
        return await call_next(request)
    # 从请求头获取API密钥
    api_key = request.headers.get("X-API-Key")

    # 验证API密钥
    if not api_key or api_key not in api_keys:
        return JSONResponse(
            status_code=401,
            content={"detail": "无效的API密钥"}
        )
    return await call_next(request)
@router.get("/public/check")
async def root():
    return {"message": "知识抽取API服务正在运行",
            "version": "1.0.0",
            "description": "上传PDF文件以抽取其中的医学知识"}

@router.post("/public/create-api-key", response_model=APIKeyResponse)
async def create_api_key(key_request: APIKeyRequest):
    """
    申请新的API密钥

    参数:
    - key_request: API密钥申请信息

    返回:
    - 新生成的API密钥信息
    """
    key = create_new_api_key(key_request.name)

    return APIKeyResponse(
        api_key=key["api_key"],
        name=key["name"],
        created_at=key["created_at"]
    )


@router.get("/api-keys", response_model=APIKeyListResponse)
async def list_api_keys():
    """
    获取所有API密钥列表（需要管理员权限）

    参数:
    - api_key: API密钥（通过依赖注入验证）

    返回:
    - API密钥列表
    """
    key_list = []
    key_list = list_all_api_keys()
    return APIKeyListResponse(
        keys=key_list,
        total=len(key_list)
    )


@router.delete("/api-keys/{api_key}")
async def delete_api_key(api_key_to_delete: str):
    """
    删除指定的API密钥（需要管理员权限）

    参数:
    - api_key_to_delete: 要删除的API密钥
    - api_key: 请求者的API密钥（通过依赖注入验证）

    返回:
    - 删除结果
    """
    res = remove_api_key(api_key_to_delete)
    if res:
        return {"message": "API密钥已删除"}
    else:
        raise HTTPException(
            status_code=400,
            detail="API密钥删除失败",
            headers={"WWW-Authenticate": "API Key"}
        )


@router.post("/extract", response_model=TaskStatus)
async def extract_knowledge_from_pdf(file: UploadFile = File(...)):
    """
    从上传的PDF文件中抽取知识（异步处理）

    参数:
    - file: PDF文件

    返回:
    - 任务ID，用于轮询结果
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")

    # 创建任务ID
    task_id = str(uuid.uuid4())
    # 获取当前时间作为开始时间
    start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 初始化任务状态，用于存储当前线程任务的相关字段，并给TaskStatus赋值，TaskStatus响应体仅在接口返回时使用，不要混淆
    tasks[task_id] = {
        "status": "pending",
        "filename":f"{file.filename}",
        "progress": 0,
        "message": "任务已创建",
        "result": None,
        "start_time": time.time(),
        "start_time_str": start_time_str
    }

    try:
        # 创建临时文件保存上传的PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # 在后台线程中处理任务
        thread = threading.Thread(
            target=process_extraction_task,
            args=(task_id, tmp_file_path, file.filename)
        )
        thread.start()

        return TaskStatus(
            task_id=task_id,
            tag=file.filename,
            status="pending",
            progress=0,
            message="任务已提交，正在处理中",
            start_time=start_time_str,
            end_time=None,
            duration=None
        )

    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["message"] = f"任务提交失败: {str(e)}"
        raise HTTPException(status_code=500, detail=f"任务提交失败: {str(e)}")


def process_extraction_task(task_id: str, file_path: str, filename: str):
    """
    在后台线程中处理知识抽取任务
    """
    task = tasks[task_id]
    start_time_str = task["start_time_str"]
    start_time = task["start_time"]
    def progress_callback(progress: int, message: str):
        """进度回调函数"""
        if task_id in tasks:
            tasks[task_id].update({
                "progress": progress,
                "message": message
            })

    try:
        # 更新任务状态
        progress_callback(5, "开始处理PDF文件")
        # 提取PDF文本内容
        text = extract_text_from_pdf(file_path)
        progress_callback(10, "PDF文本提取完成，开始调用大模型API")
        task["status"] = "processing"
        # 调用API抽取信息（支持进度更新）
        df = extract(text, filename, progress_callback)
        progress_callback(90, "大模型处理完成，正在整理结果")
        # 转换DataFrame为字典列表
        data = df.to_dict('records')

        # 清理临时文件
        os.unlink(file_path)
        # 计算处理时长
        duration = time.time() - start_time
        # 获取结束时间
        end_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 完成任务
        task.update({
            "status": "completed",
            "progress": 100,
            "start_time_str":start_time_str,
            "end_time_str": end_time_str,
            "message": f"任务完成，成功从 {filename} 抽取了 {len(data)} 条记录",
            "result": {
                "filename": filename,
                "data": data,
                "count": len(data)
            },
            "duration": duration
        })

    except Exception as e:
        # 清理临时文件
        if os.path.exists(file_path):
            os.unlink(file_path)
        # 计算处理时长
        duration = time.time() - start_time
        end_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task.update({
            "status": "failed",
            "progress": 100,
            "start_time_str": start_time_str,
            "end_time_str": end_time_str,
            "message": f"处理文件时出错: {str(e)}",
            "duration": duration
        })


@router.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    获取任务状态

    参数:
    - task_id: 任务ID

    返回:
    - 任务当前状态
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    # 计算当前已用时长
    duration = task.get("duration")
    if duration is None and "start_time" in task:
        duration = time.time() - task["start_time"]

    return TaskStatus(
        task_id=task_id,
        tag=task["filename"],
        status=task["status"],
        progress=task["progress"],
        message=task["message"],
        result=task.get("result"),
        start_time=task.get("start_time_str"),
        end_time=task.get("end_time_str"),
        duration=duration
    )


@router.get("/tasks", response_model=TaskListResponse)
async def list_all_tasks():
    """
    获取所有任务列表

    返回:
    - 所有任务的状态列表
    """
    task_list = []

    for task_id, task_data in tasks.items():
        # 计算当前已用时长
        duration = task_data.get("duration")
        if duration is None and "start_time" in task_data:
            duration = time.time() - task_data["start_time"]

        task_status = TaskStatus(
            task_id=task_id,
            tag=task_data["filename"],
            status=task_data["status"],
            progress=task_data["progress"],
            message=task_data["message"],
            duration=duration,
            start_time=task_data.get("start_time_str"),
            end_time=task_data.get("end_time_str")
        )
        task_list.append(task_status)

    return TaskListResponse(
        tasks=task_list,
        total=len(task_list)
    )


@router.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """
    删除任务（清理任务记录）

    参数:
    - task_id: 任务ID

    返回:
    - 删除结果
    """
    if task_id in tasks:
        del tasks[task_id]
        return {"message": "任务记录已删除"}
    else:
        raise HTTPException(status_code=404, detail="任务不存在")

app.include_router(router)

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8999)
#     mcp.run(
#         sse=True,
#         host="0.0.0.0",
#         port=8999,
#         sse_path="/medicalGuideLine/knowledgeExtract/sse"
#     )