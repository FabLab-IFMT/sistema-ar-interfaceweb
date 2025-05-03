from django import forms
from .models import Resource, ResourceComment, ResourceFile
from django.core.exceptions import ValidationError
import os

class ResourceForm(forms.ModelForm):
    """Formulário para criar/editar recursos"""
    
    # Observe que não há mais um campo files aqui
    
    class Meta:
        model = Resource
        fields = ['title', 'description', 'resource_type', 'category', 'visibility', 'featured', 'tags', 'text_content', 'external_url']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'text_content': forms.Textarea(attrs={'rows': 10, 'class': 'code-editor'}),
            'tags': forms.TextInput(attrs={'placeholder': 'Tags separadas por vírgula'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Aplicar classes Bootstrap
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        self.fields['featured'].widget.attrs.update({'class': 'form-check-input'})
        
    def clean(self):
        cleaned_data = super().clean()
        resource_type = cleaned_data.get('resource_type')
        text_content = cleaned_data.get('text_content')
        external_url = cleaned_data.get('external_url')
        
        # Verificações específicas são agora baseadas apenas no tipo de recurso
        # e não mais na presença de arquivos, pois os arquivos são processados separadamente
        
        if resource_type == 'text' and not text_content:
            self.add_error('text_content', "Conteúdo de texto é necessário para recursos do tipo Texto.")
            
        if resource_type == 'link' and not external_url:
            self.add_error('external_url', "Uma URL externa é necessária para recursos do tipo Link.")
            
        return cleaned_data
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.project:
            instance.project = self.project
            
        if self.user and not instance.created_by:
            instance.created_by = self.user
            
        if commit:
            instance.save()
            self.save_m2m()
            
        return instance

class ResourceCommentForm(forms.ModelForm):
    """Formulário para comentários em recursos"""
    
    class Meta:
        model = ResourceComment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Deixe seu comentário...'})
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs.update({'class': 'form-control'})
