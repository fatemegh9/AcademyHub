from django.contrib import admin
from .models import Post, Like, Comment, Story

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'content', 'image', 'created_at']
    search_fields = ['author__username', 'content']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post']

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'image', 'text', 'created_at', 'expires_at']
    list_filter = ['user', 'created_at']
    search_fields = ['user__username', 'text']
