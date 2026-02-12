from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum

class PlatformEnum(str, enum.Enum):
    XIAOHONGSHU = "xiaohongshu"
    WECHAT = "wechat"
    BILIBILI = "bilibili"
    DOUYIN = "douyin"
    ZHIHU = "zhihu"
    OTHER = "other"

class ContentTypeEnum(str, enum.Enum):
    POST = "post"
    VIDEO = "video"
    ARTICLE = "article"
    IMAGE = "image"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    collections = relationship("Collection", back_populates="user")
    likes = relationship("Like", back_populates="user")

class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform = Column(Enum(PlatformEnum, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    content_id = Column(String(100), nullable=False)  # 平台原始ID
    title = Column(String(200), nullable=False)
    content = Column(Text)
    url = Column(String(500))
    author = Column(String(100))
    cover_image = Column(String(500))
    content_type = Column(Enum(ContentTypeEnum), default=ContentTypeEnum.POST)
    category = Column(String(50))  # AI分类结果（保留兼容性）
    category_id = Column(Integer, ForeignKey("categories.id"))  # 用户选择的分类
    tags = Column(Text)  # JSON格式存储标签
    collected_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="collections")
    likes = relationship("Like", back_populates="collection")
    category_ref = relationship("Category")  # 用户分类关联

class Like(Base):
    __tablename__ = "likes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False)
    liked_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="likes")
    collection = relationship("Collection", back_populates="likes")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 添加用户关联
    name = Column(String(50), nullable=False)  # 移除 unique，用户可以有同名分类
    description = Column(Text)
    color = Column(String(7))  # HEX颜色值
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User")

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class HotContent(Base):
    __tablename__ = "hot_contents"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(Enum(PlatformEnum), nullable=False)
    title = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    hot_score = Column(Integer, default=0)  # 热度分数
    crawled_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class BotMessage(Base):
    __tablename__ = "bot_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=False)  # 原始消息内容
    source = Column(String(50), default="unknown")  # 消息来源（飞书、钉钉等）
    parsed_urls = Column(Text)  # JSON格式存储解析出的URL信息
    total_links = Column(Integer, default=0)  # 解析出的链接数量
    processed = Column(Boolean, default=False)  # 是否已处理
    received_at = Column(DateTime, default=datetime.utcnow)