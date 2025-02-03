import requests
from django.shortcuts import render
from django.http import HttpResponse

# Substitua pelo IP do seu ESP32 (ex.: '192.168.1.100')
ESP32_IP = '192.168.1.113'

def index(request):
    return render(request, 'control/Painel_ar_condicionado.html')

def ligar(request):
    try:
        response = requests.get(f'http://{ESP32_IP}/ligar')
        return HttpResponse(f'Comando "Ligar" enviado. Resposta do ESP32: {response.text}')
    except Exception as e:
        return HttpResponse(f'Erro ao enviar comando "Ligar": {str(e)}')

def desligar(request):
    try:
        response = requests.get(f'http://{ESP32_IP}/desligar')
        return HttpResponse(f'Comando "Desligar" enviado. Resposta do ESP32: {response.text}')
    except Exception as e:
        return HttpResponse(f'Erro ao enviar comando "Desligar": {str(e)}')

def aumentar(request):
    try:
        response = requests.get(f'http://{ESP32_IP}/aumentar')
        return HttpResponse(f'Comando "Aumentar" enviado. Resposta do ESP32: {response.text}')
    except Exception as e:
        return HttpResponse(f'Erro ao enviar comando "Aumentar": {str(e)}')

def diminuir(request):
    try:
        response = requests.get(f'http://{ESP32_IP}/diminuir')
        return HttpResponse(f'Comando "Diminuir" enviado. Resposta do ESP32: {response.text}')
    except Exception as e:
        return HttpResponse(f'Erro ao enviar comando "Diminuir": {str(e)}')

def definir_temperatura(request):
    if request.method == 'POST':
        temp = request.POST.get('temp')
        if not temp:
            return HttpResponse('Temperatura não informada.')
        try:
            # Envia o comando com o parâmetro 'temp'
            response = requests.get(f'http://{ESP32_IP}/definir_temperatura', params={'temp': temp})
            return HttpResponse(f'Comando "Definir Temperatura" enviado. Resposta do ESP32: {response.text}')
        except Exception as e:
            return HttpResponse(f'Erro ao enviar comando "Definir Temperatura": {str(e)}')
    return render(request, 'control/definir_temperatura.html')
