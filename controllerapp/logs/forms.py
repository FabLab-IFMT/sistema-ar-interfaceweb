from django import forms
from .models import Event
from django.utils.translation import gettext_lazy as _

class DateInput(forms.DateInput):
    input_type = 'date'

class TimeInput(forms.TimeInput):
    input_type = 'time'

class DateTimeInput(forms.DateTimeInput):
    input_type = 'datetime-local'

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'start_time', 'end_time', 'event_type']
        widgets = {
            'start_time': DateTimeInput(),
            'end_time': DateTimeInput(),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError(
                    _("O horário de término deve ser após o horário de início.")
                )
                
        # Verificar conflitos com outros eventos
        if start_time and end_time and not self.instance.pk:  # Se não for edição
            conflicts = Event.objects.filter(
                approved=True,
                start_time__lt=end_time,
                end_time__gt=start_time,
            ).exists()
            
            if conflicts:
                raise forms.ValidationError(
                    _("Já existe um evento aprovado para este horário. Por favor, escolha outro horário.")
                )
                
        return cleaned_data

class VisitRequestForm(EventForm):
    visitor_name = forms.CharField(max_length=200, label=_("Seu Nome"))
    visitor_email = forms.EmailField(label=_("Seu Email"))
    visitor_phone = forms.CharField(max_length=15, label=_("Seu Telefone"))
    number_of_visitors = forms.IntegerField(
        min_value=1, 
        max_value=30, 
        initial=1,
        label=_("Número de Visitantes")
    )
    
    class Meta(EventForm.Meta):
        fields = ['title', 'description', 'start_time', 'end_time', 
                 'event_type', 'visitor_name', 'visitor_email', 'visitor_phone', 'number_of_visitors']
        widgets = EventForm.Meta.widgets.copy()
        widgets['event_type'] = forms.HiddenInput()
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].initial = "Solicitação de Visita"
        self.fields['event_type'].initial = Event.EventType.VISIT
        self.fields['event_type'].disabled = True  # Impede a alteração do tipo
