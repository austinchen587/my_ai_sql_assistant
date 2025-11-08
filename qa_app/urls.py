from django.urls import path
from .views import home_views, ai_views
urlpatterns = [
    # 主页路由 - 直接指向聊天页面
    path('', home_views.chat_view, name='home'),
    path('chat/', home_views.chat_view, name='chat'),
    
    # AI功能路由
    path('ask/', ai_views.ask_question, name='ask_question'),
    
    # 其他路由...
]
