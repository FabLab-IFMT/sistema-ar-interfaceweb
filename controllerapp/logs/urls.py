from django.urls import path
from . import views

app_name = 'logs'

urlpatterns = [
    path('', views.logs_list, name='list'),
    path('<int:day>/<int:month>/<int:year>', views.logs_datepage, name='datepage'),
]