from django import forms
from .models import Item, Categoria, Emprestimo
from django.utils import timezone
from datetime import timedelta

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            'codigo', 'nome', 'descricao', 'categoria', 'quantidade', 
            'quantidade_minima', 'unidade', 'valor_unitario', 'localizacao',
            'imagem', 'observacoes'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'descricao']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }

class EmprestimoForm(forms.ModelForm):
    data_prevista_devolucao = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        initial=timezone.now() + timedelta(days=7)
    )
    
    class Meta:
        model = Emprestimo
        fields = ['item', 'usuario', 'quantidade', 'data_prevista_devolucao', 'observacao']
        widgets = {
            'observacao': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get('item')
        quantidade = cleaned_data.get('quantidade')
        
        if item and quantidade:
            if quantidade > item.quantidade:
                self.add_error('quantidade', 'Quantidade solicitada maior que disponível em estoque.')
            
            if not item.disponivel_para_emprestimo:
                self.add_error('item', 'Este item já está emprestado ou não tem unidades disponíveis.')
                
        return cleaned_data

class DevolucaoEmprestimoForm(forms.Form):
    observacao = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Observação sobre a devolução"
    )
