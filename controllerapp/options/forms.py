from django import forms
from .models import SolicitacaoOrcamento

class SolicitacaoOrcamentoForm(forms.ModelForm):
    class Meta:
        model = SolicitacaoOrcamento
        fields = ['nome', 'email', 'telefone', 'servico', 'descricao_projeto', 'arquivo_referencia']
        widgets = {
            'descricao_projeto': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'servico': forms.HiddenInput(),
            'arquivo_referencia': forms.FileInput(attrs={'class': 'form-control'})
        }
