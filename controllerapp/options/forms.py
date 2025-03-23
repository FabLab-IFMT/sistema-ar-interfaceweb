from django import forms
from .models import SolicitacaoInteresse

class SolicitacaoInteresseForm(forms.ModelForm):
    class Meta:
        model = SolicitacaoInteresse
        fields = ['nome', 'email', 'telefone', 'servico', 'descricao_projeto', 'arquivo_referencia']
        widgets = {
            'descricao_projeto': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Descreva seu projeto ou interesse nesta capacidade do laboratório'}),
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu nome completo'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Seu email para contato'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefone (opcional)'}),
            'servico': forms.HiddenInput(),
            'arquivo_referencia': forms.FileInput(attrs={'class': 'form-control'})
        }
