import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict, List, Optional
from config.settings import settings
import json
import time
from loguru import logger

class BaseScraper:
    """基础爬虫类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        """设置会话"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def get_page_content(self, url: str) -> str:
        """获取页面内容"""
        try:
            response = self.session.get(url, timeout=settings.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return ""

class XiaohongshuScraper(BaseScraper):
    """小红书爬虫"""
    
    def __init__(self):
        super().__init__()
        if settings.XIAOHONGSHU_COOKIE:
            self.session.cookies.update({'cookie': settings.XIAOHONGSHU_COOKIE})
    
    def scrape_post(self, post_id: str) -> Dict:
        """爬取小红书帖子"""
        url = f"https://www.xiaohongshu.com/discovery/item/{post_id}"
        content = self.get_page_content(url)
        
        if not content:
            return {}
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # 提取标题
        title_elem = soup.find('title')
        title = title_elem.text if title_elem else ""
        
        # 提取图片
        img_elems = soup.find_all('img')
        images = [img.get('src') for img in img_elems if img.get('src')]
        
        # 提取作者信息
        author_elem = soup.find('span', class_='username')
        author = author_elem.text if author_elem else ""
        
        return {
            'platform': 'xiaohongshu',
            'content_id': post_id,
            'title': title,
            'author': author,
            'images': images[:5],  # 限制图片数量
            'url': url
        }

class WechatScraper(BaseScraper):
    """微信公众号爬虫"""
    
    def scrape_article(self, article_url: str) -> Dict:
        """爬取微信文章"""
        content = self.get_page_content(article_url)
        
        if not content:
            return {}
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # 提取标题
        title_elem = soup.find('h1', class_='rich_media_title')
        title = title_elem.text.strip() if title_elem else ""
        
        # 提取作者
        author_elem = soup.find('span', class_='rich_media_meta_text')
        author = author_elem.text.strip() if author_elem else ""
        
        # 提取正文内容
        content_elem = soup.find('div', class_='rich_media_content')
        content_text = content_elem.get_text().strip() if content_elem else ""
        
        return {
            'platform': 'wechat',
            'content_id': self.extract_wechat_id(article_url),
            'title': title,
            'author': author,
            'content': content_text[:1000],  # 限制内容长度
            'url': article_url
        }
    
    def extract_wechat_id(self, url: str) -> str:
        """提取微信文章ID"""
        # 实现微信文章ID提取逻辑
        return url.split('/')[-1] if url else ""

class BilibiliScraper(BaseScraper):
    """B站爬虫"""
    
    def __init__(self):
        super().__init__()
        if settings.BILIBILI_COOKIE:
            self.session.cookies.update({'cookie': settings.BILIBILI_COOKIE})
    
    def scrape_video(self, video_id: str) -> Dict:
        """爬取B站视频"""
        url = f"https://www.bilibili.com/video/{video_id}"
        content = self.get_page_content(url)
        
        if not content:
            return {}
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # 提取标题
        title_elem = soup.find('h1', class_='video-title')
        title = title_elem.text.strip() if title_elem else ""
        
        # 提取作者
        author_elem = soup.find('a', class_='username')
        author = author_elem.text.strip() if author_elem else ""
        
        # 提取封面图
        cover_elem = soup.find('img', class_='cover-img')
        cover_url = cover_elem.get('src') if cover_elem else ""
        
        return {
            'platform': 'bilibili',
            'content_id': video_id,
            'title': title,
            'author': author,
            'cover_image': cover_url,
            'url': url
        }

class ScraperFactory:
    """爬虫工厂类"""
    
    @staticmethod
    def get_scraper(platform: str):
        """根据平台获取对应的爬虫"""
        scrapers = {
            'xiaohongshu': XiaohongshuScraper,
            'wechat': WechatScraper,
            'bilibili': BilibiliScraper
        }
        
        scraper_class = scrapers.get(platform.lower())
        if not scraper_class:
            raise ValueError(f"Unsupported platform: {platform}")
        
        return scraper_class()
    
    @staticmethod
    def scrape_content(platform: str, content_id: str) -> Dict:
        """爬取内容的统一接口"""
        try:
            scraper = ScraperFactory.get_scraper(platform)
            
            if platform.lower() == 'xiaohongshu':
                return scraper.scrape_post(content_id)
            elif platform.lower() == 'wechat':
                return scraper.scrape_article(content_id)
            elif platform.lower() == 'bilibili':
                return scraper.scrape_video(content_id)
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Scraping failed for {platform}/{content_id}: {e}")
            return {}