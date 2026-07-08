from django.urls import path
from . import views

urlpatterns = [
    path('', views.note_list, name='note_list'),
    path('upload/', views.upload_note, name='upload_note'),
    path('download/<int:note_id>/', views.download_note, name='download_note'),
    #path('search/', views.search_notes, name='search_notes'),
    path('edit/<int:note_id>/',views.edit_note, name='edit_note'),
    path('delete_note/<int:note_id>/', views.delete_note, name='delete_note'),
    path('rate/<int:note_id>/<int:score>/', views.rate_note, name='rate_note'),
    path('tag/<str:slug>/', views.search_by_tag, name='search_by_tag'),
    path('save/<int:note_id>/', views.save_note, name='save_note'),
    path('unsave/<int:note_id>/', views.unsave_note, name='unsave_note'),
    path('saved/', views.saved_notes_list, name='saved_notes'),
    path('saved/', views.saved_items, name='saved_items'),
    path('get-note/<int:note_id>/', views.get_note_json, name='get_note_json'),
    path('summarize/<int:note_id>/', views.summarize_note_view, name='summarize_note'),
    path('ask/<int:note_id>/', views.ask_note_view, name='ask_note'),
    path('quiz/<int:note_id>/', views.generate_quiz_view, name='generate_quiz'),
]