from django.urls import path

from . import views

# board应用的路由配置
urlpatterns = [
    path('message', views.message, name='message'), # /api/message
	path('clearmessage', views.clearmessage, name='clearmessage'),
	path('messages_for_user', views.messages_for_user, name='messages_for_user'),
    path('avatar', views.avatar, name='avatar'), # AVATAR
]