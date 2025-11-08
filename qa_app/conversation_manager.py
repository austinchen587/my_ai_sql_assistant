import json
import os
import logging
from datetime import datetime, timedelta
from django.conf import settings
import uuid

logger = logging.getLogger(__name__)

class ConversationManager:
    """对话管理器，负责保存和检索对话历史"""
    
    def __init__(self, storage_dir=None):
        self.storage_dir = storage_dir or os.path.join(settings.BASE_DIR, 'conversations')
        self.ensure_storage_dir()
        self.current_session_id = self.generate_session_id()
        
    def ensure_storage_dir(self):
        """确保存储目录存在"""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
            logger.info(f"创建对话存储目录: {self.storage_dir}")
    
    def generate_session_id(self):
        """生成唯一的会话ID"""
        return str(uuid.uuid4())
    
    def save_conversation(self, question, raw_answer, formatted_answer, response_time):
        """保存单次对话到JSON文件"""
        try:
            conversation = {
                "session_id": self.current_session_id,
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "raw_answer": raw_answer,
                "formatted_answer": formatted_answer,
                "response_time": response_time
            }
            
            # 按日期组织文件
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"conversations_{date_str}.json"
            filepath = os.path.join(self.storage_dir, filename)
            
            # 读取现有数据或创建新文件
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = {"conversations": []}
            else:
                data = {"conversations": []}
            
            # 添加新对话
            data["conversations"].append(conversation)
            
            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"对话已保存到: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"保存对话失败: {str(e)}")
            return False
    
    def get_conversation_history(self, days=7):
        """获取最近N天的对话历史"""
        try:
            history = []
            for i in range(days):
                date = datetime.now().date() - timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")
                filename = f"conversations_{date_str}.json"
                filepath = os.path.join(self.storage_dir, filename)
                
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        history.extend(data.get("conversations", []))
            
            # 按时间戳排序（最新的在前）
            history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return history
            
        except Exception as e:
            logger.error(f"获取对话历史失败: {str(e)}")
            return []
    
    def search_conversations(self, keyword, limit=10):
        """根据关键词搜索对话历史"""
        try:
            history = self.get_conversation_history(days=30)  # 搜索最近30天
            results = []
            
            for conversation in history:
                question = conversation.get("question", "").lower()
                answer = conversation.get("raw_answer", "").lower()
                keyword_lower = keyword.lower()
                
                if keyword_lower in question or keyword_lower in answer:
                    results.append(conversation)
                    if len(results) >= limit:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"搜索对话失败: {str(e)}")
            return []

# 全局对话管理器实例
conversation_manager = ConversationManager()
