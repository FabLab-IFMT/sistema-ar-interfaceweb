from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

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
    
    # Recuperação de senha
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'), 
        name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html'), 
        name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'), 
        name='password_reset_complete'),
]
