from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.defaults import page_not_found, server_error, permission_denied, bad_request
from . import views


# Definir aqui os handlers de erro
handler400 = 'controllerapp.views.bad_request'
handler403 = 'controllerapp.views.permission_denied'
handler404 = 'controllerapp.views.page_not_found'
handler500 = 'controllerapp.views.server_error'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('projetos/', include('projetos.urls')),  # Atualizado para português
    path('users/', include('users.urls')),
    path('logs/', include('logs.urls')),
    path('painelar/', include('Controle_ar.urls')),
    path('options/', include('options.urls')),
    path('acesso_e_ponto/', include('acesso_e_ponto.urls')),
    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),
    path('inventario/', include('inventario.urls')),
    path('cambam/', include('canva.urls')),  # Adicionar URLs do quadro Kanban
    path('repositorio/', include('repositorio.urls')),  # Adicionar URLs do repositório
    path('gestao/', include('gestao.urls')),  # Adicionar URLs da área de gestão
]

# Adicionar URLs para mídia - mesmo com DEBUG=False para uso local
# IMPORTANTE: Esta abordagem é apenas para uso local/teste e não deve ser usada em produção web
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# Método alternativo para testar páginas de erro
urlpatterns += [
    path('teste-400/', lambda request: bad_request(request, Exception("Teste de erro 400"))),
    path('teste-403/', lambda request: permission_denied(request, Exception("Teste de erro 403"))),
    path('teste-404/', lambda request: page_not_found(request, Exception("Teste de erro 404"))),
    path('teste-500/', lambda request: server_error(request)),
    path('erro-teste/', lambda request: 1/0),  
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)