import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.utils import timezone
import json
import datetime
from logs.models import Action
from logs.scripts import create_log
from .models import Ar_condicionado, Comando_ar, LogOperacao

ESP32_IP = '192.168.1.113'

# Função auxiliar para verificar se o usuário é administrador
def is_admin(user):
    return user.is_authenticated and user.is_staff

# Função auxiliar para redirecionar usuários não administradores
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not is_admin(request.user):
            messages.error(request, "Acesso negado. Apenas administradores podem acessar esta funcionalidade.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@admin_required
def automacao_home(request):
    """Página inicial de automação com seleção de subsistemas"""
    ar_count = Ar_condicionado.objects.count()
    return render(request, 'Controle_ar/automacao_home.html', {'ar_count': ar_count})

@login_required
@admin_required
def ar_dashboard(request):
    """Exibe todos os ar-condicionados disponíveis para controle"""
    ares = Ar_condicionado.objects.all()
    return render(request, 'Controle_ar/dashboard.html', {'ares': ares})

# Renomear o método original dashboard para ar_dashboard e manter um redirecionamento por compatibilidade
@login_required
@admin_required
def dashboard(request):
    """Redirecionamento para compatibilidade"""
    return ar_dashboard(request)

@login_required
@admin_required
def controlar_ar(request, ar_id):
    """Exibe a interface de controle para um ar-condicionado específico"""
    ar = get_object_or_404(Ar_condicionado, id=ar_id)
    return render(request, 'Controle_ar/controlar_ar.html', {'ar': ar})

@login_required
@admin_required
def ligar_ar(request, ar_id):
    """Liga o ar-condicionado"""
    ar = get_object_or_404(Ar_condicionado, id=ar_id)
    ar.estado = True
    ar.save()
    
    # Registrar comando para o ESP
    Comando_ar.objects.create(
        ar_condicionado=ar,
        comando=f"ligar:{ar.temperatura}:{ar.modo}:{ar.velocidade}:{1 if ar.swing else 0}"
    )
    
    # Registrar no log
    LogOperacao.objects.create(
        ar_condicionado=ar,
        operacao=f"Ligado - Temperatura: {ar.temperatura}°C, Modo: {ar.modo_display}, Velocidade: {ar.velocidade_display}",
        usuario=f"{request.user.first_name} {request.user.last_name}"
    )
    
    # Registrar no log geral
    Action.objects.create(
        author=f"{request.user.first_name} {request.user.last_name}",
        type="Ar Condicionado",
        description=f"Ligou o ar-condicionado {ar.nome}",
        date=datetime.date.today(),
        time=datetime.datetime.now().time()
    )
    
    return redirect('Controle_ar:controlar_ar', ar_id=ar.id)

@login_required
@admin_required
def desligar_ar(request, ar_id):
    """Desliga o ar-condicionado"""
    ar = get_object_or_404(Ar_condicionado, id=ar_id)
    ar.estado = False
    ar.save()
    
    # Registrar comando para o ESP
    Comando_ar.objects.create(
        ar_condicionado=ar,
        comando="desligar"
    )
    
    # Registrar no log
    LogOperacao.objects.create(
        ar_condicionado=ar,
        operacao="Desligado",
        usuario=f"{request.user.first_name} {request.user.last_name}"
    )
    
    # Registrar no log geral
    Action.objects.create(
        author=f"{request.user.first_name} {request.user.last_name}",
        type="Ar Condicionado",
        description=f"Desligou o ar-condicionado {ar.nome}",
        date=datetime.date.today(),
        time=datetime.datetime.now().time()
    )
    
    return redirect('Controle_ar:controlar_ar', ar_id=ar.id)

@login_required
@admin_required
def ajustar_temperatura(request, ar_id):
    """Ajusta a temperatura do ar-condicionado"""
    if request.method == "POST":
        ar = get_object_or_404(Ar_condicionado, id=ar_id)
        nova_temperatura = int(request.POST.get('temperatura', ar.temperatura))
        
        # Limitar a temperatura entre 16 e 30 graus
        if 16 <= nova_temperatura <= 30:
            ar.temperatura = nova_temperatura
            ar.save()
            
            # Se o ar estiver ligado, enviar comando de ajuste
            if ar.estado:
                Comando_ar.objects.create(
                    ar_condicionado=ar,
                    comando=f"temperatura:{nova_temperatura}"
                )
            
            # Registrar no log
            LogOperacao.objects.create(
                ar_condicionado=ar,
                operacao=f"Temperatura ajustada para {nova_temperatura}°C",
                usuario=f"{request.user.first_name} {request.user.last_name}"
            )
            
            # Registrar no log geral
            Action.objects.create(
                author=f"{request.user.first_name} {request.user.last_name}",
                type="Ar Condicionado",
                description=f"Ajustou a temperatura do ar-condicionado {ar.nome} para {nova_temperatura}°C",
                date=datetime.date.today(),
                time=datetime.datetime.now().time()
            )
    
    return redirect('Controle_ar:controlar_ar', ar_id=ar_id)

@login_required
@admin_required
def ajustar_modo(request, ar_id):
    """Ajusta o modo de operação do ar-condicionado"""
    if request.method == "POST":
        ar = get_object_or_404(Ar_condicionado, id=ar_id)
        novo_modo = request.POST.get('modo', ar.modo)
        
        modos_validos = ["cold", "heat", "fan", "dry", "auto"]
        if novo_modo in modos_validos:
            ar.modo = novo_modo
            ar.save()
            
            # Se o ar estiver ligado, enviar comando de ajuste
            if ar.estado:
                Comando_ar.objects.create(
                    ar_condicionado=ar,
                    comando=f"modo:{novo_modo}"
                )
            
            # Registrar no log
            LogOperacao.objects.create(
                ar_condicionado=ar,
                operacao=f"Modo alterado para {ar.modo_display}",
                usuario=f"{request.user.first_name} {request.user.last_name}"
            )
            
            # Registrar no log geral
            Action.objects.create(
                author=f"{request.user.first_name} {request.user.last_name}",
                type="Ar Condicionado",
                description=f"Alterou o modo do ar-condicionado {ar.nome} para {ar.modo_display}",
                date=datetime.date.today(),
                time=datetime.datetime.now().time()
            )
    
    return redirect('Controle_ar:controlar_ar', ar_id=ar_id)

@login_required
@admin_required
def ajustar_velocidade(request, ar_id):
    """Ajusta a velocidade do ventilador do ar-condicionado"""
    if request.method == "POST":
        ar = get_object_or_404(Ar_condicionado, id=ar_id)
        nova_velocidade = int(request.POST.get('velocidade', ar.velocidade))
        
        if 1 <= nova_velocidade <= 4:  # Incluindo velocidade 4 (automática)
            ar.velocidade = nova_velocidade
            ar.save()
            
            # Se o ar estiver ligado, enviar comando de ajuste
            if ar.estado:
                Comando_ar.objects.create(
                    ar_condicionado=ar,
                    comando=f"velocidade:{nova_velocidade}"
                )
            
            # Registrar no log
            LogOperacao.objects.create(
                ar_condicionado=ar,
                operacao=f"Velocidade alterada para {ar.velocidade_display}",
                usuario=f"{request.user.first_name} {request.user.last_name}"
            )
            
            # Registrar no log geral
            Action.objects.create(
                author=f"{request.user.first_name} {request.user.last_name}",
                type="Ar Condicionado",
                description=f"Alterou a velocidade do ar-condicionado {ar.nome} para {ar.velocidade_display}",
                date=datetime.date.today(),
                time=datetime.datetime.now().time()
            )
    
    return redirect('Controle_ar:controlar_ar', ar_id=ar_id)

@login_required
@admin_required
def toggle_swing(request, ar_id):
    """Alterna o modo swing do ar-condicionado"""
    ar = get_object_or_404(Ar_condicionado, id=ar_id)
    ar.swing = not ar.swing
    ar.save()
    
    # Se o ar estiver ligado, enviar comando de ajuste
    if ar.estado:
        Comando_ar.objects.create(
            ar_condicionado=ar,
            comando=f"swing:{1 if ar.swing else 0}"
        )
    
    # Registrar no log
    status_swing = "ativado" if ar.swing else "desativado"
    LogOperacao.objects.create(
        ar_condicionado=ar,
        operacao=f"Swing {status_swing}",
        usuario=f"{request.user.first_name} {request.user.last_name}"
    )
    
    # Registrar no log geral
    Action.objects.create(
        author=f"{request.user.first_name} {request.user.last_name}",
        type="Ar Condicionado",
        description=f"{status_swing.capitalize()} o swing do ar-condicionado {ar.nome}",
        date=datetime.date.today(),
        time=datetime.datetime.now().time()
    )
    
    return redirect('Controle_ar:controlar_ar', ar_id=ar_id)

@csrf_exempt
def api_status(request):
    """API para o ESP8266 informar status e receber comandos"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            tag = data.get('tag')
            
            ar = get_object_or_404(Ar_condicionado, tag=tag)
            
            # Atualizar status baseado no relatório do ESP
            ar.online = True
            ar.ultimo_ping = timezone.now()
            
            if 'temperatura_ambiente' in data:
                ar.temperatura_ambiente = data.get('temperatura_ambiente')
            
            if 'consumo' in data:
                ar.consumo_atual = data.get('consumo')
                
            ar.save()
            
            # Verificar se há comandos pendentes
            comandos = Comando_ar.objects.filter(ar_condicionado=ar, executado=False).order_by('data_hora')
            
            if comandos.exists():
                comando = comandos.first()
                comando.executado = True
                comando.save()
                
                return JsonResponse({
                    'status': 'success',
                    'comando': comando.comando
                })
            
            return JsonResponse({
                'status': 'success',
                'comando': 'none'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Método não permitido'
    }, status=405)
