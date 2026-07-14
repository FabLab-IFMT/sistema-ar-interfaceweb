"""
Serviço do módulo de IA: coleta dados operacionais de todos os apps do SGL
e gera insights em linguagem natural via API da OpenAI.
"""
import logging

import requests
from django.conf import settings
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .models import InsightIA

logger = logging.getLogger(__name__)

OPENAI_CHAT_URL = 'https://api.openai.com/v1/chat/completions'

DIAS_SEMANA = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']


class IAError(Exception):
    """Erro na geração de insights (configuração ou comunicação com a API)."""


def _safe(coletor):
    """Executa um coletor de dados sem deixar uma falha derrubar a geração."""
    try:
        return coletor()
    except Exception as e:
        logger.warning('Coletor de dados da IA falhou: %s', e)
        return None


def _dados_usuarios():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return {
        'total': User.objects.count(),
        'ativos': User.objects.filter(is_active=True).count(),
        'staff': User.objects.filter(is_staff=True).count(),
    }


def _dados_agenda():
    from logs.models import Event
    agora = timezone.now()
    proximos = Event.objects.filter(
        start_time__gte=agora,
        start_time__lte=agora + timedelta(days=30),
    ).order_by('start_time')
    pendentes = Event.objects.filter(approved=False, start_time__gte=agora)

    # Distribuição por dia da semana (últimos 90 dias) para achar picos de demanda
    historico = Event.objects.filter(start_time__gte=agora - timedelta(days=90))
    por_dia = {}
    for ev in historico:
        dia = DIAS_SEMANA[ev.start_time.weekday()]
        por_dia[dia] = por_dia.get(dia, 0) + 1

    return {
        'eventos_proximos_30_dias': [
            {
                'titulo': ev.title,
                'tipo': ev.get_event_type_display(),
                'inicio': ev.start_time.strftime('%d/%m/%Y %H:%M'),
                'aprovado': ev.approved,
            }
            for ev in proximos[:20]
        ],
        'solicitacoes_pendentes_aprovacao': pendentes.count(),
        'eventos_por_dia_da_semana_ultimos_90_dias': por_dia,
    }


def _dados_inventario():
    from inventario.models import Item, Emprestimo
    agora = timezone.now()
    itens = Item.objects.all()
    estoque_baixo = [i for i in itens if i.estoque_baixo][:15]
    emprestimos_abertos = Emprestimo.objects.filter(data_devolucao__isnull=True)
    atrasados = emprestimos_abertos.filter(data_prevista_devolucao__lt=agora)
    return {
        'total_itens': itens.count(),
        'itens_estoque_baixo': [
            {
                'nome': i.nome,
                'quantidade': float(i.quantidade),
                'minimo': float(i.quantidade_minima),
                'unidade': i.unidade,
            }
            for i in estoque_baixo
        ],
        'emprestimos_ativos': emprestimos_abertos.count(),
        'emprestimos_atrasados': atrasados.count(),
    }


def _dados_projetos():
    from projetos.models import Projeto
    hoje = timezone.now().date()
    em_andamento = Projeto.objects.filter(status='em_andamento').prefetch_related('marcos')
    projetos = []
    for p in em_andamento[:20]:
        marcos = list(p.marcos.all())
        atrasados = [
            m for m in marcos
            if m.data <= hoje + timedelta(days=14) and m.progresso < 100
        ]
        progresso_medio = (
            round(sum(m.progresso for m in marcos) / len(marcos)) if marcos else None
        )
        projetos.append({
            'titulo': p.titulo,
            'dias_desde_inicio': (hoje - p.data_inicio).days,
            'progresso_medio_marcos': progresso_medio,
            'marcos_proximos_ou_vencidos_incompletos': len(atrasados),
        })
    return {
        'em_andamento': em_andamento.count(),
        'detalhes': projetos,
    }


def _dados_fluxo():
    from acesso_e_ponto.models import Session
    agora = timezone.now()
    sessoes = Session.objects.filter(entry_time__gte=agora - timedelta(days=30))
    por_dia = {}
    for s in sessoes:
        dia = DIAS_SEMANA[s.entry_time.weekday()]
        por_dia[dia] = por_dia.get(dia, 0) + 1
    return {
        'sessoes_ultimos_30_dias': sessoes.count(),
        'sessoes_por_dia_da_semana': por_dia,
        'pessoas_no_lab_agora': Session.objects.filter(is_active=True).count(),
    }


def _dados_climatizacao():
    from Controle_ar.models import Ar_condicionado, LogOperacao
    agora = timezone.now()
    return {
        'aparelhos': [
            {'nome': ar.nome, 'ligado': ar.estado, 'online': ar.online}
            for ar in Ar_condicionado.objects.all()
        ],
        'operacoes_ultimos_30_dias': LogOperacao.objects.filter(
            data_hora__gte=agora - timedelta(days=30)
        ).count(),
    }


def coletar_dados_sistema():
    """Snapshot dos dados operacionais de todos os módulos do SGL."""
    return {
        'data_referencia': timezone.now().strftime('%d/%m/%Y %H:%M'),
        'usuarios': _safe(_dados_usuarios),
        'agenda': _safe(_dados_agenda),
        'inventario': _safe(_dados_inventario),
        'projetos': _safe(_dados_projetos),
        'fluxo_de_pessoas': _safe(_dados_fluxo),
        'climatizacao': _safe(_dados_climatizacao),
    }


FOCO_INSTRUCOES = {
    InsightIA.Foco.GERAL: (
        'Faça uma análise geral da operação do laboratório: demanda, estoque, '
        'projetos e fluxo de pessoas. Destaque os 3 pontos que mais precisam de atenção.'
    ),
    InsightIA.Foco.AGENDA: (
        'Analise a agenda: identifique períodos de maior demanda, solicitações '
        'pendentes e sugira otimizações na distribuição de eventos e visitas.'
    ),
    InsightIA.Foco.ESTOQUE: (
        'Analise o inventário: alerte sobre estoque crítico, empréstimos atrasados '
        'e sugira prioridades de reposição.'
    ),
    InsightIA.Foco.PROJETOS: (
        'Analise os projetos em andamento: identifique projetos em risco de atraso '
        'com base no progresso dos marcos e na proximidade dos prazos.'
    ),
    InsightIA.Foco.MANUTENCAO: (
        'Com base no fluxo de pessoas e na agenda, sugira as melhores janelas para '
        'manutenção e limpeza dos equipamentos (períodos de baixo movimento).'
    ),
}

SYSTEM_PROMPT = (
    'Você é o assistente de gestão do IFMT Maker Fablab, um laboratório maker '
    'educacional. Você recebe um snapshot em JSON dos dados operacionais do '
    'Sistema de Gerenciamento de Laboratórios (SGL) e gera insights práticos '
    'para os gestores. Responda em português do Brasil, em texto simples '
    '(sem markdown), organizado em tópicos curtos iniciados por "•". '
    'Seja específico: cite nomes de itens, projetos e dias da semana presentes '
    'nos dados. Se algum dado estiver ausente ou vazio, não invente valores. '
    'Termine com uma seção "Ações recomendadas:" com no máximo 3 ações objetivas.'
)


def gerar_insight(usuario=None, foco=InsightIA.Foco.GERAL):
    """Coleta os dados do sistema, consulta a OpenAI e persiste o insight."""
    import json

    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        raise IAError(
            'OPENAI_API_KEY não configurada. Adicione a chave no arquivo .env.'
        )

    if foco not in InsightIA.Foco.values:
        foco = InsightIA.Foco.GERAL

    dados = coletar_dados_sistema()
    instrucao = FOCO_INSTRUCOES[foco]

    payload = {
        'model': getattr(settings, 'OPENAI_MODEL', 'gpt-4o'),
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {
                'role': 'user',
                'content': (
                    f'{instrucao}\n\nDados operacionais do SGL:\n'
                    f'{json.dumps(dados, ensure_ascii=False, indent=2)}'
                ),
            },
        ],
        'temperature': 0.4,
        'max_tokens': 900,
    }

    try:
        resposta = requests.post(
            OPENAI_CHAT_URL,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=60,
        )
    except requests.RequestException as e:
        raise IAError(f'Falha de comunicação com a API da OpenAI: {e}') from e

    if resposta.status_code == 401:
        raise IAError('Chave da OpenAI inválida ou expirada (HTTP 401).')
    if resposta.status_code == 429:
        raise IAError('Limite de requisições da OpenAI atingido (HTTP 429). Tente novamente em instantes.')
    if not resposta.ok:
        raise IAError(f'Erro da API da OpenAI (HTTP {resposta.status_code}): {resposta.text[:300]}')

    corpo = resposta.json()
    try:
        conteudo = corpo['choices'][0]['message']['content'].strip()
    except (KeyError, IndexError) as e:
        raise IAError(f'Resposta inesperada da API da OpenAI: {corpo}') from e

    tokens = corpo.get('usage', {}).get('total_tokens', 0)
    rotulo = dict(InsightIA.Foco.choices)[foco]

    return InsightIA.objects.create(
        foco=foco,
        titulo=f'Insight — {rotulo}',
        conteudo=conteudo,
        dados_contexto=dados,
        modelo_usado=corpo.get('model', payload['model']),
        tokens_usados=tokens,
        gerado_por=usuario if (usuario and usuario.is_authenticated) else None,
    )
