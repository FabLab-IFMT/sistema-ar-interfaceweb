from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from gestao.views import is_gestao_authorized

from .models import InsightIA
from .services import IAError, gerar_insight


@login_required
@user_passes_test(is_gestao_authorized)
def painel_insights(request):
    """Painel de insights de IA: histórico + geração de novos insights."""
    insights = InsightIA.objects.select_related('gerado_por')
    paginator = Paginator(insights, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'titulo': 'Insights de IA',
        'page_obj': page_obj,
        'focos': InsightIA.Foco.choices,
        'ultimo_insight': insights.first(),
    }
    return render(request, 'ia/insights.html', context)


@login_required
@user_passes_test(is_gestao_authorized)
@require_POST
def gerar(request):
    """Gera um novo insight com o foco escolhido."""
    foco = request.POST.get('foco', InsightIA.Foco.GERAL)
    try:
        insight = gerar_insight(usuario=request.user, foco=foco)
        messages.success(request, 'Insight gerado com sucesso!')
        return redirect('ia:detalhe', insight_id=insight.pk)
    except IAError as e:
        messages.error(request, str(e))
    return redirect('ia:painel')


@login_required
@user_passes_test(is_gestao_authorized)
def detalhe(request, insight_id):
    """Exibe um insight completo, com os dados de contexto usados."""
    insight = get_object_or_404(InsightIA, pk=insight_id)
    return render(request, 'ia/insight_detail.html', {
        'titulo': insight.titulo,
        'insight': insight,
    })


@login_required
@user_passes_test(is_gestao_authorized)
@require_POST
def excluir(request, insight_id):
    """Remove um insight do histórico."""
    insight = get_object_or_404(InsightIA, pk=insight_id)
    insight.delete()
    messages.success(request, 'Insight excluído.')
    return redirect('ia:painel')
