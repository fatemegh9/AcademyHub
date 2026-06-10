from django.contrib import admin
from .models import Note, Tag


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson_name', 'uploaded_by', 'created_at', 'downloads_count']
    search_fields = ['title', 'lesson_name', 'professor_name']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    