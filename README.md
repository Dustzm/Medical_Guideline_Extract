# 知识抽取API

这是一个基于FastAPI的知识抽取系统，可以将医学指南文档中的信息抽取为结构化数据。

## 功能特性

- 通过API接口上传PDF文件进行知识抽取
- 支持直接输入文本进行知识抽取
- 返回结构化的JSON数据
- 保留原有的PDF批量处理功能

## 安装依赖
```bash
pip install -r requirements.txt
```
## 启动服务
```bash
cd backend
python main.py
```
服务将运行在 `http://localhost:8999`
## API接口

### 1. 根路径
- **URL**: `GET /`
- **描述**: 检查API服务是否运行正常

### 2. 上传PDF文件抽取知识
- **URL**: `POST /extract`
- **描述**: 上传PDF文件并抽取其中的知识
- **参数**: 
  - `file`: PDF文件 (multipart/form-data)
- **返回**: 结构化的抽取结果

### 3. 输入文本抽取知识
- **URL**: `POST /extract_text`
- **描述**: 直接输入文本内容进行知识抽取
- **参数**: 
  - `text`: 需要抽取的文本内容 (application/json)
- **返回**: 结构化的抽取结果