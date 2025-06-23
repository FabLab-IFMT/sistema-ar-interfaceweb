# Sistema de Gestão do FabLab IFMT

Sistema web integrado para gestão do Laboratório de Fabricação Digital (FabLab) do IFMT. Esta plataforma combina funcionalidades administrativas, agendamento de recursos, controle de inventário, automação de dispositivos e comunicação com usuários.

## 🚀 Recursos principais

- **Agendamento de visitas e equipamentos**: Permite que usuários agendem visitas e reservem equipamentos do laboratório
- **Inventário digital**: Controle completo dos equipamentos, materiais e insumos do laboratório
- **Automação de dispositivos**: Interface de controle de equipamentos como ar-condicionados e projetores
- **Gestão de notícias**: Publicação e gerenciamento de notícias e conteúdos
- **Perfis de usuários**: Diferentes níveis de acesso para administradores e visitantes
- **Integração com e-mail**: Sistema de notificações automáticas

## 📋 Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Git

## 🔧 Instalação

1. Clone este repositório:
```bash
git clone https://github.com/FabLab-IFMT/sistema-ar-interfaceweb.git
cd controllerapp
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure o banco de dados:
```bash
python manage.py migrate
```

5. Crie um superusuário:
```bash
python manage.py createsuperuser
```

6. Execute o servidor de desenvolvimento:
```bash
python manage.py runserver
```

7. Acesse o sistema em: http://localhost:8000

## 🏗️ Estrutura do projeto

O sistema está dividido em vários aplicativos Django:

- **users**: Gerenciamento de usuários e autenticação
- **logs**: Registros de atividades e agendamentos
- **Controle_ar**: Aplicativo para controle de dispositivos (ar-condicionado, etc.)
- **options**: Gerenciamento de opções do sistema (equipamentos, serviços, notícias)
- **acesso_e_ponto**: Controle de acesso ao laboratório
- **Email_notificacoes**: Sistema de notificações por e-mail
- **inventario**: Gestão do inventário do laboratório

## 👨‍👩‍👧‍👦 Tipos de Usuários

O sistema possui diferentes níveis de acesso:

- **Visitante**: Pode visualizar informações públicas e solicitar agendamentos
- **Usuário registrado**: Pode agendar equipamentos e serviços
- **Administrador**: Acesso completo ao sistema, incluindo aprovação de solicitações e gestão de conteúdo

## 📱 Principais funcionalidades para usuários

1. **Página inicial**: Visão geral do laboratório com notícias e eventos
2. **Equipamentos**: Lista de equipamentos disponíveis no FabLab
3. **Serviços**: Serviços oferecidos pelo laboratório
4. **Agenda**: Calendário de eventos e disponibilidade de equipamentos
5. **Solicitar visita**: Formulário para agendamento de visitas

## 👨‍💻 Principais funcionalidades para administradores

1. **Aprovação de solicitações**: Gerenciar pedidos de agendamentos
2. **Automação**: Controle dos dispositivos do laboratório
3. **Inventário**: Gerenciamento de estoque e equipamentos
4. **Gerenciamento de conteúdo**: Publicação de notícias e eventos

## 🛠️ Configuração do ambiente de produção

Para ambiente de produção, é necessário configurar:

1. Desativar o modo DEBUG no arquivo settings.py
2. Configurar um servidor web como Nginx ou Apache
3. Utilizar Gunicorn ou uWSGI como servidor WSGI
4. Configurar um banco de dados de produção (PostgreSQL recomendado)
5. Definir chaves secretas seguras
6. Configurar backup regular do banco de dados

## 🔧 Solução de problemas comuns

- **Erro de conexão com banco de dados**: Verifique se as credenciais estão corretas em settings.py
- **Arquivos estáticos não aparecem**: Execute `python manage.py collectstatic`
- **Problemas com envio de e-mail**: Verifique as configurações SMTP em settings.py
- Qualquer outro erro notifique a equipe de desenvolvimento para ajuda

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## ✒️ Autores

* **Henrique** - *Desenvolvimento* - [henrltop](https://github.com/henrltop)
* **Equipe FabLab IFMT** - *Colaboradores*

## 🎁 Agradecimentos

* Henrique boladão e equipe muito massa do ensino médio 




.