from django.urls import path
from . import views
from .views import create_superuser
from social.views import timeline

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
    path('profile/', views.profile_view, name='my_profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('follow/<str:username>/', views.follow_user, name='follow_user'),
    path('unfollow/<str:username>/', views.unfollow_user, name='unfollow_user'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path("create-superuser/", create_superuser),
]