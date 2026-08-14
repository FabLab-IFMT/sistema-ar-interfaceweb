import json
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Estufa, LeituraEstufa, LogOperacaoEstufa


def staff_required(view_func):
    """Mesmo critério do módulo de automação (Controle_ar): apenas staff."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Acesso negado. Apenas membros da equipe podem acessar a automação.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def _float_ou_none(valor):
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return None
    # DHT22 com falha manda NaN — não persistimos
    return v if v == v else None


def _autenticar_dispositivo(request):
    """Resolve a estufa pelo header X-Estufa-Token.

    Retorna (estufa, None) em caso de sucesso ou (None, JsonResponse de erro).
    """
    token = request.headers.get('X-Estufa-Token', '')
    if not token:
        return None, JsonResponse({'erro': 'Token ausente'}, status=401)
    try:
        return Estufa.objects.get(token=token), None
    except Estufa.DoesNotExist:
        return None, JsonResponse({'erro': 'Token inválido'}, status=403)


def _payload_comandos(estufa):
    """Estado desejado completo, enviado ao ESP32 em toda resposta."""
    return {
        'ok': True,
        'modo_desejado': estufa.modo_desejado,
        'controle': estufa.controle,
        'lampada_desejada': estufa.lampada_desejada,
        'cooler_desejado': estufa.cooler_desejado,
        'temp_alvo_sec': estufa.temp_alvo_sec,
        'temp_max_sec': estufa.temp_max_sec,
        'histerese_sec': estufa.histerese_sec,
        'temp_max_arm': estufa.temp_max_arm,
        'temp_min_arm': estufa.temp_min_arm,
    }


@csrf_exempt
def api_comandos(request):
    """Poll leve e frequente do ESP32 (~2,5 s): só devolve o estado desejado.

    Serve como heartbeat — atualiza ultimo_contato sem gravar leitura.
    """
    estufa, erro = _autenticar_dispositivo(request)
    if erro:
        return erro

    Estufa.objects.filter(pk=estufa.pk).update(ultimo_contato=timezone.now())
    return JsonResponse(_payload_comandos(estufa))


@csrf_exempt
def api_telemetria(request):
    """Endpoint chamado pelo ESP32 da estufa a cada ~30 s.

    Recebe POST JSON com as leituras e o estado atual, e responde com o
    estado desejado. Se o payload trouxer origem_botao=true, o modo
    reportado pelo dispositivo vira o modo desejado (o botão físico tem
    prioridade sobre a interface web).
    """
    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido'}, status=405)

    estufa, erro = _autenticar_dispositivo(request)
    if erro:
        return erro

    try:
        dados = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'erro': 'JSON inválido'}, status=400)

    modo = dados.get('modo', estufa.modo_atual)
    if modo not in (Estufa.MODO_SECAGEM, Estufa.MODO_ARMAZEM):
        return JsonResponse({'erro': 'Modo inválido'}, status=400)

    estado = dados.get('estado', 'ESTAVEL')
    estados_validos = {e[0] for e in Estufa.ESTADO_CHOICES}
    if estado not in estados_validos:
        estado = 'ESTAVEL'

    leitura = LeituraEstufa.objects.create(
        estufa=estufa,
        modo=modo,
        estado=estado,
        temperatura_media=_float_ou_none(dados.get('temperatura_media')),
        umidade_media=_float_ou_none(dados.get('umidade_media')),
        lampada_ligada=bool(dados.get('lampada', False)),
        cooler_ligado=bool(dados.get('cooler', False)),
        **{
            campo: _float_ou_none(dados.get(campo))
            for campo in ('t1', 'h1', 't2', 'h2', 't3', 'h3', 't4', 'h4', 't5', 'h5')
        },
    )

    # Botão físico apertado no laboratório manda no modo
    if dados.get('origem_botao') and modo != estufa.modo_desejado:
        estufa.modo_desejado = modo
        LogOperacaoEstufa.objects.create(
            estufa=estufa,
            operacao=f'Modo alterado para {modo} pelo botão físico',
            usuario='dispositivo',
        )

    estufa.modo_atual = modo
    estufa.estado = leitura.estado
    estufa.temperatura_media = leitura.temperatura_media
    estufa.umidade_media = leitura.umidade_media
    estufa.lampada_ligada = leitura.lampada_ligada
    estufa.cooler_ligado = leitura.cooler_ligado
    estufa.ultimo_contato = timezone.now()
    estufa.save()

    return JsonResponse(_payload_comandos(estufa))


@login_required
@staff_required
def dashboard(request):
    estufas = Estufa.objects.all()
    return render(request, 'estufa/dashboard.html', {'estufas': estufas})


@login_required
@staff_required
def detalhe(request, estufa_id):
    estufa = get_object_or_404(Estufa, pk=estufa_id)
    leituras = estufa.leituras.all()[:60]
    logs = estufa.logs.all()[:20]
    return render(request, 'estufa/detalhe.html', {
        'estufa': estufa,
        'leituras': leituras,
        'logs': logs,
    })


def _log(estufa, request, mensagem):
    LogOperacaoEstufa.objects.create(
        estufa=estufa, operacao=mensagem, usuario=str(request.user))


@login_required
@staff_required
@require_POST
def definir_modo(request, estufa_id):
    estufa = get_object_or_404(Estufa, pk=estufa_id)
    modo = request.POST.get('modo', '')
    if modo not in (Estufa.MODO_SECAGEM, Estufa.MODO_ARMAZEM):
        return JsonResponse({'erro': 'Modo inválido'}, status=400)

    if modo != estufa.modo_desejado:
        estufa.modo_desejado = modo
        estufa.save(update_fields=['modo_desejado'])
        _log(estufa, request, f'Modo alterado para {modo} pela interface web')

    return JsonResponse({'ok': True, 'modo_desejado': estufa.modo_desejado})


@login_required
@staff_required
@require_POST
def definir_controle(request, estufa_id):
    estufa = get_object_or_404(Estufa, pk=estufa_id)
    controle = request.POST.get('controle', '')
    if controle not in (Estufa.CONTROLE_AUTO, Estufa.CONTROLE_MANUAL):
        return JsonResponse({'erro': 'Controle inválido'}, status=400)

    if controle != estufa.controle:
        estufa.controle = controle
        if controle == Estufa.CONTROLE_MANUAL:
            # Parte do estado atual reportado, para não haver solavanco
            estufa.lampada_desejada = estufa.lampada_ligada
            estufa.cooler_desejado = estufa.cooler_ligado
        estufa.save(update_fields=['controle', 'lampada_desejada', 'cooler_desejado'])
        _log(estufa, request, f'Controle alterado para {estufa.get_controle_display()}')

    return JsonResponse({'ok': True, 'controle': estufa.controle})


@login_required
@staff_required
@require_POST
def definir_atuador(request, estufa_id):
    """Liga/desliga lâmpada ou cooler. Ativa o controle manual automaticamente."""
    estufa = get_object_or_404(Estufa, pk=estufa_id)
    atuador = request.POST.get('atuador', '')
    acao = request.POST.get('acao', '')
    if atuador not in ('lampada', 'cooler') or acao not in ('on', 'off'):
        return JsonResponse({'erro': 'Comando inválido'}, status=400)

    ligar = (acao == 'on')
    campos = ['controle']
    if estufa.controle != Estufa.CONTROLE_MANUAL:
        estufa.controle = Estufa.CONTROLE_MANUAL
        # Congela o outro atuador no estado atual reportado
        estufa.lampada_desejada = estufa.lampada_ligada
        estufa.cooler_desejado = estufa.cooler_ligado
        campos += ['lampada_desejada', 'cooler_desejado']
        _log(estufa, request, 'Controle manual ativado por comando de atuador')

    if atuador == 'lampada':
        estufa.lampada_desejada = ligar
        campos.append('lampada_desejada')
    else:
        estufa.cooler_desejado = ligar
        campos.append('cooler_desejado')

    estufa.save(update_fields=list(set(campos)))
    _log(estufa, request,
         f'{"Lâmpada" if atuador == "lampada" else "Cooler"} '
         f'{"ligada(o)" if ligar else "desligada(o)"} pela interface web')

    return JsonResponse({
        'ok': True,
        'controle': estufa.controle,
        'lampada_desejada': estufa.lampada_desejada,
        'cooler_desejado': estufa.cooler_desejado,
    })


@login_required
@staff_required
@require_POST
def definir_parametros(request, estufa_id):
    estufa = get_object_or_404(Estufa, pk=estufa_id)

    valores = {}
    for campo in ('temp_alvo_sec', 'temp_max_sec', 'histerese_sec',
                  'temp_max_arm', 'temp_min_arm'):
        v = _float_ou_none(request.POST.get(campo))
        if v is None:
            return JsonResponse({'erro': f'Valor inválido para {campo}'}, status=400)
        valores[campo] = v

    # Sanidade: limites físicos da estufa e coerência entre parâmetros
    erros = []
    for campo, v in valores.items():
        if not (0 <= v <= 60):
            erros.append(f'{campo} deve estar entre 0 e 60')
    if not (0.1 <= valores['histerese_sec'] <= 5):
        erros.append('histerese_sec deve estar entre 0.1 e 5')
    if valores['temp_alvo_sec'] >= valores['temp_max_sec']:
        erros.append('temp_alvo_sec deve ser menor que temp_max_sec')
    if valores['temp_min_arm'] >= valores['temp_max_arm']:
        erros.append('temp_min_arm deve ser menor que temp_max_arm')
    if erros:
        return JsonResponse({'erro': '; '.join(erros)}, status=400)

    for campo, v in valores.items():
        setattr(estufa, campo, v)
    estufa.save(update_fields=list(valores))
    _log(estufa, request,
         'Parâmetros atualizados: '
         f'secagem alvo {valores["temp_alvo_sec"]}°C / máx {valores["temp_max_sec"]}°C '
         f'/ hist {valores["histerese_sec"]}°C; '
         f'armazém {valores["temp_min_arm"]}–{valores["temp_max_arm"]}°C')

    return JsonResponse({'ok': True, **{c: valores[c] for c in valores}})


@login_required
@staff_required
def status_ajax(request, estufa_id):
    """Consumido pela página de detalhe para atualizar o painel sem reload."""
    estufa = get_object_or_404(Estufa, pk=estufa_id)
    return JsonResponse({
        'online': estufa.online,
        'modo_atual': estufa.modo_atual,
        'modo_desejado': estufa.modo_desejado,
        'controle': estufa.controle,
        'lampada_desejada': estufa.lampada_desejada,
        'cooler_desejado': estufa.cooler_desejado,
        'estado': estufa.estado,
        'estado_display': estufa.get_estado_display(),
        'temperatura_media': estufa.temperatura_media,
        'umidade_media': estufa.umidade_media,
        'lampada_ligada': estufa.lampada_ligada,
        'cooler_ligado': estufa.cooler_ligado,
        'temp_alvo_sec': estufa.temp_alvo_sec,
        'temp_max_sec': estufa.temp_max_sec,
        'histerese_sec': estufa.histerese_sec,
        'temp_max_arm': estufa.temp_max_arm,
        'temp_min_arm': estufa.temp_min_arm,
        'ultimo_contato': (
            timezone.localtime(estufa.ultimo_contato).strftime('%d/%m/%Y %H:%M:%S')
            if estufa.ultimo_contato else None
        ),
    })
