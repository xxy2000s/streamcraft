from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from schemas import CollectionCreate, CollectionUpdate, Collection, SuccessResponse
from models import Collection as CollectionModel, User as UserModel, Like as LikeModel
from database import get_db
from routers.auth import get_current_user
from datetime import datetime
import json
import re
import requests
import json
import codecs
from urllib.parse import urlparse, parse_qs

router = APIRouter()

def parse_bilibili_url(url: str) -> dict:
    """解析B站URL"""
    try:
        # 提取视频ID
        # 支持 https://www.bilibili.com/video/BVxxxxx 或 https://b23.tv/xxxxx
        bv_match = re.search(r'(BV[a-zA-Z0-9]+)', url)
        if not bv_match:
            return {'success': False}
        
        bvid = bv_match.group(1)
        
        # 调用B站API获取视频信息
        api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.bilibili.com'
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('code') != 0:
            return {'success': False}
        
        info = data['data']
        
        return {
            'success': True,
            'platform': 'bilibili',
            'content_id': bvid,
            'title': info.get('title', ''),
            'content': info.get('desc', ''),
            'url': f"https://www.bilibili.com/video/{bvid}",
            'cover_image': info.get('pic', ''),
            'author': info.get('owner', {}).get('name', ''),
            'content_type': 'video'
        }
    except Exception as e:
        return {'success': False}

def parse_xiaohongshu_url(url: str) -> dict:
    """解析小红书URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Referer': 'https://www.xiaohongshu.com'
        }
        
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        response.raise_for_status()
        
        # 提取标题 - 尝试多种方式
        title = ''
        title_match = re.search(r'"title":"([^"]+)"', response.text)
        if not title_match:
            title_match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE)
        if title_match:
            title_match_text = title_match.group(1).strip()
            try:
                # 尝试直接解析为 JSON 字符串
                title = json.loads(f'"{title_match_text}"')
            except:
                try:
                    # 如果是字面形式的 \uXXXX，使用 codecs.decode
                    if '\\u' in title_match_text:
                        title = codecs.decode(title_match_text, 'unicode-escape')
                    else:
                        title = title_match_text
                except:
                    title = title_match_text
        
        # 提取描述
        desc = ''
        desc_match = re.search(r'"desc":"([^"]+)"', response.text)
        if desc_match:
            desc_match_text = desc_match.group(1)
            try:
                desc = json.loads(f'"{desc_match_text}"')
            except:
                try:
                    if '\\u' in desc_match_text:
                        desc = codecs.decode(desc_match_text, 'unicode-escape')
                    else:
                        desc = desc_match_text
                except:
                    desc = desc_match_text
        
        # 提取封面图
        cover_image = ''
        image_patterns = [
            r'"cover":"([^"]+)"',
            r'"defaultCover":"([^"]+)"',
            r'"imageDefault":"([^"]+)"',
            r'"key":"([^"]+)"',
            r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"',
            r'<meta[^>]*property="twitter:image"[^>]*content="([^"]+)"'
        ]
        for pattern in image_patterns:
            if not cover_image:
                image_match = re.search(pattern, response.text, re.IGNORECASE)
                if image_match:
                    cover_image = image_match.group(1)
                    break
        
        # 提取作者
        author = ''
        author_match = re.search(r'"nickname":"([^"]+)"', response.text)
        if author_match:
            author_match_text = author_match.group(1)
            try:
                author = json.loads(f'"{author_match_text}"')
            except:
                try:
                    if '\\u' in author_match_text:
                        author = codecs.decode(author_match_text, 'unicode-escape')
                    else:
                        author = author_match_text
                except:
                    author = author_match_text
        
        # 提取笔记ID
        note_id = url.split('/')[-1]
        note_id_match = re.search(r'/explore/([a-f0-9]+)', url)
        if note_id_match:
            note_id = note_id_match.group(1)
        
        # 判断类型（视频或图文）
        content_type = 'video' if 'video' in response.text.lower() else 'post'
        
        return {
            'success': True,
            'platform': 'xiaohongshu',
            'content_id': note_id,
            'title': title,
            'content': desc,
            'url': url,
            'cover_image': cover_image,
            'author': author,
            'content_type': content_type
        }
    except Exception as e:
        return {'success': False}

def parse_douyin_url(url: str) -> dict:
    """解析抖音URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Referer': 'https://www.douyin.com'
        }
        
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        response.raise_for_status()
        
        # 辅助函数：解码 Unicode 转义字符
        def decode_unicode(text):
            if not text:
                return text
            try:
                # 尝试使用 codecs.decode
                decoded = text.encode('utf-8').decode('unicode-escape')
                return decoded
            except:
                try:
                    # 尝试使用 json.loads
                    return json.loads(f'"{text}"')
                except:
                    return text
        
        # 提取视频ID - 支持多种格式
        video_id = url.split('/')[-1]
        video_id_match = re.search(r'/video/(\d+)', response.url)
        if video_id_match:
            video_id = video_id_match.group(1)
        else:
            video_id_match = re.search(r'modal_id=(\d+)', url)
            if video_id_match:
                video_id = video_id_match.group(1)
        
        # 提取标题 - 尝试多种方式
        title = ''
        title_patterns = [
            r'"title":"([^"]+)"',
            r'"desc":"([^"]+)"',
            r'<title>(.*?)</title>'
        ]
        for pattern in title_patterns:
            if not title:
                title_match = re.search(pattern, response.text, re.IGNORECASE | re.DOTALL)
                if title_match:
                    title_match_text = title_match.group(1)
                    # 处理 Unicode 转义字符
                    try:
                        # 尝试直接解析为 JSON 字符串
                        title = json.loads(f'"{title_match_text}"')
                    except:
                        try:
                            # 如果是字面形式的 \uXXXX，使用 codecs.decode
                            if '\\u' in title_match_text:
                                title = codecs.decode(title_match_text, 'unicode-escape')
                            else:
                                title = title_match_text
                        except:
                            title = title_match_text
                    title = title.strip()
                    break
        
        # 提取描述
        desc = ''
        desc_match = re.search(r'"desc":"([^"]+)"', response.text)
        if desc_match:
            desc_match_text = desc_match.group(1)
            try:
                desc = json.loads(f'"{desc_match_text}"')
            except:
                try:
                    if '\\u' in desc_match_text:
                        desc = codecs.decode(desc_match_text, 'unicode-escape')
                    else:
                        desc = desc_match_text
                except:
                    desc = desc_match_text
        
        # 提取封面图 - 尝试多种方式
        cover_image = ''
        image_patterns = [
            r'"cover":"([^"]+)"',
            r'"thumbnail":"([^"]+)"',
            r'"originCover":"([^"]+)"',
            r'"dynamicCover":"([^"]+)"',
            r'"staticCover":"([^"]+)"',
            r'"videoCover":"([^"]+)"',
            r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"',
            r'<meta[^>]*property="twitter:image"[^>]*content="([^"]+)"'
        ]
        for pattern in image_patterns:
            if not cover_image:
                image_match = re.search(pattern, response.text, re.IGNORECASE)
                if image_match:
                    cover_image = image_match.group(1)
                    break
        
        # 提取作者
        author = ''
        author_match = re.search(r'"nickname":"([^"]+)"', response.text)
        if author_match:
            author_match_text = author_match.group(1)
            try:
                author = json.loads(f'"{author_match_text}"')
            except:
                try:
                    if '\\u' in author_match_text:
                        author = codecs.decode(author_match_text, 'unicode-escape')
                    else:
                        author = author_match_text
                except:
                    author = author_match_text
        
        return {
            'success': True,
            'platform': 'douyin',
            'content_id': video_id,
            'title': title or desc,
            'content': desc,
            'url': url,
            'cover_image': cover_image,
            'author': author,
            'content_type': 'video'
        }
    except Exception as e:
        return {'success': False}

def parse_wechat_url(url: str) -> dict:
    """解析微信文章URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://mp.weixin.qq.com'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 提取标题（微信文章标题在 msg_title 或 meta 标签中）
        title_match = re.search(r'msg_title\s*=\s*["\']([^"\']+)["\']', response.text)
        if not title_match:
            title_match = re.search(r'<meta property="og:title" content="([^"]+)"', response.text)
        title = title_match.group(1) if title_match else ''
        
        # 提取描述
        desc_match = re.search(r'msg_desc\s*=\s*["\']([^"\']+)["\']', response.text)
        if not desc_match:
            desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', response.text)
        desc = desc_match.group(1) if desc_match else ''
        
        # 提取封面图
        image_match = re.search(r'msg_cdn_url\s*=\s*["\']([^"\']+)["\']', response.text)
        if not image_match:
            image_match = re.search(r'<meta property="og:image" content="([^"]+)"', response.text)
        cover_image = image_match.group(1) if image_match else ''
        
        # 提取作者
        author_match = re.search(r'<meta name="author" content="([^"]+)"', response.text)
        author = author_match.group(1) if author_match else ''
        
        # 提取文章ID
        article_id_match = re.search(r's\/([a-f0-9]+)', url)
        article_id = article_id_match.group(1) if article_id_match else url.split('/')[-1]
        
        return {
            'success': True,
            'platform': 'wechat',
            'content_id': article_id,
            'title': title,
            'content': desc,
            'url': url,
            'cover_image': cover_image,
            'author': author,
            'content_type': 'post'
        }
    except Exception as e:
        return {'success': False}

def parse_url_content(url: str) -> dict:
    """解析URL内容，自动识别平台并提取信息"""
    try:
        # 识别平台并调用对应的解析函数
        if 'bilibili.com' in url or 'b23.tv' in url:
            result = parse_bilibili_url(url)
            if result.get('success'):
                return result
        
        elif 'xiaohongshu.com' in url or 'xhslink.com' in url:
            result = parse_xiaohongshu_url(url)
            if result.get('success'):
                return result
        
        elif 'douyin.com' in url or 'v.douyin.com' in url:
            result = parse_douyin_url(url)
            if result.get('success'):
                return result
        
        elif 'weixin.qq.com' in url or 'mp.weixin.qq.com' in url:
            result = parse_wechat_url(url)
            if result.get('success'):
                return result
        
        # 通用解析（作为后备方案）
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, timeout=5, headers=headers)
        response.raise_for_status()
        
        # 提取title
        title_match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ''
        
        # 提取description
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', response.text, re.IGNORECASE)
        description = desc_match.group(1) if desc_match else ''
        
        # 提取og:image
        image_match = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']*)["\']', response.text, re.IGNORECASE)
        cover_image = image_match.group(1) if image_match else ''
        
        # 提取ID
        content_id = url.split('/')[-1] or url
        
        # 识别平台
        platform = 'other'
        if 'xiaohongshu.com' in url:
            platform = 'xiaohongshu'
        elif 'weixin.qq.com' in url or 'mp.weixin.qq.com' in url:
            platform = 'wechat'
        elif 'bilibili.com' in url or 'b23.tv' in url:
            platform = 'bilibili'
        elif 'douyin.com' in url or 'v.douyin.com' in url:
            platform = 'douyin'
        
        return {
            'platform': platform,
            'content_id': content_id,
            'title': title,
            'content': description,
            'url': url,
            'cover_image': cover_image,
            'content_type': 'video' if 'bilibili' in url or 'douyin' in url else 'post'
        }
    except Exception as e:
        return {
            'platform': 'other',
            'content_id': url.split('/')[-1] or url,
            'title': '',
            'content': '',
            'url': url,
            'cover_image': '',
            'content_type': 'post'
        }

@router.post("/collections/parse-url", response_model=SuccessResponse)
def parse_url(
    url_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """解析URL，自动提取内容信息"""
    url = url_data.get('url', '')
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL is required"
        )
    
    result = parse_url_content(url)
    return SuccessResponse(data=result, message="URL parsed successfully")

def collection_to_dict(collection_model: CollectionModel, like_count: int = 0) -> dict:
    """将 SQLAlchemy Collection 模型转换为字典"""
    return {
        'id': collection_model.id,
        'user_id': collection_model.user_id,
        'platform': collection_model.platform,
        'content_id': collection_model.content_id,
        'title': collection_model.title,
        'content': collection_model.content,
        'url': collection_model.url,
        'author': collection_model.author,
        'cover_image': collection_model.cover_image,
        'content_type': collection_model.content_type,
        'category': collection_model.category,
        'category_id': collection_model.category_id,
        'tags': json.loads(collection_model.tags) if collection_model.tags else None,
        'collected_at': collection_model.collected_at.isoformat() if collection_model.collected_at else None,
        'created_at': collection_model.created_at.isoformat() if collection_model.created_at else None,
        'updated_at': collection_model.updated_at.isoformat() if collection_model.updated_at else None,
        'like_count': like_count
    }

@router.post("/collections", response_model=SuccessResponse)
def create_collection(
    collection: CollectionCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """创建收藏"""
    # 处理 tags 字段
    collection_data = collection.model_dump()
    if collection_data.get('tags') and len(collection_data['tags']) > 0:
        collection_data['tags'] = json.dumps(collection_data['tags'])
    else:
        collection_data['tags'] = None
    
    db_collection = CollectionModel(**collection_data, user_id=current_user.id)
    db.add(db_collection)
    db.commit()
    db.refresh(db_collection)
    return SuccessResponse(data=collection_to_dict(db_collection), message="Collection created successfully")

@router.get("/collections", response_model=SuccessResponse)
def get_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    platform: Optional[str] = None,
    category: Optional[str] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """获取用户收藏列表"""
    query = db.query(CollectionModel).filter(CollectionModel.user_id == current_user.id)

    if platform:
        query = query.filter(CollectionModel.platform == platform)
    if category:
        query = query.filter(CollectionModel.category == category)
    if category_id:
        query = query.filter(CollectionModel.category_id == category_id)

    collections = query.offset(skip).limit(limit).all()

    # 添加点赞计数并转换为字典
    result = []
    for collection in collections:
        like_count = db.query(func.count(LikeModel.id)).filter(
            LikeModel.collection_id == collection.id
        ).scalar() or 0
        result.append(collection_to_dict(collection, like_count))

    return SuccessResponse(data=result, message="Collections retrieved successfully")

@router.get("/collections/{collection_id}", response_model=SuccessResponse)
def get_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """获取单个收藏详情"""
    collection = db.query(CollectionModel).filter(
        CollectionModel.id == collection_id,
        CollectionModel.user_id == current_user.id
    ).first()

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    # 添加点赞计数
    like_count = db.query(func.count(LikeModel.id)).filter(
        LikeModel.collection_id == collection.id
    ).scalar() or 0

    return SuccessResponse(data=collection_to_dict(collection, like_count), message="Collection retrieved successfully")

@router.put("/collections/{collection_id}", response_model=SuccessResponse)
def update_collection(
    collection_id: int,
    collection_update: CollectionUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """更新收藏"""
    db_collection = db.query(CollectionModel).filter(
        CollectionModel.id == collection_id,
        CollectionModel.user_id == current_user.id
    ).first()

    if not db_collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    update_data = collection_update.model_dump(exclude_unset=True)
    # 处理 tags 字段
    if 'tags' in update_data:
        if update_data['tags'] is not None and len(update_data['tags']) > 0:
            update_data['tags'] = json.dumps(update_data['tags'])
        else:
            update_data['tags'] = None
    
    for key, value in update_data.items():
        setattr(db_collection, key, value)

    db.commit()
    db.refresh(db_collection)
    return SuccessResponse(data=collection_to_dict(db_collection), message="Collection updated successfully")

@router.delete("/collections/{collection_id}", response_model=SuccessResponse)
def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """删除收藏"""
    collection = db.query(CollectionModel).filter(
        CollectionModel.id == collection_id,
        CollectionModel.user_id == current_user.id
    ).first()

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    db.delete(collection)
    db.commit()
    return SuccessResponse(message="Collection deleted successfully")

@router.post("/collections/{collection_id}/like", response_model=SuccessResponse)
def like_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """点赞收藏"""
    # 检查收藏是否存在
    collection = db.query(CollectionModel).filter(
        CollectionModel.id == collection_id
    ).first()

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    # 检查是否已经点赞
    existing_like = db.query(LikeModel).filter(
        LikeModel.user_id == current_user.id,
        LikeModel.collection_id == collection_id
    ).first()

    if existing_like:
        return SuccessResponse(message="Already liked")

    # 创建点赞
    like = LikeModel(user_id=current_user.id, collection_id=collection_id)
    db.add(like)
    db.commit()
    return SuccessResponse(message="Liked successfully")

@router.delete("/collections/{collection_id}/like", response_model=SuccessResponse)
def unlike_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """取消点赞收藏"""
    # 查找点赞记录
    like = db.query(LikeModel).filter(
        LikeModel.user_id == current_user.id,
        LikeModel.collection_id == collection_id
    ).first()

    if not like:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like not found"
        )

    db.delete(like)
    db.commit()
    return SuccessResponse(message="Unliked successfully")