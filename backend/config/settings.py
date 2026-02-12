from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://streamcraft:streamcraft123@localhost:3306/streamcraft"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS配置
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
    # 平台API密钥
    XIAOHONGSHU_COOKIE: Optional[str] = None
    WECHAT_COOKIE: Optional[str] = None
    BILIBILI_COOKIE: Optional[str] = None
    
    # AI配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    
    # 爬虫配置
    CHROME_DRIVER_PATH: str = "/usr/local/bin/chromedriver"
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    
    # 监控配置
    ENABLE_MONITORING: bool = True
    LOG_LEVEL: str = "INFO"
    
    # 机器人配置
    BOT_TOKEN: Optional[str] = None  # 外部机器人调用验证token
    
    class Config:
        env_file = ".env"

settings = Settings()