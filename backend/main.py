from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from config.settings import settings
from database import engine, get_db
from models import Base
import logging
from loguru import logger

# 导入路由
from routers import auth, collections, categories, tags, hot_content, users

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 配置日志
logging.basicConfig(level=settings.LOG_LEVEL)
logger.add("logs/app.log", rotation="500 MB", level=settings.LOG_LEVEL)

app = FastAPI(
    title="StreamCraft API",
    description="多平台媒体聚合系统API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1", tags=["认证"])
app.include_router(users.router, prefix="/api/v1", tags=["用户"])
app.include_router(collections.router, prefix="/api/v1", tags=["收藏"])
app.include_router(categories.router, prefix="/api/v1", tags=["分类"])
app.include_router(tags.router, prefix="/api/v1", tags=["标签"])
app.include_router(hot_content.router, prefix="/api/v1", tags=["热门内容"])

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

@app.get("/")
async def root():
    return {"message": "Welcome to StreamCraft API"}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)