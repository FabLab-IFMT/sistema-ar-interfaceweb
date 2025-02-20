from django.urls import path
from .views import check_card

urlpatterns = [
    path('verificar_cartao/', check_card, name='verificar_cartao'),
]
