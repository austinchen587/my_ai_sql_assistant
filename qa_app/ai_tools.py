import os
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
import psycopg2
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def get_sql_agent():
    """初始化并返回SQL Agent（使用硅基流动）"""
    try:
        # 数据库连接配置
        db_config = {
            'host': settings.DATABASES['default']['HOST'],
            'port': settings.DATABASES['default']['PORT'],
            'database': settings.DATABASES['default']['NAME'],
            'user': settings.DATABASES['default']['USER'],
            'password': settings.DATABASES['default']['PASSWORD'],
        }
        
        # 构建数据库连接URL
        db_url = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        
        # 连接数据库
        db = SQLDatabase.from_uri(db_url)
        
        # 检查硅基流动配置
        if not settings.SILICONFLOW_API_KEY:
            raise ValueError("硅基流动 API 密钥未配置")
        if not settings.SILICONFLOW_BASE_URL:
            raise ValueError("硅基流动 API 地址未配置")
        
        # 初始化LLM - 使用硅基流动的DeepSeek模型
        llm = ChatOpenAI(
            model="deepseek-ai/DeepSeek-V3.1-Terminus",  # 硅基流动上的模型名称
            temperature=0,
            openai_api_key=settings.SILICONFLOW_API_KEY,  # 使用硅基流动的API密钥
            openai_api_base=settings.SILICONFLOW_BASE_URL,  # 硅基流动的API地址
        )
        
        # 创建SQL Agent
        agent = create_sql_agent(
            llm=llm,
            db=db,
            agent_type="openai-tools",
            verbose=True
        )
        
        logger.info("SQL Agent初始化成功（使用硅基流动）")
        return agent
        
    except Exception as e:
        logger.error(f"初始化SQL Agent失败: {str(e)}")
        raise

# 预初始化Agent（可选，用于提高响应速度）
_sql_agent = None

def get_cached_sql_agent():
    """获取缓存的SQL Agent"""
    global _sql_agent
    if _sql_agent is None:
        _sql_agent = get_sql_agent()
    return _sql_agent
