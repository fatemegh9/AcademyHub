from django.urls import path
from . import views

urlpatterns = [
    path('', views.question_list, name='question_list'),
    path('ask/', views.ask_question, name='ask_question'),
    path('<int:question_id>/', views.question_detail, name='question_detail'),
    path('<int:question_id>/answer/', views.add_answer, name='add_answer'),
    path('answer/<int:answer_id>/accept/', views.accept_answer, name='accept_answer'),
    path('<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('answer/<int:answer_id>/vote/', views.vote_answer, name='vote_answer'),
]