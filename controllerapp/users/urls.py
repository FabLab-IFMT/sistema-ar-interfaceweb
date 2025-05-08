from django.urls import path
from . import views

app_name = 'users'  # Define o namespace usado em {% url 'users:logout' %}

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),  # Adiciona o caminho para logout
    path('user-list/', views.user_list, name='user_list'),
    path('pending-registrations/', views.pending_registrations, name='pending_registrations'),
    path('approve-registration/<int:request_id>/', views.approve_registration, name='approve_registration'),
    path('reject-registration/<int:request_id>/', views.reject_registration, name='reject_registration'),
    
    # Páginas de perfil de usuário
    path('profile/', views.profile, name='profile'),  # Perfil do usuário logado
    path('profile/<str:user_id>/', views.profile, name='user_profile'),  # Perfil de outro usuário
    path('change-password/', views.change_password, name='change_password'),  # Alteração de senha
]
