from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('projects/', views.projects, name='projects'),
    path('users/', include('users.urls')),
    path('logs/', include('logs.urls')),
    path('painelar/', include('Controle_ar.urls')),
    path('options/', include('options.urls')),
    path('acesso_e_ponto/', include('acesso_e_ponto.urls')),
]

# Adicionar URLs para mídia durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)