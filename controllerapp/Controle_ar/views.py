import requests
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from logs.models import Action
from logs.scripts import create_log

# Substitua pelo IP do seu ESP32 (ex.: '192.168.1.100')
ESP32_IP = '192.168.1.113'

def admin_check(user):
    return user.is_staff

@user_passes_test(admin_check)
def index(request):
    return render(request, 'control/Painel_ar_condicionado.html')

@user_passes_test(admin_check)
def ligar(request):
    try:
        response = requests.get(f'http://{ESP32_IP}/ligar')

        create_log("turn_on", author="ESP32")
        return HttpResponse(f'Comando "Ligar" enviado. Resposta do ESP32: {response.text}')
    except Exception as e:
        create_log("init_error", author="ESP32")
        return HttpResponse(f'Erro ao enviar comando "Ligar": {str(e)}')
        

@user_passes_test(admin_check)
def desligar(request):
    try:
        response = requests.get(f'http://{ESP32_IP}/desligar')
        create_log("shutdown", author="ESP32")
        return HttpResponse(f'Comando "Desligar" enviado. Resposta do ESP32: {response.text}')
    except Exception as e:
        create_log("shutdown_error", author="ESP32")
        return HttpResponse(f'Erro ao enviar comando "Desligar": {str(e)}')

@user_passes_test(admin_check)
def aumentar(request):
    try:
        response = requests.get(f'http://{ESP32_IP}/aumentar')
        return HttpResponse(f'Comando "Aumentar" enviado. Resposta do ESP32: {response.text}')
    except Exception as e:
        return HttpResponse(f'Erro ao enviar comando "Aumentar": {str(e)}')

@user_passes_test(admin_check)
def diminuir(request):
    try:
        response = requests.get(f'http://{ESP32_IP}/diminuir')
        return HttpResponse(f'Comando "Diminuir" enviado. Resposta do ESP32: {response.text}')
    except Exception as e:
        return HttpResponse(f'Erro ao enviar comando "Diminuir": {str(e)}')

@user_passes_test(admin_check)
def definir_temperatura(request):
    if request.method == 'POST':
        temp = request.POST.get('temp')
        if not temp:
            return HttpResponse('Temperatura não informada.')
        try:
            # Envia o comando com o parâmetro 'temp'
            response = requests.get(f'http://{ESP32_IP}/definir_temperatura', params={'temp': temp})
            create_log("temp_config_changed", author="ESP32", param1= "", param2= temp)
            return HttpResponse(f'Comando "Definir Temperatura" enviado. Resposta do ESP32: {response.text}')
        except Exception as e:
            create_log("command_error", author="ESP32", param1= "Definir temperatura")
            return HttpResponse(f'Erro ao enviar comando "Definir Temperatura": {str(e)}')
        
    return render(request, 'control/definir_temperatura.html')
