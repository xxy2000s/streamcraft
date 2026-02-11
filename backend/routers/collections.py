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

router = APIRouter()

def parse_url_content(url: str) -> dict:
    """解析URL内容，自动识别平台并提取信息"""
    try:
        response = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
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
        
        # 识别平台
        platform = 'OTHER'
        if 'xiaohongshu.com' in url:
            platform = 'XIAOHONGSHU'
        elif 'weixin.qq.com' in url or 'mp.weixin.qq.com' in url:
            platform = 'WECHAT'
        elif 'bilibili.com' in url:
            platform = 'BILIBILI'
        
        # 提取ID
        content_id = url.split('/')[-1] or url
        
        return {
            'platform': platform,
            'content_id': content_id,
            'title': title,
            'content': description,
            'url': url,
            'cover_image': cover_image,
            'content_type': 'POST' if 'bilibili' not in url else 'VIDEO'
        }
    except Exception as e:
        return {
            'platform': 'OTHER',
            'content_id': url.split('/')[-1] or url,
            'title': '',
            'content': '',
            'url': url,
            'cover_image': '',
            'content_type': 'POST'
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