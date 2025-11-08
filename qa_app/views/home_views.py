from django.shortcuts import render
def home(request):
    """主页视图 - 重定向到聊天页面"""
    return render(request, 'qa_app/chat.html')
def chat_view(request):
    """渲染主聊天页面"""
    return render(request, 'qa_app/chat.html')