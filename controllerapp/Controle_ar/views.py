import requests
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from logs.models import Action
from logs.scripts import create_log

ESP32_IP = '192.168.1.113'

def index(request):
    return render(request, 'control/Painel_ar_condicionado.html')

def ligar(request):
    try:
        url = f'http://{ESP32_IP}/ligar'
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Lança erro se a resposta não for 200
        create_log("turn_on", author="ESP32")
        messages.success(request, "Comando 'Ligar' enviado com sucesso!")
    except requests.exceptions.ConnectionError:
        create_log("init_error", author="ESP32")
        messages.error(request, "Erro: Falha de conexão com o dispositivo.")
    except requests.exceptions.Timeout:
        create_log("init_error", author="ESP32")
        messages.error(request, "Erro: O tempo de resposta expirou. O dispositivo pode estar offline.")
    except requests.exceptions.RequestException as e:
        create_log("init_error", author="ESP32")
        messages.error(request, f"Erro ao enviar comando 'Ligar': {e}")
    return redirect('Controle_ar:home')

def desligar(request):
    try:
        url = f'http://{ESP32_IP}/desligar'
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        create_log("shutdown", author="ESP32")
        messages.success(request, "Comando 'Desligar' enviado com sucesso!")
    except requests.exceptions.ConnectionError:
        create_log("shutdown_error", author="ESP32")
        messages.error(request, "Erro: Falha de conexão com o dispositivo.")
    except requests.exceptions.Timeout:
        create_log("shutdown_error", author="ESP32")
        messages.error(request, "Erro: O tempo de resposta expirou. O dispositivo pode estar offline.")
    except requests.exceptions.RequestException as e:
        create_log("shutdown_error", author="ESP32")
        messages.error(request, f"Erro ao enviar comando 'Desligar': {e}")
    return redirect('Controle_ar:home')

def aumentar(request):
    try:
        url = f'http://{ESP32_IP}/aumentar'
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        messages.success(request, "Comando 'Aumentar' enviado com sucesso!")
    except requests.exceptions.ConnectionError:
        messages.error(request, "Erro: Falha de conexão com o dispositivo.")
    except requests.exceptions.Timeout:
        messages.error(request, "Erro: O tempo de resposta expirou. O dispositivo pode estar offline.")
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Erro ao enviar comando 'Aumentar': {e}")
    return redirect('Controle_ar:home')

def diminuir(request):
    try:
        url = f'http://{ESP32_IP}/diminuir'
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        messages.success(request, "Comando 'Diminuir' enviado com sucesso!")
    except requests.exceptions.ConnectionError:
        messages.error(request, "Erro: Falha de conexão com o dispositivo.")
    except requests.exceptions.Timeout:
        messages.error(request, "Erro: O tempo de resposta expirou. O dispositivo pode estar offline.")
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Erro ao enviar comando 'Diminuir': {e}")
    return redirect('Controle_ar:home')

def definir_temperatura(request):
    if request.method == 'POST':
        temp = request.POST.get('temp')
        if not temp:
            messages.error(request, "Temperatura não informada.")
            return redirect('Controle_ar:home')
        try:
            url = f'http://{ESP32_IP}/definir_temperatura'
            response = requests.get(url, params={'temp': temp}, timeout=5)
            response.raise_for_status()
            create_log("temp_config_changed", author="ESP32", param1="", param2=temp)
            messages.success(request, "Comando 'Definir Temperatura' enviado com sucesso!")
        except requests.exceptions.ConnectionError:
            create_log("command_error", author="ESP32", param1="Definir temperatura")
            messages.error(request, "Erro: Falha de conexão com o dispositivo.")
        except requests.exceptions.Timeout:
            create_log("command_error", author="ESP32", param1="Definir temperatura")
            messages.error(request, "Erro: O tempo de resposta expirou. O dispositivo pode estar offline.")
        except requests.exceptions.RequestException as e:
            create_log("command_error", author="ESP32", param1="Definir temperatura")
            messages.error(request, f"Erro ao enviar comando 'Definir Temperatura': {e}")
        return redirect('Controle_ar:home')
    return render(request, 'control/definir_temperatura.html')
