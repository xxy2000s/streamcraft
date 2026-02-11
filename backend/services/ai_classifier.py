from openai import OpenAI
from typing import List, Dict, Optional
from config.settings import settings
from loguru import logger
import json

class AIClassifier:
    """AI分类器"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        ) if settings.OPENAI_API_KEY else None
        
        # 预定义的分类标签
        self.categories = [
            "科技数码", "生活日常", "美食分享", "旅行游记", "时尚美妆",
            "学习教育", "娱乐影视", "游戏电竞", "运动健身", "宠物萌宠",
            "家居装修", "摄影艺术", "音乐音频", "读书笔记", "其他"
        ]
        
        self.tags_template = [
            "实用技巧", "经验分享", "产品评测", "教程指南", "心得体会",
            "避坑指南", "种草推荐", "开箱测评", "使用心得", "对比分析"
        ]
    
    def classify_content(self, title: str, content: str = "", platform: str = "") -> Dict:
        """对内容进行AI分类"""
        if not self.client:
            logger.warning("OpenAI API key not configured, using rule-based classification")
            return self._rule_based_classify(title, content, platform)
        
        try:
            prompt = f"""
            请对以下内容进行分类和打标签：
            
            标题：{title}
            内容：{content[:500]}  # 限制内容长度
            平台：{platform}
            
            可选分类：{', '.join(self.categories)}
            
            请从上述分类中选择最合适的1-2个分类，并提供3-5个相关的标签。
            
            回复格式请严格按照以下JSON格式：
            {{
                "categories": ["分类1", "分类2"],
                "tags": ["标签1", "标签2", "标签3"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个内容分类专家，请准确地对内容进行分类和打标签。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 解析JSON响应
            try:
                result = json.loads(result_text)
                return {
                    'categories': result.get('categories', []),
                    'tags': result.get('tags', [])
                }
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI response: {result_text}")
                return self._rule_based_classify(title, content, platform)
                
        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            return self._rule_based_classify(title, content, platform)
    
    def _rule_based_classify(self, title: str, content: str, platform: str) -> Dict:
        """基于规则的分类（备用方案）"""
        text = (title + " " + content).lower()
        
        # 关键词匹配分类
        category_keywords = {
            "科技数码": ["手机", "电脑", "科技", "数码", "app", "软件", "硬件"],
            "生活日常": ["生活", "日常", "分享", "记录", "vlog"],
            "美食分享": ["美食", "吃", "餐厅", "菜谱", "烹饪", "探店"],
            "旅行游记": ["旅行", "旅游", "景点", "攻略", "酒店", "机票"],
            "时尚美妆": ["穿搭", "美妆", "化妆", "护肤", "时尚", "搭配"],
            "学习教育": ["学习", "教育", "课程", "知识", "技能", "培训"],
            "娱乐影视": ["电影", "电视剧", "综艺", "明星", "娱乐", "剧评"],
            "游戏电竞": ["游戏", "电竞", "手游", "主机", "攻略", "评测"],
            "运动健身": ["运动", "健身", "跑步", "瑜伽", "锻炼", "健康"],
            "宠物萌宠": ["宠物", "猫", "狗", "动物", "萌宠", "饲养"],
            "家居装修": ["家居", "装修", "设计", "家具", "收纳", "布置"],
            "摄影艺术": ["摄影", "拍照", "相机", "构图", "后期", "作品"],
            "音乐音频": ["音乐", "歌曲", "音频", "乐器", "演唱会", "专辑"],
            "读书笔记": ["读书", "书籍", "阅读", "书评", "笔记", "推荐"]
        }
        
        matched_categories = []
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                matched_categories.append(category)
        
        # 如果没有匹配到分类，使用默认分类
        if not matched_categories:
            matched_categories = ["其他"]
        
        # 基于规则生成标签
        tags = []
        tag_keywords = {
            "实用技巧": ["教程", "方法", "技巧", "如何", "步骤"],
            "经验分享": ["经验", "分享", "心得", "体会", "总结"],
            "产品评测": ["评测", "测评", "评价", "体验", "试用"],
            "教程指南": ["教程", "指南", "教学", "学习", "入门"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in text for keyword in keywords):
                tags.append(tag)
        
        # 限制标签数量
        tags = tags[:5] if tags else ["其他"]
        
        return {
            'categories': matched_categories[:2],  # 最多返回2个分类
            'tags': tags
        }
    
    def generate_summary(self, title: str, content: str) -> str:
        """生成内容摘要"""
        if not self.client:
            # 简单截取前200字符作为摘要
            return content[:200] + "..." if len(content) > 200 else content
        
        try:
            prompt = f"""
            请为以下内容生成一个简洁的中文摘要（50-100字）：
            
            标题：{title}
            内容：{content[:800]}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的摘要生成器，请生成简洁准确的内容摘要。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return content[:200] + "..." if len(content) > 200 else content

# 全局实例
ai_classifier = AIClassifier()