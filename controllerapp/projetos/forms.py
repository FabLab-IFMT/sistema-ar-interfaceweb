from django import forms
from .models import Projeto, ComentarioProjeto

class ProjetoForm(forms.ModelForm):
    class Meta:
        model = Projeto
        fields = [
            'titulo', 'descricao_curta', 'descricao', 'imagem', 
            'data_inicio', 'data_conclusao', 'status', 
            'responsavel', 'participantes', 'tags',
            'link_github', 'link_video', 'link_documentacao',
            'mostrar_na_home', 'publicado', 'destaque'
        ]
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_conclusao': forms.DateInput(attrs={'type': 'date'}),
            'descricao': forms.Textarea(attrs={'rows': 6}),
        }

class ComentarioProjetoForm(forms.ModelForm):
    class Meta:
        model = ComentarioProjeto
        fields = ['texto']
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Escreva seu comentário aqui...'}),
        }