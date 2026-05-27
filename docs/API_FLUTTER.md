# 📱 FabLab IFMT — API Reference para o App Flutter

> **Base URL:** `http://<servidor>/api/`
> **Autenticação:** JWT (Bearer Token) via SimpleJWT
> **Formato:** JSON
> **Paginação:** 20 itens por página (`?page=2` para avançar)

---

## Índice

1. [Autenticação](#1-autenticação)
2. [Perfil do Usuário Autenticado](#2-perfil-do-usuário-autenticado)
3. [Usuários e Cargos](#3-usuários-e-cargos)
4. [Notícias](#4-notícias)
5. [Equipamentos (Materiais)](#5-equipamentos-materiais)
6. [Serviços](#6-serviços)
7. [Membros da Equipe](#7-membros-da-equipe)
8. [Projetos](#8-projetos)
9. [Tarefas (To-Do)](#9-tarefas-to-do)
10. [Agenda / Eventos](#10-agenda--eventos)
11. [Horário de Funcionamento do Lab](#11-horário-de-funcionamento-do-lab)
12. [Inventário](#12-inventário)
13. [Empréstimos de Itens](#13-empréstimos-de-itens)
14. [Controle de Acesso e Ponto](#14-controle-de-acesso-e-ponto)
15. [Ar-Condicionado (IoT)](#15-ar-condicionado-iot)
16. [Kanban](#16-kanban)
17. [Repositório de Recursos](#17-repositório-de-recursos)
18. [Solicitações de Serviço](#18-solicitações-de-serviço)
19. [Dashboard Administrativo](#19-dashboard-administrativo)
20. [Níveis de Permissão](#20-níveis-de-permissão)
21. [Guia Rápido Flutter / Dart](#21-guia-rápido-flutter--dart)

---

## 1. Autenticação

A API usa **JWT (JSON Web Token)**. Toda requisição autenticada deve enviar o header:

```
Authorization: Bearer <access_token>
```

### Obter tokens

```
POST /api/token/
```

**Body:**
```json
{
  "username": "2024001234567",
  "password": "senha123"
}
```
> ⚠️ O campo `username` é a **matrícula** do usuário (o sistema usa matrícula como identificador, não e-mail).

**Resposta:**
```json
{
  "access":  "<jwt_access_token>",   // validade: 60 min (padrão)
  "refresh": "<jwt_refresh_token>"   // validade: 7 dias (padrão)
}
```

---

### Renovar o access token

```
POST /api/token/refresh/
```

**Body:**
```json
{
  "refresh": "<jwt_refresh_token>"
}
```

**Resposta:**
```json
{
  "access": "<novo_access_token>"
}
```

> 💡 **Estratégia recomendada no Flutter:** salve o `refresh` em `flutter_secure_storage`, monitore o `access` e renove-o automaticamente quando receber HTTP 401.

---

## 2. Perfil do Usuário Autenticado

Endpoint especial para ler e atualizar o próprio perfil sem precisar do ID.

| Método | Endpoint   | Descrição                        | Permissão     |
|--------|-----------|----------------------------------|---------------|
| GET    | `/api/me/` | Retorna perfil do usuário logado | Autenticado   |
| PATCH  | `/api/me/` | Atualiza campos do próprio perfil | Autenticado  |

**Resposta GET:**
```json
{
  "id": "2024001234567",
  "first_name": "João",
  "last_name": "Silva",
  "email": "joao@ifmt.edu.br",
  "profile_image": "/media/users/profile/foto.webp",
  "is_staff": false,
  "is_superuser": false,
  "email_verified": true,
  "roles": [
    { "code": "projetista", "name": "Projetista", "description": "..." }
  ],
  "role_codes": ["projetista"],
  "date_joined": "2024-03-01T10:00:00Z"
}
```

**Campos editáveis via PATCH:**
```json
{
  "first_name": "João",
  "last_name": "Silva",
  "email": "novo@ifmt.edu.br"
}
```

---

## 3. Usuários e Cargos

### Usuários

| Método | Endpoint                | Descrição                              | Permissão           |
|--------|------------------------|----------------------------------------|---------------------|
| GET    | `/api/users/`           | Lista usuários (staff vê todos)        | Autenticado         |
| GET    | `/api/users/<id>/`      | Detalhe de um usuário                  | Autenticado         |
| PATCH  | `/api/users/<id>/`      | Atualiza usuário                       | Autenticado (próprio) |

**Filtros disponíveis:**
- `?search=joao` — busca por nome ou email

**Campos retornados:** `id` (matrícula), `first_name`, `last_name`, `email`, `full_name`, `profile_image`, `is_staff`, `is_superuser`, `is_active`, `roles`, `date_joined`

---

### Cargos (Roles)

| Método | Endpoint               | Descrição          | Permissão    |
|--------|------------------------|--------------------|--------------|
| GET    | `/api/roles/`           | Lista todos cargos | Admin        |
| GET    | `/api/roles/<id>/`      | Detalhe de um cargo | Admin       |

---

### Solicitações de Registro

| Método | Endpoint                                              | Descrição                   | Permissão |
|--------|------------------------------------------------------|-----------------------------|-----------|
| GET    | `/api/registration-requests/`                         | Lista solicitações           | Admin     |
| POST   | `/api/registration-requests/<id>/approve/`            | Aprova cadastro              | Admin     |
| POST   | `/api/registration-requests/<id>/reject/`             | Rejeita cadastro             | Admin     |

**Filtros:** `?status=pending` | `approved` | `rejected`

---

### Solicitações de Título de Projetista

| Método | Endpoint                                              | Descrição                        | Permissão   |
|--------|------------------------------------------------------|----------------------------------|-------------|
| GET    | `/api/projectist-requests/`                           | Lista solicitações                | Autenticado |
| POST   | `/api/projectist-requests/`                           | Cria nova solicitação             | Autenticado |
| POST   | `/api/projectist-requests/<id>/approve/`              | Aprova e concede cargo            | Admin       |
| POST   | `/api/projectist-requests/<id>/reject/`               | Rejeita                          | Admin       |

**Body para criar:**
```json
{
  "motivation": "Quero contribuir com projetos de impressão 3D..."
}
```

---

## 4. Notícias

> 🌐 **Listagem e detalhe são públicos** — não precisa de autenticação para ler.

| Método | Endpoint                    | Descrição                              | Permissão        |
|--------|-----------------------------|----------------------------------------|------------------|
| GET    | `/api/noticias/`             | Lista notícias publicadas              | Público          |
| GET    | `/api/noticias/<slug>/`      | Detalhe de uma notícia (por slug)      | Público          |
| POST   | `/api/noticias/`             | Cria notícia                           | Admin            |
| PATCH  | `/api/noticias/<slug>/`      | Edita notícia                          | Admin            |
| DELETE | `/api/noticias/<slug>/`      | Remove notícia                         | Admin            |

**Filtros disponíveis:**
```
?destaque=true          → apenas destaques
?publicado=true         → apenas publicadas
?search=impressora      → busca no título e resumo
```

**Resposta (lista):**
```json
{
  "count": 42,
  "next": "/api/noticias/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "titulo": "FabLab inaugura nova impressora",
      "slug": "fablab-inaugura-nova-impressora",
      "resumo": "Novo equipamento de última geração...",
      "imagem": "/media/noticias/foto.webp",
      "data_publicacao": "2025-03-15T14:30:00Z",
      "destaque": true,
      "publicado": true,
      "hashtags": [
        { "id": 1, "nome": "impressao3d", "slug": "impressao3d" }
      ]
    }
  ]
}
```

> 📌 A galeria de fotos de cada notícia (`NoticiaFoto`) ainda não está no serializer — a incluir em versão futura.

---

## 5. Equipamentos (Materiais)

> 🌐 **Leitura pública.**

| Método | Endpoint                  | Descrição              | Permissão       |
|--------|---------------------------|------------------------|-----------------|
| GET    | `/api/materiais/`          | Lista equipamentos     | Público         |
| GET    | `/api/materiais/<id>/`     | Detalhe de um equipamento | Público      |

**Filtros:**
```
?situacao=ativo           → apenas ativos
?situacao=desativado
?search=laser             → busca no nome e marca
```

**Campos:** `id`, `nome_do_material`, `outras_denominacoes`, `marca`, `modelo`, `fabricante`, `link_fabricante`, `imagem_do_material`, `descricao_do_material`, `parametros`, `situacao`, `responsaveis`

---

## 6. Serviços

> 🌐 **Leitura pública.**

### Categorias de Serviço

| Método | Endpoint                          | Descrição                  | Permissão |
|--------|-----------------------------------|----------------------------|-----------|
| GET    | `/api/categorias-servico/`         | Lista categorias           | Público   |
| GET    | `/api/categorias-servico/<id>/`    | Detalhe de uma categoria   | Público   |

**Campos:** `id`, `nome`, `descricao`, `icone` (nome FontAwesome), `ordem`

---

### Serviços

| Método | Endpoint               | Descrição              | Permissão |
|--------|------------------------|------------------------|-----------|
| GET    | `/api/servicos/`        | Lista serviços         | Público   |
| GET    | `/api/servicos/<id>/`   | Detalhe de um serviço  | Público   |

**Filtros:**
```
?disponivel=true          → apenas disponíveis
?categoria=<id>           → por categoria
?search=corte             → busca no nome e descrição
```

**Campos extras (pré-processados):** `como_utilizar_list` (array de strings), `aplicacoes_list` (array de strings), `categoria_nome`

---

## 7. Membros da Equipe

> 🌐 **Leitura pública.**

| Método | Endpoint              | Descrição              | Permissão |
|--------|-----------------------|------------------------|-----------|
| GET    | `/api/membros/`        | Lista membros ativos   | Público   |
| GET    | `/api/membros/<id>/`   | Detalhe de um membro   | Público   |

**Filtros:**
```
?ativo=true               → apenas ativos
?search=joao              → busca por nome ou cargo
```

**Campos:** `id`, `nome`, `cargo`, `email`, `foto`, `bio`, `linkedin`, `github`, `lattes`, `ativo`, `ordem`, `data_entrada`

---

## 8. Projetos

> 🌐 **Projetos publicados são públicos; staff vê todos.**

| Método | Endpoint                         | Descrição                     | Permissão       |
|--------|----------------------------------|-------------------------------|-----------------|
| GET    | `/api/projetos/`                  | Lista projetos                | Público         |
| GET    | `/api/projetos/<slug>/`           | Detalhe de um projeto         | Público         |
| POST   | `/api/projetos/`                  | Cria projeto                  | Staff           |
| PATCH  | `/api/projetos/<slug>/`           | Edita projeto                 | Staff           |
| DELETE | `/api/projetos/<slug>/`           | Remove projeto                | Staff           |

**Filtros:**
```
?status=em_andamento      → em_andamento | concluido | planejado | cancelado
?destaque=true
?publicado=true
?search=drone
```

**Campos principais:** `id`, `titulo`, `slug`, `descricao_curta`, `descricao`, `imagem`, `status`, `data_inicio`, `data_conclusao`, `responsavel`, `participantes`, `tags`, `link_github`, `link_video`, `link_documentacao`, `mostrar_na_home`, `destaque`

---

### Comentários de Projetos

| Método | Endpoint                             | Descrição           | Permissão               |
|--------|--------------------------------------|---------------------|-------------------------|
| GET    | `/api/comentarios-projeto/`           | Lista comentários   | Autenticado             |
| POST   | `/api/comentarios-projeto/`           | Cria comentário     | Autenticado             |
| DELETE | `/api/comentarios-projeto/<id>/`      | Remove comentário   | Dono ou Staff           |

**Filtros:** `?projeto=<id>`

**Body para criar:**
```json
{
  "projeto": 5,
  "texto": "Excelente projeto!"
}
```

---

### Tags de Projetos

| Método | Endpoint                  | Descrição       | Permissão |
|--------|---------------------------|-----------------|-----------|
| GET    | `/api/projeto-tags/`       | Lista tags      | Público   |

---

### Grupos de Projeto

| Método | Endpoint                    | Descrição         | Permissão   |
|--------|-----------------------------|-------------------|-------------|
| GET    | `/api/grupos-projeto/`       | Lista grupos      | Superuser   |
| POST   | `/api/grupos-projeto/`       | Cria grupo        | Superuser   |

---

## 9. Tarefas (To-Do)

> Cada usuário vê apenas as próprias tarefas; staff vê todas.

| Método | Endpoint                    | Descrição           | Permissão   |
|--------|-----------------------------|---------------------|-------------|
| GET    | `/api/todo-tasks/`           | Lista tarefas       | Autenticado |
| POST   | `/api/todo-tasks/`           | Cria tarefa         | Autenticado |
| GET    | `/api/todo-tasks/<id>/`      | Detalhe de tarefa   | Autenticado |
| PATCH  | `/api/todo-tasks/<id>/`      | Atualiza tarefa     | Autenticado |
| DELETE | `/api/todo-tasks/<id>/`      | Remove tarefa       | Autenticado |

**Filtros:**
```
?prioridade=alta          → baixa | media | alta | urgente
?concluida=false
?projeto=<id>
?search=relatório
```

**Body:**
```json
{
  "titulo": "Revisar documentação",
  "descricao": "...",
  "data_limite": "2025-04-01",
  "prioridade": "alta",
  "concluida": false,
  "projeto": 3
}
```

---

## 10. Agenda / Eventos

| Método | Endpoint                           | Descrição                                | Permissão   |
|--------|------------------------------------|------------------------------------------|-------------|
| GET    | `/api/eventos/`                     | Lista eventos (apenas aprovados para user) | Autenticado |
| POST   | `/api/eventos/`                     | Cria evento / solicita visita            | Autenticado |
| GET    | `/api/eventos/<id>/`                | Detalhe de evento                        | Autenticado |
| PATCH  | `/api/eventos/<id>/`                | Edita evento                             | Autenticado |
| DELETE | `/api/eventos/<id>/`                | Remove evento                            | Autenticado |
| POST   | `/api/eventos/<id>/approve/`        | Aprova evento                            | Admin       |
| GET    | `/api/eventos/pending/`             | Lista eventos pendentes de aprovação     | Admin       |

**Filtros:**
```
?event_type=visit         → internal | workshop | visit | maintenance | other
?approved=true
?search=workshop
```

**Body:**
```json
{
  "title": "Workshop de Impressão 3D",
  "description": "...",
  "start_time": "2025-04-10T09:00:00Z",
  "end_time": "2025-04-10T12:00:00Z",
  "event_type": "workshop"
}
```

**Campos:** `id`, `title`, `description`, `start_time`, `end_time`, `event_type`, `created_by`, `approved`, `participants`

---

## 11. Horário de Funcionamento do Lab

> 🌐 **Público para leitura.**

| Método | Endpoint               | Descrição                         | Permissão |
|--------|------------------------|-----------------------------------|-----------|
| GET    | `/api/horarios/`        | Horário de funcionamento por dia  | Público   |

**Resposta:**
```json
[
  {
    "id": 1,
    "day_of_week": 0,       // 0=Segunda ... 6=Domingo
    "opening_time": "08:00:00",
    "closing_time": "18:00:00",
    "is_closed": false
  }
]
```

---

## 12. Inventário

> 🔒 **Apenas Admin.**

### Categorias

| Método | Endpoint                          | Descrição              | Permissão |
|--------|-----------------------------------|------------------------|-----------|
| GET    | `/api/categorias-inventario/`      | Lista categorias       | Admin     |
| POST   | `/api/categorias-inventario/`      | Cria categoria         | Admin     |

---

### Itens

| Método | Endpoint                   | Descrição                        | Permissão |
|--------|----------------------------|----------------------------------|-----------|
| GET    | `/api/itens/`               | Lista todos os itens             | Admin     |
| POST   | `/api/itens/`               | Cadastra item                    | Admin     |
| GET    | `/api/itens/<id>/`          | Detalhe de um item               | Admin     |
| PATCH  | `/api/itens/<id>/`          | Atualiza item                    | Admin     |
| DELETE | `/api/itens/<id>/`          | Remove item                      | Admin     |
| GET    | `/api/itens/criticos/`      | Itens com estoque abaixo do mínimo | Admin   |

**Filtros:**
```
?categoria=<id>
?unidade=kg               → un | kg | g | l | ml | m | cm | mm | m²
?search=filamento
```

**Campos:** `id`, `codigo`, `nome`, `descricao`, `categoria`, `quantidade`, `quantidade_minima`, `unidade`, `valor_unitario`, `localizacao`, `imagem`, `observacoes`, `data_cadastro`

---

## 13. Empréstimos de Itens

> 🔒 **Apenas Admin.**

| Método | Endpoint                          | Descrição                     | Permissão |
|--------|-----------------------------------|-------------------------------|-----------|
| GET    | `/api/emprestimos/`                | Lista empréstimos             | Admin     |
| POST   | `/api/emprestimos/`                | Registra empréstimo           | Admin     |
| GET    | `/api/emprestimos/<id>/`           | Detalhe de um empréstimo      | Admin     |
| POST   | `/api/emprestimos/<id>/devolver/`  | Registra devolução            | Admin     |

**Filtros:** `?item=<id>` | `?usuario=<matricula>`

**Body para criar:**
```json
{
  "item": 12,
  "usuario": "2024001234567",
  "quantidade": 2,
  "data_prevista_devolucao": "2025-04-15T18:00:00Z",
  "observacao": "Para o projeto de drone"
}
```

---

## 14. Controle de Acesso e Ponto

### Registros de Ponto (Time Logs)

> 🔒 **Admin.**

| Método | Endpoint               | Descrição                   | Permissão |
|--------|------------------------|-----------------------------|-----------|
| GET    | `/api/time-logs/`       | Lista registros de entrada/saída | Admin |
| POST   | `/api/time-logs/`       | Registra entrada ou saída   | Admin     |

**Body:**
```json
{
  "user": "2024001234567",
  "status": "entrada"   // "entrada" ou "saida"
}
```

---

### Sessões de Presença

| Método | Endpoint               | Descrição                     | Permissão |
|--------|------------------------|-------------------------------|-----------|
| GET    | `/api/sessions/`        | Lista sessões (entrada + saída combinadas) | Admin |

**Campos:** `id`, `user`, `entry_time`, `exit_time`, `duration`, `is_active`

---

### Horas Semanais Exigidas

| Método | Endpoint                | Descrição                           | Permissão |
|--------|-------------------------|-------------------------------------|-----------|
| GET    | `/api/weekly-hours/`     | Horas semanais por usuário          | Admin     |
| PATCH  | `/api/weekly-hours/<id>/`| Atualiza carga horária              | Admin     |

---

## 15. Ar-Condicionado (IoT)

> 🔒 **Admin.** Controla os dispositivos IoT do laboratório em tempo real.

### Status dos Aparelhos

| Método | Endpoint                             | Descrição                        | Permissão |
|--------|--------------------------------------|----------------------------------|-----------|
| GET    | `/api/ar-condicionados/`              | Lista todos os ACs               | Admin     |
| GET    | `/api/ar-condicionados/<id>/`         | Status de um AC                  | Admin     |
| POST   | `/api/ar-condicionados/<id>/toggle/`  | Liga / Desliga                   | Admin     |
| POST   | `/api/ar-condicionados/<id>/set_temperature/` | Altera temperatura      | Admin     |

**Body para set_temperature:**
```json
{
  "temperatura": 23
}
```

**Campos de status:**
```json
{
  "id": 1,
  "nome": "AC Sala Principal",
  "tag": "AC_SALA_01",
  "estado": true,
  "temperatura": 23,
  "modo": "cold",
  "velocidade": 2,
  "swing": false,
  "online": true,
  "ultimo_ping": "2025-03-20T14:00:00Z",
  "consumo_atual": 1450.5,
  "temperatura_ambiente": 28.3
}
```

---

### Fila de Comandos

| Método | Endpoint             | Descrição                      | Permissão |
|--------|----------------------|--------------------------------|-----------|
| GET    | `/api/comandos-ar/`   | Lista comandos pendentes/executados | Admin |

**Filtros:** `?executado=false` | `?ar_condicionado=<id>`

---

### Imagens do Carrossel (Home)

> 🌐 **Público.**

| Método | Endpoint           | Descrição                      | Permissão |
|--------|--------------------|--------------------------------|-----------|
| GET    | `/api/carousel/`    | Lista imagens ativas do carrossel | Público |

---

## 16. Kanban

> 🔒 **Usuários autenticados.**

### Colunas

| Método | Endpoint                       | Descrição          | Permissão   |
|--------|--------------------------------|--------------------|-------------|
| GET    | `/api/kanban-columns/`          | Lista colunas      | Autenticado |
| POST   | `/api/kanban-columns/`          | Cria coluna        | Autenticado |
| PATCH  | `/api/kanban-columns/<id>/`     | Edita coluna       | Autenticado |
| DELETE | `/api/kanban-columns/<id>/`     | Remove coluna      | Autenticado |

---

### Cards

| Método | Endpoint                    | Descrição          | Permissão   |
|--------|-----------------------------|--------------------|-------------|
| GET    | `/api/kanban-cards/`         | Lista cards        | Autenticado |
| POST   | `/api/kanban-cards/`         | Cria card          | Autenticado |
| PATCH  | `/api/kanban-cards/<id>/`    | Edita card         | Autenticado |
| DELETE | `/api/kanban-cards/<id>/`    | Remove card        | Autenticado |

**Filtros:**
```
?coluna=<id>
?projeto=<id>
?responsavel=<matricula>
?prioridade=alta          → baixa | media | alta | urgente
?visivel=true
```

**Campos:** `id`, `titulo`, `descricao`, `coluna`, `projeto`, `responsavel`, `membros`, `prioridade`, `data_inicio`, `prazo`, `progresso`, `tempo_trabalhado`, `ordem`

---

## 17. Repositório de Recursos

### Categorias de Recursos

| Método | Endpoint                         | Descrição               | Permissão |
|--------|----------------------------------|-------------------------|-----------|
| GET    | `/api/categorias-recurso/`        | Lista categorias        | Público   |

---

### Recursos

| Método | Endpoint                  | Descrição           | Permissão   |
|--------|---------------------------|---------------------|-------------|
| GET    | `/api/recursos/`           | Lista recursos      | Autenticado |
| GET    | `/api/recursos/<id>/`      | Detalhe de recurso  | Autenticado |
| POST   | `/api/recursos/`           | Cria recurso        | Autenticado |
| PATCH  | `/api/recursos/<id>/`      | Edita recurso       | Dono/Staff  |
| DELETE | `/api/recursos/<id>/`      | Remove recurso      | Dono/Staff  |

**Campos:** `id`, `title`, `slug`, `description`, `resource_type` (document/image/video/audio/code/text/link/other), `category`, `project`, `visibility` (public/members/team), `text_content`, `external_url`, `featured`, `tags`

---

### Arquivos de Recursos

| Método | Endpoint                       | Descrição         | Permissão   |
|--------|--------------------------------|-------------------|-------------|
| GET    | `/api/resource-files/`          | Lista arquivos    | Autenticado |
| POST   | `/api/resource-files/`          | Upload de arquivo | Autenticado |
| DELETE | `/api/resource-files/<id>/`     | Remove arquivo    | Autenticado |

---

### Comentários de Recursos

| Método | Endpoint                          | Descrição          | Permissão   |
|--------|-----------------------------------|--------------------|-------------|
| GET    | `/api/resource-comments/`          | Lista comentários  | Autenticado |
| POST   | `/api/resource-comments/`          | Cria comentário    | Autenticado |
| DELETE | `/api/resource-comments/<id>/`     | Remove comentário  | Dono/Staff  |

---

## 18. Solicitações de Serviço

| Método | Endpoint                        | Descrição                       | Permissão   |
|--------|---------------------------------|---------------------------------|-------------|
| GET    | `/api/solicitacoes-interesse/`   | Lista solicitações              | Autenticado |
| POST   | `/api/solicitacoes-interesse/`   | Envia nova solicitação          | **Público** |

**Filtros:** `?status=pendente` | `analise` | `respondido` | `concluido` | `cancelado`

**Body para criar:**
```json
{
  "nome": "Maria Souza",
  "email": "maria@ifmt.edu.br",
  "telefone": "(65) 99999-0000",
  "servico": 3,
  "descricao_projeto": "Preciso cortar acrílico para minha maquete..."
}
```

> 💡 Se o usuário estiver logado, associe o token — o campo `usuario` é preenchido automaticamente.

---

## 19. Dashboard Administrativo

> 🔒 **Gestão (superuser ou acesso_gestao).**

| Método | Endpoint          | Descrição                               | Permissão |
|--------|-------------------|-----------------------------------------|-----------|
| GET    | `/api/dashboard/` | Estatísticas consolidadas do sistema    | Gestão    |

**Resposta:**
```json
{
  "usuarios": {
    "total": 150,
    "ativos": 142,
    "staff": 12,
    "superusers": 2
  },
  "projetos": {
    "total": 38,
    "em_andamento": 15,
    "concluidos": 20
  },
  "inventario": {
    "total_itens": 213,
    "estoque_baixo": 7,
    "emprestimos_ativos": 4
  },
  "eventos": {
    "pendentes": 3,
    "proximos": 8
  },
  "noticias_recentes": [ ... ],
  "logs_recentes": [ ... ]
}
```

---

## 20. Níveis de Permissão

| Nível              | Quem é                                              | Acesso                                    |
|--------------------|-----------------------------------------------------|-------------------------------------------|
| **Público**        | Qualquer pessoa (sem token)                         | Notícias, Serviços, Equipamentos, Membros, Horários, Carrossel |
| **Autenticado**    | Qualquer usuário com token válido                   | Perfil, Tarefas, Eventos, Kanban, Repositório, Solicitações |
| **Staff**          | `is_staff = True`                                   | CRUD de conteúdo, projetos, controle geral |
| **Admin**          | `is_staff = True` (via `IsAdminUser`)               | Inventário, Ponto, AC, Logs, Aprovações  |
| **Gestão**         | `is_superuser` ou `acesso_gestao.tem_acesso = True` | Dashboard, Configurações                  |
| **Superuser**      | `is_superuser = True`                               | Tudo, incluindo gerenciar acessos         |

---

## 21. Guia Rápido Flutter / Dart

### Dependências sugeridas (`pubspec.yaml`)

```yaml
dependencies:
  http: ^1.2.1
  flutter_secure_storage: ^9.0.0   # armazenar tokens com segurança
  shared_preferences: ^2.2.3       # cache leve
  cached_network_image: ^3.3.1     # imagens com cache automático
  intl: ^0.19.0                    # formatação de datas
```

---

### Classe de serviço de autenticação

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthService {
  static const _baseUrl = 'http://SEU_SERVIDOR/api';
  static const _storage = FlutterSecureStorage();

  /// Faz login com matrícula + senha e salva os tokens
  static Future<bool> login(String matricula, String senha) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/token/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': matricula, 'password': senha}),
    );
    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      await _storage.write(key: 'access', value: data['access']);
      await _storage.write(key: 'refresh', value: data['refresh']);
      return true;
    }
    return false;
  }

  /// Renova o access token usando o refresh token
  static Future<String?> refreshToken() async {
    final refresh = await _storage.read(key: 'refresh');
    if (refresh == null) return null;

    final res = await http.post(
      Uri.parse('$_baseUrl/token/refresh/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'refresh': refresh}),
    );
    if (res.statusCode == 200) {
      final newAccess = jsonDecode(res.body)['access'];
      await _storage.write(key: 'access', value: newAccess);
      return newAccess;
    }
    // Refresh expirado → redirecionar para login
    await logout();
    return null;
  }

  static Future<String?> getAccessToken() => _storage.read(key: 'access');

  static Future<void> logout() async {
    await _storage.deleteAll();
  }
}
```

---

### Classe base para requisições autenticadas

```dart
class ApiClient {
  static const _baseUrl = 'http://SEU_SERVIDOR/api';

  static Future<Map<String, String>> _headers() async {
    final token = await AuthService.getAccessToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  static Future<http.Response> get(String path) async {
    var res = await http.get(
      Uri.parse('$_baseUrl$path'),
      headers: await _headers(),
    );
    // Token expirado → renova e tenta de novo
    if (res.statusCode == 401) {
      final newToken = await AuthService.refreshToken();
      if (newToken != null) {
        res = await http.get(
          Uri.parse('$_baseUrl$path'),
          headers: await _headers(),
        );
      }
    }
    return res;
  }

  static Future<http.Response> post(String path, Map<String, dynamic> body) async {
    final res = await http.post(
      Uri.parse('$_baseUrl$path'),
      headers: await _headers(),
      body: jsonEncode(body),
    );
    return res;
  }

  static Future<http.Response> patch(String path, Map<String, dynamic> body) async {
    final res = await http.patch(
      Uri.parse('$_baseUrl$path'),
      headers: await _headers(),
      body: jsonEncode(body),
    );
    return res;
  }
}
```

---

### Exemplos de uso

```dart
// Buscar notícias em destaque
final res = await ApiClient.get('/noticias/?destaque=true&page=1');
final data = jsonDecode(res.body);
final noticias = data['results'] as List;

// Buscar perfil do usuário logado
final res = await ApiClient.get('/me/');
final perfil = jsonDecode(res.body);

// Buscar horário de funcionamento
final res = await ApiClient.get('/horarios/');
final horarios = jsonDecode(res.body) as List;

// Criar tarefa
final res = await ApiClient.post('/todo-tasks/', {
  'titulo': 'Revisar relatório',
  'prioridade': 'alta',
  'data_limite': '2025-04-30',
});

// Enviar solicitação de serviço (público)
final res = await http.post(
  Uri.parse('http://SEU_SERVIDOR/api/solicitacoes-interesse/'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'nome': 'João',
    'email': 'joao@ifmt.edu.br',
    'servico': 2,
    'descricao_projeto': 'Quero imprimir uma peça...',
  }),
);

// Ligar/Desligar AC (admin)
final res = await ApiClient.post('/ar-condicionados/1/toggle/', {});
```

---

### Estrutura de Telas Sugeridas para o App

```
📱 FabLab App
│
├── 🔓 Público (sem login)
│   ├── Home         → /api/carousel/ + /api/noticias/?destaque=true
│   ├── Notícias     → /api/noticias/
│   ├── Serviços     → /api/categorias-servico/ + /api/servicos/
│   ├── Equipamentos → /api/materiais/
│   ├── Membros      → /api/membros/
│   └── Horários     → /api/horarios/
│
├── 🔐 Autenticado
│   ├── Perfil          → GET/PATCH /api/me/
│   ├── Tarefas         → /api/todo-tasks/
│   ├── Agenda          → /api/eventos/
│   ├── Meus projetos   → /api/projetos/ (participante)
│   ├── Kanban          → /api/kanban-columns/ + /api/kanban-cards/
│   ├── Repositório     → /api/recursos/
│   └── Solicitar serviço → POST /api/solicitacoes-interesse/
│
└── 🔒 Admin / Staff
    ├── Dashboard       → /api/dashboard/
    ├── Ponto           → /api/time-logs/ + /api/sessions/
    ├── Inventário      → /api/itens/ + /api/emprestimos/
    ├── Controle AC     → /api/ar-condicionados/
    ├── Aprovações      → /api/registration-requests/ + /api/eventos/pending/
    └── Configurações   → /api/configuracoes/
```

---

*Documentação gerada em março de 2025 — versão 1.0*
*Base code: Django 4.2 + Django REST Framework + SimpleJWT*
