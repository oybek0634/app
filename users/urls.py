from django.urls import path
from . import views

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('my-posts/', views.my_posts, name='my_posts'),
    path('post/new/', views.post_create, name='post_create'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/<int:pk>/edit/', views.post_update, name='post_update'),
    path('post/<int:pk>/delete/', views.post_delete, name='post_delete'), 
    path('signup/', views.signup, name='signup'),
    path('verify/', views.verify_email, name='verify_email'),
    path('chat/<int:user_id>/', views.chat_view, name='chat_view'),
    path('chat/post/<int:post_id>/', views.chat_view_post, name='chat_view_post'),
    path('notifications/', views.notifications_view, name='notifications_view'),
    path('notifications/<int:pk>/', views.notifications_view, name='notification_detail'),
    path('favorites/', views.favorite_list, name='favorite_list'),
    path('favorite/<int:post_id>/', views.favorite_post, name='favorite_post'),
]
