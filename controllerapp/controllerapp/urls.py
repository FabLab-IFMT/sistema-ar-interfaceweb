# controllerapp/urls.py (VERSÃO FINAL E CORRIGIDA)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

# Handlers de erro
handler400 = 'controllerapp.views.bad_request'
handler403 = 'controllerapp.views.permission_denied'
handler404 = 'controllerapp.views.page_not_found'
handler500 = 'controllerapp.views.server_error'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('projetos/', include('projetos.urls')),
    path('users/', include('users.urls')),
    path('logs/', include('logs.urls')),
    path('painelar/', include('Controle_ar.urls')),
    path('options/', include('options.urls')),
    path('acesso_e_ponto/', include('acesso_e_ponto.urls')),
    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),
    path('inventario/', include('inventario.urls')),
    path('cambam/', include('canva.urls')),
    path('repositorio/', include('repositorio.urls')),
    path('gestao/', include('gestao.urls')),
]

# Serve arquivos de mídia localmente e opcionalmente em produção se SERVE_MEDIA=True
if settings.DEBUG or getattr(settings, 'SERVE_MEDIA', False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)