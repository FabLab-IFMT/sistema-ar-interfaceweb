import os
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings
import json
from django.utils import timezone

def get_google_calendar_events(start_date, end_date):
    """
    Obtém eventos do Google Calendar para o período especificado.
    Retorna uma lista vazia se as credenciais não estiverem disponíveis ou se ocorrer um erro.
    """
    try:
        # Caminho para o arquivo de credenciais na pasta env/
        credentials_path = os.path.join(settings.BASE_DIR.parent, 'env', 'google_credentials.json')
        
        if not os.path.exists(credentials_path):
            print("Aviso: Arquivo google_credentials.json não encontrado.")
            return []
        
        # Validação para garantir que são credenciais de Conta de Serviço
        with open(credentials_path, 'r') as f:
            try:
                credentials_info = json.load(f)
                if 'client_email' not in credentials_info or 'private_key' not in credentials_info:
                    print("Erro: O arquivo google_credentials.json parece ser de um 'Aplicativo Web'. É necessário usar credenciais de uma 'Conta de Serviço'.")
                    return []
            except json.JSONDecodeError:
                print("Erro: O arquivo google_credentials.json não é um JSON válido.")
                return []

        # Escopo de permissão para ler eventos
        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        
        # Autenticação
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES)
        
        # Construção do serviço da API
        service = build('calendar', 'v3', credentials=credentials)
        
        # --- LÓGICA DE DATA/HORA CORRIGIDA ---
        if timezone.is_naive(start_date):
            start_date = timezone.make_aware(start_date)
        if timezone.is_naive(end_date):
            end_date = timezone.make_aware(end_date)
            
        start_datetime_utc = start_date.astimezone(timezone.utc)
        end_datetime_utc = end_date.astimezone(timezone.utc)

        start_datetime_formatted = start_datetime_utc.replace(microsecond=0).isoformat()
        end_datetime_formatted = end_datetime_utc.replace(microsecond=0).isoformat()
        
        # ID do calendário que você compartilhou com a Conta de Serviço
        calendar_id = '406319dcdb0cef978956cae2b9f7c8796b9860b9a359262d96219c536a4a7064@group.calendar.google.com'
        
        # Chamada à API para buscar eventos
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_datetime_formatted,
            timeMax=end_datetime_formatted,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
        
    except Exception as e:
        print(f"Erro ao acessar Google Calendar API: {e}")
        return []
