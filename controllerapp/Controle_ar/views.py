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

# Mapeamento de tags para IPs dos ESP32
ESP32_IPS = {
    'ar-sala-reunioes': '192.168.1.113',  # ESP32 original
    'ar-sala-aula-1': '192.168.1.114',    # Novo ESP32
    # Adicione mais dispositivos conforme necessário
}

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

# Função para enviar comandos ao ESP32
def enviar_comando_esp32(comando, params=None, tag=None, ar_id=None):
    """
    Envia comandos HTTP ao ESP32.
    Parâmetros:
        comando: string com o comando (ligar, desligar, etc)
        params: dicionário com parâmetros adicionais
        tag: tag do ar-condicionado (opcional se ar_id for fornecido)
        ar_id: id do ar-condicionado (opcional se tag for fornecida)
    Retorno:
        Tupla (sucesso, mensagem)
        - sucesso: boolean indicando se o comando foi enviado com sucesso
        - mensagem: string com mensagem de sucesso ou erro
    """
    # Se não foi fornecida uma tag, tenta obter da base de dados
    if not tag and ar_id:
        try:
            ar = Ar_condicionado.objects.get(id=ar_id)
            tag = ar.tag
        except Ar_condicionado.DoesNotExist:
            return False, "Ar-condicionado não encontrado"
    
    # Verifica se a tag está no dicionário de IPs
    if tag not in ESP32_IPS:
        return False, f"Tag '{tag}' não encontrada no mapeamento de IPs"
    
    # Obtém o IP correspondente à tag
    ip = ESP32_IPS[tag]
    url = f"http://{ip}/{comando}"
    
    try:
        if params:
            response = requests.get(url, params=params, timeout=3)
        else:
            response = requests.get(url, timeout=3)
        
        if response.status_code == 200:
            return True, response.text
        else:
            return False, f"Erro: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        return False, f"Erro de conexão: {str(e)}"

@login_required
@admin_required
def automacao_home(request):
    """Página inicial de automação com seleção de subsistemas"""
    ar_total = Ar_condicionado.objects.count()
    ar_online = Ar_condicionado.objects.filter(online=True).count()
    
    # Buscar dados médios dos dispositivos online
    temperatura_media = 0
    consumo_total = 0
    
    ars_online = Ar_condicionado.objects.filter(online=True)
    if ars_online.exists():
        for ar in ars_online:
            temperatura_media += ar.temperatura_ambiente if ar.temperatura_ambiente else 0
            consumo_total += ar.consumo_atual if ar.consumo_atual else 0
        
        temperatura_media = round(temperatura_media / ars_online.count(), 1)
    
    return render(request, 'Controle_ar/automacao_home.html', {
        'ar_count': ar_total,
        'ar_online': ar_online,
        'temperatura_media': temperatura_media,
        'consumo_total': round(consumo_total, 2),
    })

@login_required
@admin_required
def ar_dashboard(request):
    """Exibe todos os ar-condicionados disponíveis para controle"""
    try:
        # Verifica status de todos os ar-condicionados
        ars = Ar_condicionado.objects.all()
        
        # Tenta atualizar o status de conexão de cada ar (simulado por enquanto)
        for ar in ars:
            try:
                # Tentativa de conexão com o ESP32 para verificar status
                sucesso, _ = enviar_comando_esp32('status')
                ar.online = sucesso
                ar.ultimo_ping = timezone.now()
                ar.save()
            except:
                ar.online = False
                ar.save()
        
        return render(request, 'Controle_ar/ar_dashboard.html', {'ars': ars})
    except Exception as e:
        messages.error(request, f"Erro ao carregar dashboard: {str(e)}")
        return redirect('home')

# Renomear o método original dashboard para ar_dashboard e manter um redirecionamento por compatibilidade
@login_required
@admin_required
def dashboard(request):
    """Redirecionamento para compatibilidade"""
    return ar_dashboard(request)

@login_required
@admin_required
def controlar_ar(request, ar_id):
    """Página para controlar um ar-condicionado específico"""
    ar = get_object_or_404(Ar_condicionado, pk=ar_id)
    
    # Se estiver online, tenta sincronizar status
    if ar.online:
        try:
            sucesso, resposta = enviar_comando_esp32('status')
            if sucesso:
                # Aqui você pode analisar a resposta para atualizar o status no banco
                # Exemplo: resposta = "Temperatura atual: 22°C.\nEstado: Ligado"
                # Por enquanto, vamos simular:
                ar.temperatura_ambiente = 25.0  # Valor simulado
            else:
                ar.online = False
                ar.save()
                messages.warning(request, "Dispositivo offline. Exibindo último estado conhecido.")
        except:
            ar.online = False
            ar.save()
            messages.warning(request, "Dispositivo offline. Exibindo último estado conhecido.")
                
    return render(request, 'Controle_ar/controlar_ar.html', {'ar': ar})

@login_required
@admin_required
def ligar_ar(request, ar_id):
    """Liga um ar-condicionado"""
    ar = get_object_or_404(Ar_condicionado, pk=ar_id)
    
    sucesso, mensagem = enviar_comando_esp32('ligar', ar_id=ar_id)
    if sucesso:
        ar.estado = True
        ar.save()
        
        # Registra o comando e o log
        Comando_ar.objects.create(
            ar_condicionado=ar,
            comando="ligar",
            executado=True
        )
        
        LogOperacao.objects.create(
            ar_condicionado=ar,
            operacao="Ligado",
            usuario=request.user.username
        )
        
        messages.success(request, f"Ar-condicionado {ar.nome} foi ligado com sucesso.")
    else:
        messages.error(request, f"Falha ao ligar o ar-condicionado: {mensagem}")
    
    return redirect('Controle_ar:controlar_ar', ar_id=ar_id)

@login_required
@admin_required
def desligar_ar(request, ar_id):
    """Desliga um ar-condicionado"""
    ar = get_object_or_404(Ar_condicionado, pk=ar_id)
    
    sucesso, mensagem = enviar_comando_esp32('desligar', ar_id=ar_id)
    if sucesso:
        ar.estado = False
        ar.save()
        
        # Registra o comando e o log
        Comando_ar.objects.create(
            ar_condicionado=ar,
            comando="desligar",
            executado=True
        )
        
        LogOperacao.objects.create(
            ar_condicionado=ar,
            operacao="Desligado",
            usuario=request.user.username
        )
        
        messages.success(request, f"Ar-condicionado {ar.nome} foi desligado com sucesso.")
    else:
        messages.error(request, f"Falha ao desligar o ar-condicionado: {mensagem}")
    
    return redirect('Controle_ar:controlar_ar', ar_id=ar_id)

@login_required
@admin_required
def ajustar_temperatura(request, ar_id):
    """Ajusta a temperatura de um ar-condicionado"""
    if request.method != 'POST':
        return redirect('Controle_ar:controlar_ar', ar_id=ar_id)
    
    ar = get_object_or_404(Ar_condicionado, pk=ar_id)
    nova_temp = int(request.POST.get('temperatura', ar.temperatura))
    
    # Verifica limites
    if nova_temp < 17:
        nova_temp = 17
        messages.warning(request, "Temperatura mínima permitida é 17°C")
    elif nova_temp > 28:
        nova_temp = 28
        messages.warning(request, "Temperatura máxima permitida é 28°C")
    
    # Envia comando
    sucesso, mensagem = enviar_comando_esp32('definir_temperatura', {'temp': nova_temp}, ar_id=ar_id)
    
    if sucesso:
        # Atualiza a temperatura no banco
        ar.temperatura = nova_temp
        ar.save()
        
        # Registra o comando e o log
        Comando_ar.objects.create(
            ar_condicionado=ar,
            comando=f"temperatura:{nova_temp}",
            executado=True
        )
        
        LogOperacao.objects.create(
            ar_condicionado=ar,
            operacao=f"Temperatura ajustada para {nova_temp}°C",
            usuario=request.user.username
        )
        
        messages.success(request, f"Temperatura ajustada para {nova_temp}°C")
    else:
        messages.error(request, f"Falha ao ajustar temperatura: {mensagem}")
    
    return redirect('Controle_ar:controlar_ar', ar_id=ar_id)

@login_required
@admin_required
def ajustar_modo(request, ar_id):
    """Ajusta o modo de operação do ar-condicionado"""
    if request.method != 'POST':
        return redirect('Controle_ar:controlar_ar', ar_id=ar_id)
    
    ar = get_object_or_404(Ar_condicionado, pk=ar_id)
    modo = request.POST.get('modo')
    
    # No momento o ESP32 não tem endpoint para mudar o modo
    # Então vamos apenas registrar a mudança no sistema
    ar.modo = modo
    ar.save()
    
    # Registrar log da operação
    LogOperacao.objects.create(
        ar_condicionado=ar,
        operacao=f"Modo alterado para {ar.modo_display}",
        usuario=request.user.username
    )
    
    messages.success(request, f"Modo alterado para {ar.modo_display}")
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

@login_required
@admin_required
def verificar_status(request, ar_id):
    """Verifica o status atual do ar-condicionado via ESP32"""
    ar = get_object_or_404(Ar_condicionado, pk=ar_id)
    
    # Tenta obter status atual do ESP32
    sucesso, mensagem = enviar_comando_esp32('status', ar_id=ar_id)
    
    if sucesso:
        ar.online = True
        ar.ultimo_ping = timezone.now()
        
        # Em uma implementação completa, aqui seria feito o parsing da resposta
        # Por enquanto, apenas atualiza o status no banco
        # No futuro: analisar a mensagem para extrair temperatura, estado, etc
        
        ar.save()
        return JsonResponse({
            'status': 'success',
            'online': True,
            'message': mensagem
        })
    else:
        ar.online = False
        ar.save()
        return JsonResponse({
            'status': 'error',
            'online': False,
            'message': 'Dispositivo offline. Tentativa de conexão falhou.'
        })
