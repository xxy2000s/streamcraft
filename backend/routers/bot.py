from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel
import re
from urllib.parse import urlparse
from services.scraper import ScraperFactory
from services.ai_classifier import ai_classifier
from models import Collection as CollectionModel, User as UserModel
from schemas import CollectionCreate, SuccessResponse
from database import get_db
from routers.auth import get_current_user
from loguru import logger

router = APIRouter()

class MessageRequest(BaseModel):
    """消息请求模型"""
    message: str
    user_id: int  # 可以通过认证获取

class BotResponse(BaseModel):
    """机器人响应模型"""
    success: bool
    message: str
    data: Dict[str, Any] = None

def extract_urls(text: str) -> list:
    """从文本中提取URL"""
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\-\.?=%&]*'
    return re.findall(url_pattern, text)

def identify_platform(url: str) -> str:
    """识别URL所属平台"""
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname.lower() if parsed_url.hostname else ""
    
    platform_mapping = {
        'xiaohongshu.com': 'xiaohongshu',
        'weixin.qq.com': 'wechat',
        'bilibili.com': 'bilibili',
        'xhslink.com': 'xiaohongshu',  # 小红书短链接
    }
    
    for domain, platform in platform_mapping.items():
        if domain in hostname:
            return platform
    
    return 'other'

def extract_content_id(url: str, platform: str) -> str:
    """从URL中提取内容ID"""
    try:
        if platform == 'xiaohongshu':
            # 小红书URL格式: https://www.xiaohongshu.com/discovery/item/xxxxxx
            match = re.search(r'/item/([a-zA-Z0-9]+)', url)
            return match.group(1) if match else ""
        elif platform == 'wechat':
            # 微信文章URL
            return url
        elif platform == 'bilibili':
            # B站URL格式: https://www.bilibili.com/video/BVxxxxxxxx
            match = re.search(r'/video/([a-zA-Z0-9]+)', url)
            return match.group(1) if match else ""
        else:
            return url
    except Exception as e:
        logger.error(f"Failed to extract content ID from {url}: {e}")
        return ""

async def process_content_async(url: str, user_id: int, db: Session):
    """异步处理内容收集"""
    try:
        # 识别平台
        platform = identify_platform(url)
        if platform == 'other':
            logger.warning(f"Unsupported platform for URL: {url}")
            return
        
        # 提取内容ID
        content_id = extract_content_id(url, platform)
        if not content_id:
            logger.warning(f"Failed to extract content ID from URL: {url}")
            return
        
        # 爬取内容
        scraper_result = ScraperFactory.scrape_content(platform, content_id)
        if not scraper_result:
            logger.warning(f"Failed to scrape content from {url}")
            return
        
        # AI分类
        ai_result = ai_classifier.classify_content(
            scraper_result.get('title', ''),
            scraper_result.get('content', ''),
            platform
        )
        
        # 生成摘要
        summary = ai_classifier.generate_summary(
            scraper_result.get('title', ''),
            scraper_result.get('content', '')
        )
        
        # 创建收藏记录
        collection_data = CollectionCreate(
            platform=platform,
            content_id=content_id,
            title=scraper_result.get('title', ''),
            content=summary,
            url=url,
            author=scraper_result.get('author', ''),
            cover_image=scraper_result.get('cover_image', ''),
            category=ai_result['categories'][0] if ai_result['categories'] else None,
            tags=ai_result['tags']
        )
        
        db_collection = CollectionModel(**collection_data.model_dump(), user_id=user_id)
        db.add(db_collection)
        db.commit()
        db.refresh(db_collection)
        
        logger.info(f"Successfully processed content: {url}")
        
    except Exception as e:
        logger.error(f"Error processing content {url}: {e}")
        db.rollback()

@router.post("/bot/message", response_model=BotResponse)
async def handle_bot_message(
    request: MessageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """处理机器人消息"""
    try:
        # 提取URL
        urls = extract_urls(request.message)
        
        if not urls:
            return BotResponse(
                success=False,
                message="未检测到有效的URL，请发送包含链接的消息"
            )
        
        # 获取用户信息（这里简化处理，实际应该通过认证）
        user = db.query(UserModel).filter(UserModel.id == request.user_id).first()
        if not user:
            return BotResponse(
                success=False,
                message="用户不存在"
            )
        
        # 处理每个URL
        processed_count = 0
        for url in urls:
            background_tasks.add_task(process_content_async, url, request.user_id, db)
            processed_count += 1
        
        return BotResponse(
            success=True,
            message=f"成功接收到{processed_count}个链接，正在后台处理...",
            data={
                "urls_processed": processed_count,
                "urls": urls
            }
        )
        
    except Exception as e:
        logger.error(f"Bot message processing failed: {e}")
        return BotResponse(
            success=False,
            message="处理消息时发生错误"
        )

@router.get("/bot/status")
async def get_bot_status():
    """获取机器人状态"""
    return {
        "status": "online",
        "supported_platforms": ["xiaohongshu", "wechat", "bilibili"],
        "version": "1.0.0"
    }