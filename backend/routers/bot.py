from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import re
import json
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
from services.scraper import ScraperFactory
from services.ai_classifier import ai_classifier
from models import Collection as CollectionModel, User as UserModel, BotMessage as BotMessageModel
from schemas import CollectionCreate, SuccessResponse
from database import get_db
from routers.auth import get_current_user
from config.settings import settings
from loguru import logger

# 设置时区（北京时间 UTC+8）
BEIJING_TZ = timezone(timedelta(hours=8))

def to_beijing_time(dt: datetime) -> datetime:
    """将UTC时间转换为北京时间"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(BEIJING_TZ)

router = APIRouter()

class BotMessageRequest(BaseModel):
    """机器人消息请求模型"""
    message: str = Field(..., description="包含链接的消息内容", min_length=1)

class BotResponse(BaseModel):
    """机器人响应模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class LinkInfo(BaseModel):
    """链接信息模型"""
    url: str
    platform: str
    content_id: Optional[str] = None
    short_link: bool = False

def extract_urls(text: str) -> List[str]:
    """从文本中提取URL（支持http和https）"""
    # 更强大的URL正则表达式，支持短链接和长链接
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\-\.?=%&_\-\+]*'
    urls = re.findall(url_pattern, text)
    
    # 去重并过滤空值
    unique_urls = list(set([url for url in urls if url]))
    return unique_urls

def identify_platform(url: str) -> str:
    """识别URL所属平台"""
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname.lower() if parsed_url.hostname else ""
    
    # 支持更多平台和短链接
    platform_mapping = {
        # 小红书
        'xiaohongshu.com': 'xiaohongshu',
        'xhslink.com': 'xiaohongshu',  # 小红书短链接
        'xhslink': 'xiaohongshu',
        # 微信
        'weixin.qq.com': 'wechat',
        'mp.weixin.qq.com': 'wechat',
        # B站
        'bilibili.com': 'bilibili',
        'b23.tv': 'bilibili',  # B站短链接
        # 知乎
        'zhihu.com': 'zhihu',
        'zhuanlan.zhihu.com': 'zhihu',
        # 抖音
        'douyin.com': 'douyin',
        'v.douyin.com': 'douyin',  # 抖音短链接
    }
    
    for domain, platform in platform_mapping.items():
        if domain in hostname:
            return platform
    
    return 'other'

def extract_content_id(url: str, platform: str) -> Optional[str]:
    """从URL中提取内容ID"""
    try:
        if platform == 'xiaohongshu':
            # 小红书URL格式: https://www.xiaohongshu.com/discovery/item/xxxxxx
            # 小红书短链接: http://xhslink.com/o/375N4Taih1F
            if 'xhslink.com' in url:
                # 短链接，直接返回短链接代码
                match = re.search(r'/([a-zA-Z0-9]+)$', url)
                return match.group(1) if match else None
            else:
                match = re.search(r'/item/([a-zA-Z0-9]+)', url)
                return match.group(1) if match else None
        elif platform == 'wechat':
            # 微信文章URL
            match = re.search(r'/s/([a-zA-Z0-9_-]+)', url)
            return match.group(1) if match else None
        elif platform == 'bilibili':
            # B站URL格式: https://www.bilibili.com/video/BVxxxxxxxx
            # B站短链接: https://b23.tv/xxxxx
            if 'b23.tv' in url:
                match = re.search(r'/([a-zA-Z0-9]+)$', url)
                return match.group(1) if match else None
            else:
                match = re.search(r'/video/([a-zA-Z0-9]+)', url)
                return match.group(1) if match else None
        elif platform == 'zhihu':
            # 知乎URL格式: https://www.zhihu.com/question/xxxxx/answer/xxxxx
            match = re.search(r'/answer/(\d+)', url)
            if match:
                return match.group(1)
            match = re.search(r'/question/(\d+)', url)
            return match.group(1) if match else None
        elif platform == 'douyin':
            # 抖音URL格式: https://www.douyin.com/video/xxxxx
            # 抖音短链接: https://v.douyin.com/xxxxx
            if 'v.douyin.com' in url:
                match = re.search(r'/([a-zA-Z0-9]+)$', url)
                return match.group(1) if match else None
            else:
                match = re.search(r'/video/(\d+)', url)
                return match.group(1) if match else None
        else:
            return None
    except Exception as e:
        logger.error(f"Failed to extract content ID from {url}: {e}")
        return None

def is_short_link(url: str) -> bool:
    """判断是否为短链接"""
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname.lower() if parsed_url.hostname else ""
    
    short_link_domains = [
        'xhslink.com',
        'b23.tv',
        'v.douyin.com',
        't.cn',
        'dwz.cn',
        'bit.ly',
        'tinyurl.com'
    ]
    
    return any(domain in hostname for domain in short_link_domains)

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

def verify_bot_token(authorization: Optional[str] = Header(None)) -> bool:
    """验证机器人token"""
    if not settings.BOT_TOKEN:
        logger.warning("BOT_TOKEN not configured in settings, rejecting request")
        return False
    
    if not authorization:
        logger.warning("Missing Authorization header")
        return False
    
    # 支持Bearer token格式和直接token格式
    token = authorization
    if authorization.startswith('Bearer '):
        token = authorization[7:]
    
    if token != settings.BOT_TOKEN:
        logger.warning(f"Invalid bot token provided")
        return False
    
    return True

@router.post("/bot/parse", response_model=BotResponse)
async def parse_bot_message(
    request: BotMessageRequest,
    authorization: Optional[str] = Header(None),
    x_message_source: Optional[str] = Header(None, alias="X-Message-Source"),  # 消息来源
    db: Session = Depends(get_db)
):
    """
    机器人消息解析接口
    
    功能：
    1. 从消息中提取所有链接
    2. 识别每个链接的平台
    3. 提取链接的内容ID
    4. 判断是否为短链接
    5. 保存消息到数据库
    6. 返回解析结果
    
    请求头：
    - Authorization: Bearer {your_token} 或直接 {your_token}
    - X-Message-Source: 消息来源（可选，如：feishu、dingtalk）
    
    请求体：
    {
        "message": "年后明牌主线 算力！ http://xhslink.com/o/375N4Taih1F"
    }
    
    响应：
    {
        "success": true,
        "message": "成功解析1个链接",
        "data": {
            "total_links": 1,
            "links": [
                {
                    "url": "http://xhslink.com/o/375N4Taih1F",
                    "platform": "xiaohongshu",
                    "content_id": "375N4Taih1F",
                    "short_link": true
                }
            ]
        }
    }
    """
    # 验证token
    if not verify_bot_token(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bot token"
        )
    
    try:
        # 提取URL
        urls = extract_urls(request.message)
        
        # 解析每个链接
        link_infos = []
        for url in urls:
            platform = identify_platform(url)
            content_id = extract_content_id(url, platform)
            short_link = is_short_link(url)
            
            link_info = LinkInfo(
                url=url,
                platform=platform,
                content_id=content_id,
                short_link=short_link
            )
            link_infos.append(link_info.model_dump())
        
        # 保存消息到数据库
        bot_message = BotMessageModel(
            message=request.message,
            source=x_message_source or "manual",
            parsed_urls=json.dumps(link_infos, ensure_ascii=False),
            total_links=len(urls),
            processed=True
        )
        db.add(bot_message)
        db.commit()
        db.refresh(bot_message)
        
        logger.info(f"Bot message saved: id={bot_message.id}, links={len(urls)}")
        
        if not urls:
            return BotResponse(
                success=False,
                message="未检测到有效的URL，请发送包含链接的消息",
                data={"message_id": bot_message.id}
            )
        
        return BotResponse(
            success=True,
            message=f"成功解析{len(urls)}个链接",
            data={
                "message_id": bot_message.id,
                "total_links": len(urls),
                "links": link_infos
            }
        )
        
    except Exception as e:
        logger.error(f"Bot message parsing failed: {e}")
        return BotResponse(
            success=False,
            message="解析消息时发生错误"
        )

@router.post("/bot/message", response_model=BotResponse)
async def handle_bot_message(
    request: BotMessageRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    机器人消息处理接口（带自动保存）
    
    功能：
    1. 解析消息中的链接
    2. 自动爬取链接内容
    3. AI分类和摘要
    4. 保存到收藏库
    
    请求头：
    - Authorization: Bearer {your_token}
    
    请求体：
    {
        "message": "年后明牌主线 算力！ http://xhslink.com/o/375N4Taih1F"
    }
    """
    # 验证token
    if not verify_bot_token(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bot token"
        )
    
    try:
        # 提取URL
        urls = extract_urls(request.message)
        
        if not urls:
            return BotResponse(
                success=False,
                message="未检测到有效的URL，请发送包含链接的消息"
            )
        
        # 获取默认用户（这里使用第一个用户，或者可以通过header传递user_id）
        user = db.query(UserModel).first()
        if not user:
            return BotResponse(
                success=False,
                message="系统未配置用户，无法保存收藏"
            )
        
        # 处理每个URL
        processed_count = 0
        for url in urls:
            background_tasks.add_task(process_content_async, url, user.id, db)
            processed_count += 1
        
        return BotResponse(
            success=True,
            message=f"成功接收到{processed_count}个链接，正在后台处理并保存...",
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
        "supported_platforms": ["xiaohongshu", "wechat", "bilibili", "zhihu", "douyin"],
        "supported_short_links": ["xhslink.com", "b23.tv", "v.douyin.com"],
        "version": "2.0.0",
        "endpoints": {
            "parse": "POST /bot/parse - 仅解析链接信息",
            "message": "POST /bot/message - 解析并自动保存到收藏",
            "status": "GET /bot/status - 获取机器人状态",
            "messages": "GET /bot/messages - 获取接收到的消息列表"
        }
    }

@router.get("/bot/messages")
async def get_bot_messages(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回的记录数"),
    source: Optional[str] = Query(None, description="按来源筛选")
):
    """
    获取机器人接收到的消息列表
    
    响应：
    {
        "total": 10,
        "messages": [
            {
                "id": 1,
                "message": "原始消息内容",
                "source": "feishu",
                "parsed_urls": [...],
                "total_links": 2,
                "processed": true,
                "received_at": "2024-01-01T00:00:00Z"
            }
        ]
    }
    """
    query = db.query(BotMessageModel)
    
    if source:
        query = query.filter(BotMessageModel.source == source)
    
    total = query.count()
    messages = query.order_by(BotMessageModel.received_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "messages": [
            {
                "id": msg.id,
                "message": msg.message,
                "source": msg.source,
                "parsed_urls": json.loads(msg.parsed_urls) if msg.parsed_urls else [],
                "total_links": msg.total_links,
                "processed": msg.processed,
                "received_at": to_beijing_time(msg.received_at).isoformat()
            }
            for msg in messages
        ]
    }