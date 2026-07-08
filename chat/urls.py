from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('start/<str:username>/', views.start_conversation, name='start_conversation'),
    path('<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('group/create/', views.create_group, name='create_group'),
    path('group/<int:pk>/delete/', views.delete_group, name='delete_group'),
    path('users/search/', views.search_users, name='search_users'),
    path('conversation/<int:conversation_id>/clear/', views.clear_chat, name='clear_chat'),
    path("conversation/<int:pk>/delete/",views.delete_conversation,name="delete_conversation"),
    path('conversation/<int:conversation_id>/add-members/', views.add_group_members, name='add_group_members'),
    path('conversation/<int:conversation_id>/remove-member/<int:user_id>/', views.remove_group_member, name='remove_group_member'),
]