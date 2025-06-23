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

# Mapeamento de tags para IPs dos ESP32 - LIBERADO PARA QUALQUER IP
ESP32_IPS = {}  # Vazio para permitir qualquer IP

# Função auxiliar para verificar se um IP é válido
def is_valid_ip(ip):
    """Verifica se o IP está em uma faixa válida - LIBERADO PARA QUALQUER IP"""
    try:
        import ipaddress
        addr = ipaddress.IPv4Address(ip)
        # Permite qualquer IP válido
        return True
    except:
        return False

# Função para obter um nome de usuário válido para logs
def get_valid_username(request):
    """Retorna um nome de usuário válido para logs, nunca retorna vazio"""
    nome_usuario = request.user.username
    if not nome_usuario:
        if request.user.first_name or request.user.last_name:
            nome_usuario = f"{request.user.first_name} {request.user.last_name}".strip()
        if not nome_usuario:
            nome_usuario = f"Usuário ID: {request.user.id}"
    return nome_usuario

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
def enviar_comando_esp32(comando, params=None, tag=None, ar_id=None, ip_direto=None):
    """
    Envia comandos HTTP ao ESP32.
    Parâmetros:
        comando: string com o comando (ligar, desligar, etc)
        params: dicionário com parâmetros adicionais
        tag: tag do ar-condicionado (opcional se ar_id ou ip_direto for fornecido)
        ar_id: id do ar-condicionado (opcional se tag ou ip_direto for fornecida)
        ip_direto: IP direto do ESP32 (opcional, sobrescreve outros métodos)
    Retorno:
        Tupla (sucesso, mensagem)
        - sucesso: boolean indicando se o comando foi enviado com sucesso
        - mensagem: string com mensagem de sucesso ou erro
    """
    ip = None
    
    # Se foi fornecido um IP direto, usa ele
    if ip_direto:
        ip = ip_direto
    # Se não foi fornecida uma tag, tenta obter da base de dados
    elif not tag and ar_id:
        try:
            ar = Ar_condicionado.objects.get(id=ar_id)
            tag = ar.tag
        except Ar_condicionado.DoesNotExist:
            return False, "Ar-condicionado não encontrado"
    
    # Se ainda não tem IP, verifica no mapeamento ou aceita qualquer IP da tag
    if not ip:
        if tag in ESP32_IPS:
            ip = ESP32_IPS[tag]
        else:
            # Para facilitar a conexão, permite que o ESP32 se registre automaticamente
            # Usa um IP padrão ou tenta descobrir através da tag
            return False, f"IP não encontrado para a tag '{tag}'. Configure o IP no sistema ou permita registro automático."
    
    # Verifica se o IP é válido
    if not is_valid_ip(ip):
        return False, f"IP inválido: {ip}"
    
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
        
        temperatura_media = round(temperatura_media / ars_online.count(), 1) if temperatura_media > 0 else 0
    
    # Busca todos os ar-condicionados para o template
    ares = Ar_condicionado.objects.all()
    
    return render(request, 'Controle_ar/home.html', {
        'ar_count': ar_total,
        'ar_online': ar_online,
        'temperatura_media': temperatura_media,
        'consumo_total': round(consumo_total, 2),
        'ares': ares,  # Adiciona a variável ares que o template espera
    })

@login_required
@admin_required
def ar_dashboard(request):
    """Exibe todos os ar-condicionados disponíveis para controle"""
    try:
        # Verifica status de todos os ar-condicionados
        ars = Ar_condicionado.objects.all()
        
        # Tenta atualizar o status de conexão de cada ar (opcional - apenas para os que têm IP configurado)
        for ar in ars:
            try:
                # Tentativa de conexão com o ESP32 para verificar status
                if ar.tag in ESP32_IPS or hasattr(ar, 'ip_address'):
                    ip = ESP32_IPS.get(ar.tag) or getattr(ar, 'ip_address', None)
                    if ip:
                        sucesso, _ = enviar_comando_esp32('status', ip_direto=ip)
                        ar.online = sucesso
                        if sucesso:
                            ar.ultimo_ping = timezone.now()
                    else:
                        # Se não tem IP configurado, mantém status atual
                        pass
                else:
                    # Dispositivo sem IP configurado - mantém como offline
                    ar.online = False
                ar.save()
            except Exception as e:
                ar.online = False
                ar.save()
                print(f"Erro ao verificar status do ar {ar.nome}: {e}")
        
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
            # Verifica se tem IP configurado para este ar
            ip = ESP32_IPS.get(ar.tag) or getattr(ar, 'ip_address', None)
            if ip:
                sucesso, resposta = enviar_comando_esp32('status', ip_direto=ip)
                if sucesso:
                    # Aqui você pode analisar a resposta para atualizar o status no banco
                    # Exemplo: resposta = "Temperatura atual: 22°C.\nEstado: Ligado"
                    # Por enquanto, vamos simular:
                    ar.temperatura_ambiente = 25.0  # Valor simulado
                else:
                    ar.online = False
                    ar.save()
                    messages.warning(request, "Dispositivo offline. Exibindo último estado conhecido.")
            else:
                messages.info(request, "IP não configurado para este dispositivo.")
        except Exception as e:
            ar.online = False
            ar.save()
            messages.warning(request, f"Dispositivo offline: {e}. Exibindo último estado conhecido.")
    
    # Usar o template AJAX para operações assíncronas
    return render(request, 'Controle_ar/controlar_ar_ajax.html', {'ar': ar})

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
    """API para o ESP32 informar status e receber comandos"""
    if request.method == "POST":
        try:
            # Obter IP do cliente
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
            if ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
            
            # Log de debugging
            print(f"Requisição recebida de IP: {client_ip}")
            print(f"Content-Type: {request.META.get('CONTENT_TYPE', 'não especificado')}")
            print(f"Body raw: {request.body}")
            
            # Verifica se o IP é válido - agora permite qualquer IP
            if not client_ip or client_ip == '':
                return JsonResponse({
                    'status': 'error',
                    'message': 'IP do cliente não pôde ser determinado'
                }, status=400)
            
            # Não verifica mais restrições de IP - permite qualquer IP válido
            if not is_valid_ip(client_ip):
                print(f"IP inválido: {client_ip}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'IP inválido: {client_ip}'
                }, status=400)
            
            # Parse do JSON do corpo da requisição
            data = {}
            try:
                if request.body:
                    data = json.loads(request.body.decode('utf-8'))
                    print(f"Dados JSON recebidos: {data}")
                else:
                    print("Corpo da requisição vazio, tentando POST data")
                    data = dict(request.POST.items())
                    print(f"Dados POST recebidos: {data}")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"Erro ao fazer parse do JSON: {e}")
                # Se não conseguir fazer parse do JSON, tenta como form data
                data = dict(request.POST.items())
                print(f"Usando form data: {data}")
            
            tag = data.get('tag')
            
            # Se não fornecer tag, tenta criar/encontrar um baseado no IP
            if not tag:
                tag = f"esp32-{client_ip.replace('.', '-')}"
                print(f"Tag gerada automaticamente: {tag}")
            
            # Busca ou cria o ar-condicionado
            try:
                ar, created = Ar_condicionado.objects.get_or_create(
                    tag=tag,
                    defaults={
                        'nome': f'Ar Condicionado {tag}',
                        'estado': False,
                        'temperatura': 24,
                        'modo': 'cold',
                        'velocidade': 1,
                        'online': True
                    }
                )
                
                if created:
                    print(f"Novo ar-condicionado criado: {ar.nome} com tag {tag}")
                    # Marca o novo dispositivo na sessão para notificação
                    new_devices = request.session.get('new_devices', [])
                    new_devices.append({
                        'id': ar.id,
                        'tag': ar.tag,
                        'nome': ar.nome,
                        'ip': client_ip
                    })
                    request.session['new_devices'] = new_devices
                    request.session.modified = True
                else:
                    print(f"Ar-condicionado encontrado: {ar.nome}")
                
            except Exception as e:
                print(f"Erro ao buscar/criar ar-condicionado: {e}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Erro ao processar dispositivo: {str(e)}'
                }, status=500)
            
            # Atualizar status baseado no relatório do ESP
            ar.online = True
            ar.ultimo_ping = timezone.now()
            
            # Se foi criado agora, registra o IP no mapeamento
            if created:
                ESP32_IPS[tag] = client_ip
                print(f"Novo ESP32 registrado: {tag} -> {client_ip}")
            else:
                # Atualiza o IP no mapeamento se mudou
                ESP32_IPS[tag] = client_ip
            
            # Atualizar dados se fornecidos
            if 'temperatura_ambiente' in data:
                try:
                    ar.temperatura_ambiente = float(data.get('temperatura_ambiente'))
                    print(f"Temperatura ambiente atualizada: {ar.temperatura_ambiente}")
                except (ValueError, TypeError) as e:
                    print(f"Erro ao converter temperatura_ambiente: {e}")
            
            if 'consumo' in data:
                try:
                    ar.consumo_atual = float(data.get('consumo'))
                    print(f"Consumo atualizado: {ar.consumo_atual}")
                except (ValueError, TypeError) as e:
                    print(f"Erro ao converter consumo: {e}")
            
            if 'estado' in data:
                ar.estado = bool(data.get('estado'))
                print(f"Estado atualizado: {ar.estado}")
            
            if 'temperatura' in data:
                try:
                    ar.temperatura = int(data.get('temperatura'))
                    print(f"Temperatura configurada atualizada: {ar.temperatura}")
                except (ValueError, TypeError) as e:
                    print(f"Erro ao converter temperatura: {e}")
            
            ar.save()
            
            # Verificar se há comandos pendentes
            comandos = Comando_ar.objects.filter(ar_condicionado=ar, executado=False).order_by('data_hora')
            
            if comandos.exists():
                comando = comandos.first()
                comando.executado = True
                comando.save()
                
                print(f"Comando enviado para {tag}: {comando.comando}")
                
                return JsonResponse({
                    'status': 'success',
                    'comando': comando.comando,
                    'ip_registrado': client_ip,
                    'tag': tag
                })
            
            return JsonResponse({
                'status': 'success',
                'comando': 'none',
                'ip_registrado': client_ip,
                'tag': tag
            })
            
        except Exception as e:
            print(f"Erro geral na API status: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'message': f'Erro interno do servidor: {str(e)}'
            }, status=500)
    
    # Para requisições GET, retorna informações da API
    elif request.method == "GET":
        # Verifica se há novos dispositivos na sessão
        new_devices = request.session.get('new_devices', [])
        # Limpa a sessão após uso
        if new_devices:
            request.session['new_devices'] = []
            request.session.modified = True
        
        return JsonResponse({
            'status': 'success',
            'message': 'API de status do ESP32',
            'endpoints': {
                'POST': 'Enviar status e receber comandos',
                'GET': 'Informações da API'
            },
            'exemplo_payload': {
                'tag': 'esp32-001',
                'temperatura_ambiente': 25.5,
                'consumo': 1.2,
                'estado': True,
                'temperatura': 24
            },
            'new_devices': new_devices
        })
    
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
    ip = ESP32_IPS.get(ar.tag) or getattr(ar, 'ip_address', None)
    if ip:
        sucesso, mensagem = enviar_comando_esp32('status', ip_direto=ip)
    else:
        sucesso, mensagem = False, "IP não configurado para este dispositivo"
    
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

# Novas funções para controle via AJAX
@csrf_exempt
@login_required
@admin_required
def ligar_ar_ajax(request, ar_id):
    """Liga um ar-condicionado via AJAX"""
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
            usuario=get_valid_username(request)
        )
        
        return JsonResponse({
            'success': True,
            'message': f"Ar-condicionado {ar.nome} foi ligado com sucesso.",
            'data': {
                'id': ar.id,
                'estado': ar.estado,
                'temperatura': ar.temperatura,
                'modo': ar.modo,
                'velocidade': ar.velocidade,
                'swing': ar.swing,
                'online': ar.online,
                'ultimo_ping': ar.ultimo_ping.strftime("%d/%m/%Y %H:%M:%S") if ar.ultimo_ping else None
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'message': f"Falha ao ligar o ar-condicionado: {mensagem}"
        })

@csrf_exempt
@login_required
@admin_required
def desligar_ar_ajax(request, ar_id):
    """Desliga um ar-condicionado via AJAX"""
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
            usuario=get_valid_username(request)
        )
        
        return JsonResponse({
            'success': True,
            'message': f"Ar-condicionado {ar.nome} foi desligado com sucesso.",
            'data': {
                'id': ar.id,
                'estado': ar.estado,
                'temperatura': ar.temperatura,
                'modo': ar.modo,
                'velocidade': ar.velocidade,
                'swing': ar.swing,
                'online': ar.online,
                'ultimo_ping': ar.ultimo_ping.strftime("%d/%m/%Y %H:%M:%S") if ar.ultimo_ping else None
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'message': f"Falha ao desligar o ar-condicionado: {mensagem}"
        })

@csrf_exempt
@login_required
@admin_required
def ajustar_temperatura_ajax(request, ar_id):
    """Ajusta a temperatura de um ar-condicionado via AJAX"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': "Método não permitido"
        }, status=405)
    
    ar = get_object_or_404(Ar_condicionado, pk=ar_id)
    
    try:
        data = json.loads(request.body)
        nova_temp = int(data.get('temperatura', ar.temperatura))
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({
            'success': False,
            'message': "Dados inválidos"
        }, status=400)
    
    # Verifica limites
    if nova_temp < 17:
        nova_temp = 17
        mensagem_limite = "Temperatura ajustada para o mínimo de 17°C"
    elif nova_temp > 28:
        nova_temp = 28
        mensagem_limite = "Temperatura ajustada para o máximo de 28°C"
    else:
        mensagem_limite = None
    
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
        
        return JsonResponse({
            'success': True,
            'message': mensagem_limite or f"Temperatura ajustada para {nova_temp}°C",
            'data': {
                'id': ar.id,
                'temperatura': ar.temperatura,
                'online': ar.online
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'message': f"Falha ao ajustar temperatura: {mensagem}"
        })

@csrf_exempt
@login_required
@admin_required
def ajustar_modo_ajax(request, ar_id):
    """Ajusta o modo de operação do ar-condicionado via AJAX"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': "Método não permitido"
        }, status=405)
    
    ar = get_object_or_404(Ar_condicionado, pk=ar_id)
    
    try:
        data = json.loads(request.body)
        modo = data.get('modo', ar.modo)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': "Dados inválidos"
        }, status=400)
    
    # No momento o ESP32 não tem endpoint para mudar o modo
    # Então vamos apenas registrar a mudança no sistema
    ar.modo = modo
    ar.save()
    
    # Obter o texto amigável do modo
    modo_display = ar.modo_display
    
    # Registrar log da operação
    LogOperacao.objects.create(
        ar_condicionado=ar,
        operacao=f"Modo alterado para {modo_display}",
        usuario=request.user.username
    )
    
    return JsonResponse({
        'success': True,
        'message': f"Modo alterado para {modo_display}",
        'data': {
            'id': ar.id,
            'modo': ar.modo,
            'modo_display': modo_display,
            'online': ar.online
        }
    })

@csrf_exempt
@login_required
@admin_required
def ajustar_velocidade_ajax(request, ar_id):
    """Ajusta a velocidade do ventilador do ar-condicionado via AJAX"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': "Método não permitido"
        }, status=405)
    
    try:
        data = json.loads(request.body)
        nova_velocidade = int(data.get('velocidade', 1))
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({
            'success': False,
            'message': "Dados inválidos"
        }, status=400)
        
    ar = get_object_or_404(Ar_condicionado, id=ar_id)
    
    if 1 <= nova_velocidade <= 4:  # Incluindo velocidade 4 (automática)
        ar.velocidade = nova_velocidade
        ar.save()
        
        # Se o ar estiver ligado, enviar comando de ajuste
        if ar.estado:
            Comando_ar.objects.create(
                ar_condicionado=ar,
                comando=f"velocidade:{nova_velocidade}"
            )
        
        # Obter o texto amigável da velocidade
        velocidade_display = ar.velocidade_display
        
        # Registrar no log
        LogOperacao.objects.create(
            ar_condicionado=ar,
            operacao=f"Velocidade alterada para {velocidade_display}",
            usuario=f"{request.user.first_name} {request.user.last_name}"
        )
        
        # Registrar no log geral
        Action.objects.create(
            author=f"{request.user.first_name} {request.user.last_name}",
            type="Ar Condicionado",
            description=f"Alterou a velocidade do ar-condicionado {ar.nome} para {velocidade_display}",
            date=datetime.date.today(),
            time=datetime.datetime.now().time()
        )
        
        return JsonResponse({
            'success': True,
            'message': f"Velocidade alterada para {velocidade_display}",
            'data': {
                'id': ar.id,
                'velocidade': ar.velocidade,
                'velocidade_display': velocidade_display,
                'online': ar.online
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'message': f"Velocidade inválida: {nova_velocidade}. Deve ser entre 1 e 4."
        }, status=400)

@csrf_exempt
@login_required
@admin_required
def toggle_swing_ajax(request, ar_id):
    """Alterna o modo swing do ar-condicionado via AJAX"""
    ar = get_object_or_404(Ar_condicionado, id=ar_id)
    ar.swing = not ar.swing
    ar.save()
    
    status_swing = "ativado" if ar.swing else "desativado"
    
    # Se o ar estiver ligado, enviar comando de ajuste
    if ar.estado:
        Comando_ar.objects.create(
            ar_condicionado=ar,
            comando=f"swing:{1 if ar.swing else 0}"
        )
    
    # Registrar no log
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
    
    return JsonResponse({
        'success': True,
        'message': f"Swing {status_swing}",
        'data': {
            'id': ar.id,
            'swing': ar.swing,
            'online': ar.online
        }
    })

@login_required
@admin_required
def verificar_status_ajax(request, ar_id):
    """Verifica o status atual do ar-condicionado via ESP32 (Versão AJAX)"""
    ar = get_object_or_404(Ar_condicionado, pk=ar_id)
    
    # Verificar se o cliente enviou um timestamp para checar alterações
    timestamp_str = request.GET.get('timestamp')
    checking_changes = False
    
    if timestamp_str:
        try:
            # Converter o timestamp para um objeto datetime
            timestamp = datetime.datetime.fromtimestamp(int(timestamp_str)/1000.0, tz=timezone.get_current_timezone())
            checking_changes = True
            
            # Verificar se houve alterações desde o timestamp
            mudou = LogOperacao.objects.filter(
                ar_condicionado=ar,
                data_hora__gt=timestamp
            ).exists()
            
            # Se está apenas verificando mudanças e não houve alterações, retorna imediatamente
            if checking_changes and not mudou:
                return JsonResponse({
                    'success': True,
                    'changed': False,
                    'message': "Sem alterações"
                })
        except (ValueError, TypeError, OverflowError):
            # Se o timestamp for inválido, ignorar e continuar normalmente
            pass
    
    # Tenta obter status atual do ESP32
    ip = ESP32_IPS.get(ar.tag) or getattr(ar, 'ip_address', None)
    if ip:
        sucesso, mensagem = enviar_comando_esp32('status', ip_direto=ip)
    else:
        sucesso, mensagem = False, "IP não configurado para este dispositivo"
    
    if sucesso:
        ar.online = True
        ar.ultimo_ping = timezone.now()
        
        # Em uma implementação completa, aqui seria feito o parsing da resposta
        # Por enquanto, apenas atualiza o status no banco
        
        ar.save()
        
        return JsonResponse({
            'success': True,
            'changed': checking_changes,  # Indica se está respondendo a uma verificação de mudanças
            'message': "Dispositivo online",
            'data': {
                'id': ar.id,
                'nome': ar.nome,
                'estado': ar.estado,
                'temperatura': ar.temperatura,
                'temperatura_ambiente': ar.temperatura_ambiente,
                'modo': ar.modo,
                'modo_display': ar.modo_display,
                'velocidade': ar.velocidade,
                'velocidade_display': ar.velocidade_display,
                'swing': ar.swing,
                'online': ar.online,
                'consumo_atual': ar.consumo_atual,
                'ultimo_ping': ar.ultimo_ping.strftime("%d/%m/%Y %H:%M:%S") if ar.ultimo_ping else None
            }
        })
    else:
        ar.online = False
        ar.save()
        
        return JsonResponse({
            'success': False,
            'changed': checking_changes,
            'message': 'Dispositivo offline. Tentativa de conexão falhou.',
            'data': {
                'id': ar.id,
                'online': ar.online
            }
        })
