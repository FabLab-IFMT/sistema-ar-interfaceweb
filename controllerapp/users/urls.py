from django.urls import path
from . import views

app_name = 'users'  # Define o namespace usado em {% url 'users:logout' %}

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),  # Adiciona o caminho para logout
    path('user-list/', views.user_list, name='user_list'),
]
