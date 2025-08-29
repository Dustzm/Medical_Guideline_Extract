import asyncio
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import io
import json
from pydantic import BaseModel
from typing import List, Optional
import tempfile
import os
from typing import Dict
import threading
import time
from datetime import datetime
from service import extract_text_from_pdf, extract_info_streaming

app = FastAPI(title="知识抽取API",
              description="将医学指南文档中的知识通过大模型抽取为结构化数据",
              version="1.0.0")

# 存储任务状态的字典
tasks: Dict[str, dict] = {}

# 多线程任务状态响应体
class TaskStatus(BaseModel):
    task_id: str
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

@app.get("/")
async def root():
    return {"message": "知识抽取API服务正在运行",
            "version": "1.0.0",
            "description": "上传PDF文件以抽取其中的医学知识"}


@app.post("/extract", response_model=TaskStatus)
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
        df = extract_info_streaming(text, filename, progress_callback)
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


@app.get("/task/{task_id}", response_model=TaskStatus)
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
        status=task["status"],
        progress=task["progress"],
        message=task["message"],
        result=task.get("result"),
        start_time=task.get("start_time_str"),
        end_time=task.get("end_time_str"),
        duration=duration
    )


@app.get("/tasks", response_model=TaskListResponse)
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


@app.delete("/task/{task_id}")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8999)
