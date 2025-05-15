from django import forms
from django.utils import timezone
from .models import Event
import datetime
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
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'event_type': forms.Select(attrs={'class': 'form-control'})
        }
        labels = {
            'title': 'Título do Evento',
            'description': 'Descrição',
            'start_time': 'Data e Hora de Início',
            'end_time': 'Data e Hora de Término',
            'event_type': 'Tipo de Evento'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define valores iniciais de data/hora
        if not self.instance.pk:  # Se for um novo evento
            now = timezone.now()
            rounded_now = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
            self.fields['start_time'].initial = rounded_now
            self.fields['end_time'].initial = rounded_now + datetime.timedelta(hours=1)

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Validar se a hora de término é posterior à hora de início
        if start_time and end_time and end_time <= start_time:
            self.add_error('end_time', 'A hora de término deve ser posterior à hora de início.')
            
        # Validar se a data não é passada
        if start_time and start_time < timezone.now():
            self.add_error('start_time', 'Não é possível agendar eventos em datas passadas.')
            
        return cleaned_data

class VisitRequestForm(forms.ModelForm):
    # Campos adicionais para informações do visitante
    visitor_name = forms.CharField(label='Seu Nome', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    visitor_email = forms.EmailField(label='Seu Email', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    visitor_phone = forms.CharField(label='Seu Telefone', max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    number_of_visitors = forms.IntegerField(label='Número de Visitantes', min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    
    # Novos campos para data e horários separados
    visit_date = forms.DateField(
        label='Data da Visita',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    start_hour = forms.TimeField(
        label='Horário de Entrada',
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    end_hour = forms.TimeField(
        label='Horário de Saída',
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    class Meta:
        model = Event
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'title': 'Motivo da Visita',
            'description': 'Detalhes Adicionais'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Valores iniciais para data e hora
        now = timezone.now()
        rounded_now = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now.hour >= 9:
            rounded_now = rounded_now + datetime.timedelta(days=1)
            
        self.fields['visit_date'].initial = rounded_now.date()
        self.fields['start_hour'].initial = "09:00"
        self.fields['end_hour'].initial = "11:00"

    def clean(self):
        cleaned_data = super().clean()
        visit_date = cleaned_data.get('visit_date')
        start_hour = cleaned_data.get('start_hour')
        end_hour = cleaned_data.get('end_hour')
        
        if visit_date and start_hour and end_hour:
            # Conversão para datetime para validação
            start_datetime = timezone.make_aware(
                datetime.datetime.combine(visit_date, start_hour)
            )
            end_datetime = timezone.make_aware(
                datetime.datetime.combine(visit_date, end_hour)
            )
            
            # Verificar se o horário de saída é depois do horário de entrada
            if end_hour <= start_hour:
                self.add_error('end_hour', 'O horário de saída deve ser posterior ao horário de entrada')
            
            # Verificar se a data não é passada
            if start_datetime < timezone.now():
                self.add_error('visit_date', 'Não é possível agendar visitas para datas/horários passados')
                
            # Armazenar os valores datetime para uso em save_event
            self.start_datetime = start_datetime
            self.end_datetime = end_datetime
                
        return cleaned_data

class EventRejectForm(forms.Form):
    """
    Formulário para coletar o motivo da recusa de uma solicitação de evento/visita.
    """
    MOTIVOS_COMUNS = [
        ('', '-- Selecione um motivo comum ou digite outro abaixo --'),
        ('data_indisponivel', 'A data/horário solicitado já está reservada para outro evento'),
        ('fora_horario', 'A solicitação está fora do horário de funcionamento do laboratório'),
        ('lotacao_maxima', 'O número de visitantes excede nossa capacidade máxima'),
        ('manutencao', 'O laboratório estará em manutenção na data solicitada'),
        ('falta_detalhes', 'A solicitação não contém detalhes suficientes para avaliação'),
        ('outro', 'Outro motivo (especifique abaixo)')
    ]
    
    motivo_comum = forms.ChoiceField(
        choices=MOTIVOS_COMUNS,
        required=False,
        label='Motivos Comuns',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_motivo_comum'}),
        help_text='Selecione um motivo comum ou escreva um personalizado abaixo'
    )
    
    motivo = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'id': 'id_motivo_detalhado'}),
        label='Detalhamento do Motivo',
        help_text='Esta informação será enviada por email ao solicitante. Seja claro e cordial.'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        motivo = cleaned_data.get('motivo')
        
        # Validar se o motivo foi preenchido
        if not motivo or motivo.strip() == '':
            self.add_error('motivo', 'Por favor, forneça um motivo para a recusa da solicitação.')
            
        return cleaned_data
