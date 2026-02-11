import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from models import HotContent as HotContentModel, PlatformEnum
from loguru import logger
import time
from sqlalchemy.orm import Session

class HotContentCrawler:
    """热门内容爬虫"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def crawl_xiaohongshu_hot(self) -> List[Dict]:
        """爬取小红书热门内容"""
        # 注意：这只是一个示例实现，实际的小红书爬虫需要更复杂的处理
        hot_contents = []
        
        try:
            # 这里应该调用小红书的实际API或使用更复杂的爬虫逻辑
            # 目前返回模拟数据
            mock_data = [
                {
                    "title": "今日热门：秋季穿搭指南",
                    "url": "https://www.xiaohongshu.com/discovery/item/abc123",
                    "hot_score": 950
                },
                {
                    "title": "美食推荐：网红餐厅打卡",
                    "url": "https://www.xiaohongshu.com/discovery/item/def456",
                    "hot_score": 890
                }
            ]
            
            for item in mock_data:
                hot_contents.append({
                    "platform": PlatformEnum.XIAOHONGSHU,
                    "title": item["title"],
                    "url": item["url"],
                    "hot_score": item["hot_score"]
                })
                
        except Exception as e:
            logger.error(f"Failed to crawl Xiaohongshu hot content: {e}")
        
        return hot_contents
    
    def crawl_wechat_hot(self) -> List[Dict]:
        """爬取微信热门内容"""
        hot_contents = []
        
        try:
            # 模拟数据
            mock_data = [
                {
                    "title": "科技前沿：AI发展趋势分析",
                    "url": "https://mp.weixin.qq.com/s/article123",
                    "hot_score": 920
                },
                {
                    "title": "生活分享：居家办公效率提升",
                    "url": "https://mp.weixin.qq.com/s/article456",
                    "hot_score": 870
                }
            ]
            
            for item in mock_data:
                hot_contents.append({
                    "platform": PlatformEnum.WECHAT,
                    "title": item["title"],
                    "url": item["url"],
                    "hot_score": item["hot_score"]
                })
                
        except Exception as e:
            logger.error(f"Failed to crawl Wechat hot content: {e}")
        
        return hot_contents
    
    def crawl_bilibili_hot(self) -> List[Dict]:
        """爬取B站热门内容"""
        hot_contents = []
        
        try:
            # 模拟数据
            mock_data = [
                {
                    "title": "游戏资讯：最新游戏发布",
                    "url": "https://www.bilibili.com/video/BV123",
                    "hot_score": 980
                },
                {
                    "title": "学习教程：编程入门指南",
                    "url": "https://www.bilibili.com/video/BV456",
                    "hot_score": 910
                }
            ]
            
            for item in mock_data:
                hot_contents.append({
                    "platform": PlatformEnum.BILIBILI,
                    "title": item["title"],
                    "url": item["url"],
                    "hot_score": item["hot_score"]
                })
                
        except Exception as e:
            logger.error(f"Failed to crawl Bilibili hot content: {e}")
        
        return hot_contents
    
    def crawl_all_platforms(self, db: Session):
        """爬取所有平台的热门内容"""
        all_hot_contents = []
        
        # 爬取各平台热门内容
        platforms_crawlers = {
            PlatformEnum.XIAOHONGSHU: self.crawl_xiaohongshu_hot,
            PlatformEnum.WECHAT: self.crawl_wechat_hot,
            PlatformEnum.BILIBILI: self.crawl_bilibili_hot
        }
        
        for platform, crawler_func in platforms_crawlers.items():
            try:
                logger.info(f"Starting to crawl {platform} hot content...")
                platform_contents = crawler_func()
                all_hot_contents.extend(platform_contents)
                logger.info(f"Successfully crawled {len(platform_contents)} items from {platform}")
                
                # 添加延迟避免请求过于频繁
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to crawl {platform}: {e}")
        
        # 保存到数据库
        self.save_to_database(all_hot_contents, db)
        logger.info(f"Saved {len(all_hot_contents)} hot contents to database")
    
    def save_to_database(self, hot_contents: List[Dict], db: Session):
        """保存热门内容到数据库"""
        try:
            for content_data in hot_contents:
                # 检查是否已存在
                existing = db.query(HotContentModel).filter(
                    HotContentModel.url == content_data["url"]
                ).first()
                
                if existing:
                    # 更新热度分数
                    existing.hot_score = content_data["hot_score"]
                else:
                    # 创建新记录
                    new_content = HotContentModel(**content_data)
                    db.add(new_content)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to save hot contents to database: {e}")
            db.rollback()