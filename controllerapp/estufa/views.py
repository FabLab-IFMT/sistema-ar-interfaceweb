import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Estufa, LeituraEstufa, LogOperacaoEstufa


def _float_ou_none(valor):
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return None
    # DHT22 com falha manda NaN — não persistimos
    return v if v == v else None


@csrf_exempt
def api_telemetria(request):
    """Endpoint chamado pelo ESP32 da estufa.

    Recebe POST JSON com as leituras e o estado atual, e responde com o
    modo desejado pelo servidor. Se o payload trouxer origem_botao=true,
    o modo reportado pelo dispositivo vira o modo desejado (o botão
    físico tem prioridade sobre a interface web).
    """
    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido'}, status=405)

    token = request.headers.get('X-Estufa-Token', '')
    if not token:
        return JsonResponse({'erro': 'Token ausente'}, status=401)

    try:
        estufa = Estufa.objects.get(token=token)
    except Estufa.DoesNotExist:
        return JsonResponse({'erro': 'Token inválido'}, status=403)

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

    return JsonResponse({
        'ok': True,
        'modo_desejado': estufa.modo_desejado,
    })


@login_required
def dashboard(request):
    estufas = Estufa.objects.all()
    return render(request, 'estufa/dashboard.html', {'estufas': estufas})


@login_required
def detalhe(request, estufa_id):
    estufa = get_object_or_404(Estufa, pk=estufa_id)
    leituras = estufa.leituras.all()[:60]
    logs = estufa.logs.all()[:20]
    return render(request, 'estufa/detalhe.html', {
        'estufa': estufa,
        'leituras': leituras,
        'logs': logs,
    })


@login_required
@require_POST
def definir_modo(request, estufa_id):
    estufa = get_object_or_404(Estufa, pk=estufa_id)
    modo = request.POST.get('modo', '')
    if modo not in (Estufa.MODO_SECAGEM, Estufa.MODO_ARMAZEM):
        return JsonResponse({'erro': 'Modo inválido'}, status=400)

    if modo != estufa.modo_desejado:
        estufa.modo_desejado = modo
        estufa.save(update_fields=['modo_desejado'])
        LogOperacaoEstufa.objects.create(
            estufa=estufa,
            operacao=f'Modo alterado para {modo} pela interface web',
            usuario=str(request.user),
        )

    return JsonResponse({'ok': True, 'modo_desejado': estufa.modo_desejado})


@login_required
def status_ajax(request, estufa_id):
    """Consumido pela página de detalhe para atualizar o painel sem reload."""
    estufa = get_object_or_404(Estufa, pk=estufa_id)
    return JsonResponse({
        'online': estufa.online,
        'modo_atual': estufa.modo_atual,
        'modo_desejado': estufa.modo_desejado,
        'estado': estufa.estado,
        'estado_display': estufa.get_estado_display(),
        'temperatura_media': estufa.temperatura_media,
        'umidade_media': estufa.umidade_media,
        'lampada_ligada': estufa.lampada_ligada,
        'cooler_ligado': estufa.cooler_ligado,
        'ultimo_contato': (
            timezone.localtime(estufa.ultimo_contato).strftime('%d/%m/%Y %H:%M:%S')
            if estufa.ultimo_contato else None
        ),
    })
