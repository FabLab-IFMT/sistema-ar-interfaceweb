from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from users.models import Card  # Corrigido: importar do app users

@csrf_exempt  # Desativa proteção CSRF para permitir requisições do ESP32
def check_card(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Lendo JSON enviado pelo ESP32
            card_number = data.get("card_number")

            if not card_number:
                return JsonResponse({"message": "Número do cartão não enviado"}, status=400)

            # Verifica se o cartão existe no banco de dados
            if Card.objects.filter(card_number=card_number).exists():
                return JsonResponse({"authorized": True, "message": "Acesso permitido"})
            else:
                return JsonResponse({"authorized": False, "message": "Acesso negado"})

        except json.JSONDecodeError:
            return JsonResponse({"message": "Erro ao processar JSON"}, status=400)
    
    return JsonResponse({"message": "Método não permitido"}, status=405)
