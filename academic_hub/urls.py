from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import profile_view
from social.views import timeline

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', timeline, name='home'),              
    path('profile/', profile_view, name='my_profile'), 
    path('accounts/', include('accounts.urls')),
    path('notes/', include('notes.urls')),
    path('social/', include('social.urls')),
    path('password-reset/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)