from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from models import PlatformEnum, ContentTypeEnum

# 用户相关
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Token相关
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# 内容相关
class CollectionBase(BaseModel):
    platform: PlatformEnum
    content_id: str
    title: str
    content: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None
    cover_image: Optional[str] = None
    content_type: ContentTypeEnum = ContentTypeEnum.POST
    category: Optional[str] = None
    tags: Optional[List[str]] = None

class CollectionCreate(CollectionBase):
    pass

class CollectionUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None

class Collection(CollectionBase):
    id: int
    user_id: int
    collected_at: datetime
    created_at: datetime
    updated_at: datetime
    like_count: int = 0
    
    class Config:
        from_attributes = True

# 分类相关
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 标签相关
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 热门内容相关
class HotContentBase(BaseModel):
    platform: PlatformEnum
    title: str
    url: str
    hot_score: int = 0

class HotContentCreate(HotContentBase):
    pass

class HotContent(HotContentBase):
    id: int
    crawled_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

# 通用响应
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None