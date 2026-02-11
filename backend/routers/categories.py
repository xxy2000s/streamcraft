from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from schemas import CategoryCreate, CategoryUpdate, Category, SuccessResponse
from models import Category as CategoryModel, User as UserModel
from database import get_db
from routers.auth import get_current_user

router = APIRouter()

def category_to_dict(category_model: CategoryModel) -> dict:
    """将 SQLAlchemy Category 模型转换为字典"""
    return {
        'id': category_model.id,
        'user_id': category_model.user_id,
        'name': category_model.name,
        'description': category_model.description,
        'color': category_model.color,
        'created_at': category_model.created_at.isoformat() if category_model.created_at else None
    }

@router.post("/categories", response_model=SuccessResponse)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """创建分类"""
    # 检查该用户的分类名是否已存在
    existing_category = db.query(CategoryModel).filter(
        CategoryModel.name == category.name,
        CategoryModel.user_id == current_user.id
    ).first()

    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists for this user"
        )

    db_category = CategoryModel(**category.model_dump(), user_id=current_user.id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return SuccessResponse(data=category_to_dict(db_category), message="Category created successfully")

@router.get("/categories", response_model=SuccessResponse)
def get_categories(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """获取当前用户的分类列表"""
    categories = db.query(CategoryModel).filter(
        CategoryModel.user_id == current_user.id
    ).all()
    return SuccessResponse(data=[category_to_dict(cat) for cat in categories], message="Categories retrieved successfully")

@router.get("/categories/{category_id}", response_model=SuccessResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """获取单个分类"""
    category = db.query(CategoryModel).filter(
        CategoryModel.id == category_id,
        CategoryModel.user_id == current_user.id
    ).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return SuccessResponse(data=category_to_dict(category), message="Category retrieved successfully")

@router.put("/categories/{category_id}", response_model=SuccessResponse)
def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """更新分类"""
    db_category = db.query(CategoryModel).filter(
        CategoryModel.id == category_id,
        CategoryModel.user_id == current_user.id
    ).first()

    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    update_data = category_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)
    return SuccessResponse(data=category_to_dict(db_category), message="Category updated successfully")

@router.delete("/categories/{category_id}", response_model=SuccessResponse)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """删除分类（只能删除自己的分类）"""
    category = db.query(CategoryModel).filter(
        CategoryModel.id == category_id,
        CategoryModel.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    db.delete(category)
    db.commit()
    return SuccessResponse(message="Category deleted successfully")