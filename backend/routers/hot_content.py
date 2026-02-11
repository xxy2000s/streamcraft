from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from schemas import HotContent, HotContentCreate, SuccessResponse
from models import HotContent as HotContentModel
from database import get_db
from services.hot_content_crawler import HotContentCrawler

router = APIRouter()

@router.get("/hot-content", response_model=List[HotContent])
def get_hot_content(
    platform: str = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取热门内容"""
    query = db.query(HotContentModel)
    
    if platform:
        query = query.filter(HotContentModel.platform == platform)
    
    hot_contents = query.order_by(HotContentModel.hot_score.desc()).limit(limit).all()
    return hot_contents

@router.post("/hot-content/crawl", response_model=SuccessResponse)
def crawl_hot_content(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """手动触发热门内容爬取"""
    crawler = HotContentCrawler()
    background_tasks.add_task(crawler.crawl_all_platforms, db)
    return SuccessResponse(message="Started crawling hot content")

@router.get("/hot-content/platforms")
def get_supported_platforms():
    """获取支持的平台列表"""
    return {
        "platforms": ["xiaohongshu", "wechat", "bilibili"],
        "last_updated": "2024-01-01T00:00:00Z"
    }