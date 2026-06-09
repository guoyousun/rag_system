"""
工业软件平台多模式协同智能问答系统 - FastAPI后端服务
支持文件上传、向量化处理、智能问答等功能
"""
import os
import time
import hashlib
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio

from agent.react_agent import ReactAgent
from rag.vector_store import VectorStoreService
from utils.file_handler import pdf_loader, txt_loader, get_file_md5_hex
from utils.logger_handler import logger
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.config_handler import chroma_conf

# 初始化FastAPI应用
app = FastAPI(
    title="工业软件平台智能问答系统API",
    description="支持文件上传、向量化、智能问答等功能",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
vector_store_service = VectorStoreService()
react_agent = ReactAgent()
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chroma_conf["chunk_size"],
    chunk_overlap=chroma_conf["chunk_overlap"],
    separators=chroma_conf["separators"],
    length_function=len,
)

# 上传文件目录
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 向量化进度追踪
vectorize_status = {
    "status": "idle",  # idle, processing, completed, failed
    "progress": 0,
    "total_files": 0,
    "processed_files": 0,
    "current_file": ""
}


# ==================== 数据模型 ====================

class ChatRequest(BaseModel):
    message: str


class DocumentInfo(BaseModel):
    name: str
    size: int
    md5: str
    type: str
    uploadTime: str
    status: str  # vectorized, pending


class StatsResponse(BaseModel):
    documentCount: int
    vectorCount: int
    totalSize: int


# ==================== API路由 ====================

@app.get("/")
async def root():
    return {
        "message": "工业软件平台智能问答系统API",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """智能问答接口（流式输出）"""
    try:
        async def generate_response():
            res_stream = react_agent.execute_stream(request.message)
            for chunk in res_stream:
                yield chunk
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"聊天失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """单文件上传接口"""
    try:
        # 验证文件名
        if not file.filename:
            logger.error("文件名为空")
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 验证文件类型
        allowed_extensions = ['.pdf', '.docx', '.doc', '.txt', '.xlsx', '.xls', '.csv', '.jpg', '.jpeg', '.png']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            logger.error(f"不支持的文件格式: {file_ext}")
            raise HTTPException(status_code=400, detail=f"不支持的文件格式: {file_ext}")
        
        # 确保上传目录存在
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            logger.info(f"创建上传目录: {UPLOAD_DIR}")
        
        # 保存文件
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        content = await file.read()
        
        # 验证文件大小（最大50MB）
        max_size = 50 * 1024 * 1024
        if len(content) > max_size:
            logger.error(f"文件过大: {len(content)} bytes")
            raise HTTPException(status_code=400, detail=f"文件大小超过限制（最大50MB）")
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 验证文件是否成功保存
        if not os.path.exists(file_path):
            logger.error(f"文件保存失败: {file_path}")
            raise HTTPException(status_code=500, detail="文件保存失败")
        
        # 计算MD5
        md5 = get_file_md5_hex(file_path)
        if not md5:
            logger.error(f"MD5计算失败: {file_path}")
            raise HTTPException(status_code=500, detail="文件校验失败")
        
        logger.info(f"文件上传成功: {file.filename}, 大小: {len(content)}, MD5: {md5}")
        
        return {
            "success": True,
            "filename": file.filename,
            "size": len(content),
            "md5": md5,
            "path": file_path
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@app.post("/api/upload/batch")
async def upload_files_batch(files: List[UploadFile] = File(...)):
    """批量文件上传接口"""
    results = []
    
    for file in files:
        try:
            result = await upload_file(file)
            results.append(result)
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    return {
        "success": True,
        "total": len(files),
        "results": results
    }


@app.post("/api/vectorize")
async def trigger_vectorization(background_tasks: BackgroundTasks):
    """触发向量化处理"""
    global vectorize_status
    
    if vectorize_status["status"] == "processing":
        raise HTTPException(status_code=400, detail="向量化正在进行中")
    
    # 在后台执行向量化
    background_tasks.add_task(process_vectorization)
    
    return {
        "success": True,
        "message": "向量化任务已启动"
    }


async def process_vectorization():
    """处理向量化任务"""
    global vectorize_status
    
    try:
        vectorize_status = {
            "status": "processing",
            "progress": 0,
            "total_files": 0,
            "processed_files": 0,
            "current_file": ""
        }
        
        # 获取所有待处理的文件
        files = [f for f in os.listdir(UPLOAD_DIR) 
                if os.path.isfile(os.path.join(UPLOAD_DIR, f))]
        
        vectorize_status["total_files"] = len(files)
        
        for idx, filename in enumerate(files):
            file_path = os.path.join(UPLOAD_DIR, filename)
            vectorize_status["current_file"] = filename
            
            try:
                # 加载文档
                documents = load_document(file_path)
                
                if not documents:
                    logger.warning(f"文件 {filename} 没有有效内容，跳过")
                    continue
                
                # 分片
                split_docs = text_splitter.split_documents(documents)
                
                if not split_docs:
                    logger.warning(f"文件 {filename} 分片后没有有效内容，跳过")
                    continue
                
                # 添加到向量库
                vector_store_service.vector_store.add_documents(split_docs)
                
                # 更新进度
                vectorize_status["processed_files"] = idx + 1
                vectorize_status["progress"] = int((idx + 1) / len(files) * 100)
                
                logger.info(f"文件 {filename} 向量化完成 ({idx + 1}/{len(files)})")
                
                # 模拟处理时间（实际使用时可移除）
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"文件 {filename} 向量化失败: {str(e)}", exc_info=True)
                continue
        
        vectorize_status["status"] = "completed"
        vectorize_status["progress"] = 100
        logger.info("所有文件向量化完成")
        
    except Exception as e:
        vectorize_status["status"] = "failed"
        logger.error(f"向量化任务失败: {str(e)}", exc_info=True)


def load_document(file_path: str) -> List[Document]:
    """加载不同类型的文档"""
    try:
        if file_path.endswith('.pdf'):
            return pdf_loader(file_path)
        elif file_path.endswith('.txt'):
            return txt_loader(file_path)
        elif file_path.endswith('.docx') or file_path.endswith('.doc'):
            # TODO: 添加Word文档加载器
            logger.warning(f"暂不支持Word文档: {file_path}")
            return []
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            # TODO: 添加Excel文档加载器
            logger.warning(f"暂不支持Excel文档: {file_path}")
            return []
        elif file_path.endswith('.csv'):
            # TODO: 添加CSV加载器
            logger.warning(f"暂不支持CSV文件: {file_path}")
            return []
        elif file_path.endswith(('.jpg', '.jpeg', '.png')):
            # TODO: 添加图片OCR功能
            logger.warning(f"暂不支持图片文件: {file_path}")
            return []
        else:
            logger.warning(f"不支持的文件类型: {file_path}")
            return []
    except Exception as e:
        logger.error(f"加载文档失败 {file_path}: {str(e)}", exc_info=True)
        return []


@app.get("/api/vectorize/progress")
async def get_vectorize_progress():
    """获取向量化进度"""
    return vectorize_status


@app.get("/api/documents")
async def get_documents():
    """获取文档列表"""
    try:
        documents = []
        
        # 扫描上传目录
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    md5 = get_file_md5_hex(file_path)
                    
                    documents.append({
                        "name": filename,
                        "size": stat.st_size,
                        "md5": md5,
                        "type": os.path.splitext(filename)[1][1:].upper(),
                        "uploadTime": time.strftime('%Y-%m-%d %H:%M:%S', 
                                                   time.localtime(stat.st_mtime)),
                        "status": "vectorized"  # 简化处理，实际应查询数据库
                    })
        
        return {
            "success": True,
            "data": documents,
            "total": len(documents)
        }
    
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents/{md5}")
async def delete_document(md5: str):
    """删除文档"""
    try:
        # 查找并删除文件
        deleted = False
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                file_md5 = get_file_md5_hex(file_path)
                if file_md5 == md5:
                    os.remove(file_path)
                    deleted = True
                    logger.info(f"文档已删除: {filename}")
                    break
        
        if not deleted:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return {
            "success": True,
            "message": "文档删除成功"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """获取系统统计信息"""
    try:
        # 统计文档数量
        doc_count = 0
        total_size = 0
        
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    doc_count += 1
                    total_size += os.path.getsize(file_path)
        
        # 统计向量数量（简化处理）
        vector_count = len(vector_store_service.vector_store.get()) if hasattr(vector_store_service.vector_store, 'get') else 0
        
        return {
            "success": True,
            "data": {
                "documentCount": doc_count,
                "vectorCount": vector_count,
                "totalSize": total_size
            }
        }
    
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)






