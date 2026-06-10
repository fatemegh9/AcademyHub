from django.urls import path
from . import views


urlpatterns = [
    path('', views.timeline, name='timeline'),
    path('create/', views.create_post, name='create_post'),
    path('like/<int:post_id>/', views.like_post, name='like_post'),
    path('comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('edit_post/<int:post_id>/', views.edit_post, name='edit_post'),
    path('delete_post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('like_comment/<int:comment_id>/', views.like_comment, name='like_comment'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('story/create/', views.create_story, name='create_story'),
    path('story/list/', views.story_list_api, name='story_list_api'),
    path('story/delete/<int:story_id>/', views.delete_story, name='delete_story'),
    path('my-stories/', views.my_stories_api, name='my_stories_api'),
    path('edit/<int:post_id>/', views.edit_post, name='edit_post'),
    path('save_post/<int:post_id>/', views.save_post, name='save_post'),
    path('unsave_post/<int:post_id>/', views.unsave_post, name='unsave_post'),
    path('get-post/<int:post_id>/', views.get_post_json, name='get_post_json'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment')
]