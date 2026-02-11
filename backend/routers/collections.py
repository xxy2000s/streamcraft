from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from schemas import CollectionCreate, CollectionUpdate, Collection, SuccessResponse
from models import Collection as CollectionModel, User as UserModel
from database import get_db
from routers.auth import get_current_user

router = APIRouter()

@router.post("/collections", response_model=Collection)
def create_collection(
    collection: CollectionCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """创建收藏"""
    db_collection = CollectionModel(**collection.model_dump(), user_id=current_user.id)
    db.add(db_collection)
    db.commit()
    db.refresh(db_collection)
    return db_collection

@router.get("/collections", response_model=List[Collection])
def get_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    platform: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """获取用户收藏列表"""
    query = db.query(CollectionModel).filter(CollectionModel.user_id == current_user.id)
    
    if platform:
        query = query.filter(CollectionModel.platform == platform)
    if category:
        query = query.filter(CollectionModel.category == category)
    
    collections = query.offset(skip).limit(limit).all()
    return collections

@router.get("/collections/{collection_id}", response_model=Collection)
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
    
    return collection

@router.put("/collections/{collection_id}", response_model=Collection)
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
    for key, value in update_data.items():
        setattr(db_collection, key, value)
    
    db.commit()
    db.refresh(db_collection)
    return db_collection

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