from django import forms
from .models import GrupoProjetos
from projetos.models import Projeto
from django.contrib.auth import get_user_model

User = get_user_model()

class GrupoProjetosForm(forms.ModelForm):
    """Formulário para criação e edição de grupos de projetos"""
    
    class Meta:
        model = GrupoProjetos
        fields = ['nome', 'descricao', 'projetos', 'membros']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'projetos': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
            'membros': forms.SelectMultiple(attrs={'class': 'form-control select2'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['projetos'].queryset = Projeto.objects.all().order_by('titulo')
        self.fields['membros'].queryset = User.objects.all().order_by('username')