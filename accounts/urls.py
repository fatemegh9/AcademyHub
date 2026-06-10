from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
    path('profile/', views.profile_view, name='my_profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('follow/<str:username>/', views.follow_user, name='follow_user'),
path('unfollow/<str:username>/', views.unfollow_user, name='unfollow_user'),
]