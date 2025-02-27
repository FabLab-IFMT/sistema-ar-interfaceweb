#!/usr/bin/env python3
import os
import sys
import django

# Adicionar o diretório do projeto ao path
sys.path.append('/home/henrique/Área de Trabalho/Programação em geral/Sistema de gestão do laboratório/5/sistema-ar-interfaceweb')

# Configurar as configurações do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controllerapp.settings')
django.setup()

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from Controle_ar.models import Ar_condicionado

def check_fields():
    """Verifica se todos os campos necessários existem no modelo."""
    print("Verificando campos do modelo Ar_condicionado...")
    
    # Lista de campos esperados
    expected_fields = [
        'id', 'nome', 'tag', 'estado', 'temperatura', 'modo', 'velocidade', 
        'swing', 'ultima_alteracao', 'online', 'ultimo_ping', 'consumo_atual', 
        'temperatura_ambiente'
    ]
    
    # Verificar campos existentes
    model_fields = [field.name for field in Ar_condicionado._meta.get_fields()]
    
    # Mostrar campos existentes
    print("Campos existentes:", model_fields)
    
    # Verificar campos faltantes
    missing_fields = [field for field in expected_fields if field not in model_fields]
    
    if missing_fields:
        print("Campos faltantes:", missing_fields)
        print("É necessário criar e executar migrações para adicionar esses campos.")
    else:
        print("Todos os campos necessários existem no modelo.")

def run_migrations():
    """Executa migrações pendentes para o app Controle_ar."""
    # Verificar se existem migrações pendentes
    executor = MigrationExecutor(connection)
    plan = executor.migration_plan([("Controle_ar", None)])
    
    if plan:
        print("Executando migrações pendentes para o app Controle_ar...")
        executor.migrate([("Controle_ar", None)])
        print("Migrações concluídas!")
    else:
        print("Não há migrações pendentes para o app Controle_ar.")

if __name__ == "__main__":
    check_fields()
    run_migrations()
    
    # Verificar instâncias existentes
    print("\nVerificando instâncias existentes:")
    ares = Ar_condicionado.objects.all()
    print(f"Total de ar-condicionados: {ares.count()}")
    
    for ar in ares:
        print(f"- {ar.nome}: Status={ar.online}, Consumo={ar.consumo_atual}")
        
    print("\nScript concluído com sucesso!")
