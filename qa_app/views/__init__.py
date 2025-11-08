# 导入所有视图模块，方便统一导入
from .home_views import home
from .ai_views import ask_question

__all__ = ['home', 'ask_question']
