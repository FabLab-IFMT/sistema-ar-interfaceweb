# API REST — Sistema FabLab IFMT

API REST com Django REST Framework para o app Flutter de gestão do FabLab.

## Autenticação

Todos os endpoints (exceto os marcados como públicos) requerem autenticação JWT.

```
# Login
POST /api/token/
Body: {"id": "2024123456", "password": "senha123"}
Response: {"access": "...", "refresh": "..."}

# Header de autenticação
Authorization: Bearer <access_token>
```

---

## 🔐 Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/token/` | Login — retorna access + refresh token |
| `POST` | `/api/token/refresh/` | Renovar access token |
| `GET/PATCH` | `/api/me/` | Perfil do usuário autenticado |

## 📊 Dashboard

| Método | Endpoint | Permissão | Descrição |
|--------|----------|-----------|-----------|
| `GET` | `/api/dashboard/` | Gestão | Estatísticas consolidadas do sistema |

## 👥 Users

| Método | Endpoint | Permissão | Descrição |
|--------|----------|-----------|-----------|
| `CRUD` | `/api/users/` | Staff (list) / Owner (self) | Usuários |
| `CRUD` | `/api/roles/` | Admin | Cargos/papéis |
| `CRUD` | `/api/registration-requests/` | Admin | Solicitações de registro |
| `POST` | `/api/registration-requests/{id}/approve/` | Admin | Aprovar registro |
| `POST` | `/api/registration-requests/{id}/reject/` | Admin | Rejeitar registro |
| `CRUD` | `/api/projectist-requests/` | Autenticado | Solicitações de projetista |
| `POST` | `/api/projectist-requests/{id}/approve/` | Admin | Aprovar projetista |
| `POST` | `/api/projectist-requests/{id}/reject/` | Admin | Rejeitar projetista |

## ⚙️ Gestão

| Método | Endpoint | Permissão | Descrição |
|--------|----------|-----------|-----------|
| `CRUD` | `/api/acessos-gestao/` | SuperUser | Controle de acessos à gestão |
| `POST` | `/api/acessos-gestao/{id}/toggle/` | SuperUser | Alternar acesso |
| `CRUD` | `/api/configuracoes/` | Gestão | Configurações do sistema |

## 📰 Options (Conteúdo)

| Método | Endpoint | Permissão | Descrição |
|--------|----------|-----------|-----------|
| `CRUD` | `/api/materiais/` | Staff/Público (read) | Materiais/equipamentos |
| `CRUD` | `/api/membros/` | Staff/Público (read) | Membros da equipe |
| `CRUD` | `/api/categorias-servico/` | Staff/Público (read) | Categorias de serviço |
| `CRUD` | `/api/servicos/` | Staff/Público (read) | Serviços do lab |
| `CRUD` | `/api/hashtags/` | Staff/Público (read) | Hashtags |
| `CRUD` | `/api/solicitacoes-interesse/` | Público (create) / Auth | Solicitações de interesse |
| `CRUD` | `/api/noticias/` | Público (read) / Admin | Notícias (lookup por slug) |

## 📦 Inventário

| Método | Endpoint | Permissão | Descrição |
|--------|----------|-----------|-----------|
| `CRUD` | `/api/categorias-inventario/` | Admin | Categorias do inventário |
| `CRUD` | `/api/itens/` | Admin | Itens do inventário |
| `GET` | `/api/itens/criticos/` | Admin | Itens com estoque baixo |
| `CRUD` | `/api/emprestimos/` | Admin | Empréstimos |
| `POST` | `/api/emprestimos/{id}/devolver/` | Admin | Registrar devolução |

## 🏗️ Projetos

| Método | Endpoint | Permissão | Descrição |
|--------|----------|-----------|-----------|
| `CRUD` | `/api/projeto-tags/` | Staff/Público (read) | Tags de projetos |
| `CRUD` | `/api/projetos/` | Staff/Público (read) | Projetos (lookup por slug) |
| `CRUD` | `/api/comentarios-projeto/` | Autenticado | Comentários em projetos |
| `CRUD` | `/api/grupos-projeto/` | SuperUser | Grupos de projetos |
| `CRUD` | `/api/todo-tasks/` | Autenticado (own) | Tarefas (to-do list) |

## 📋 Logs e Agenda

| Método | Endpoint | Permissão | Descrição |
|--------|----------|-----------|-----------|
| `GET` | `/api/logs/` | Admin | Logs do sistema (somente leitura) |
| `CRUD` | `/api/eventos/` | Autenticado | Eventos/agenda |
| `POST` | `/api/eventos/{id}/approve/` | Admin | Aprovar evento |
| `GET` | `/api/eventos/pending/` | Admin | Eventos pendentes |
| `CRUD` | `/api/horarios/` | Staff/Público (read) | Horários de funcionamento |

## ❄️ Controle AR

| Método | Endpoint | Permissão | Descrição |
|--------|----------|-----------|-----------|
| `CRUD` | `/api/carousel/` | Público (read) / Admin | Imagens do carrossel |
| `CRUD` | `/api/ar-condicionados/` | Admin | Ar condicionados |
| `POST` | `/api/ar-condicionados/{id}/toggle/` | Admin | Ligar/desligar |
| `POST` | `/api/ar-condicionados/{id}/set_temperature/` | Admin | Alterar temperatura |
| `GET` | `/api/comandos-ar/` | Admin | Comandos pendentes (somente leitura) |

## 📌 Kanban

| Método | Endpoint | Permissão | Descrição |
|--------|----------|-----------|-----------|
| `CRUD` | `/api/kanban-columns/` | Autenticado | Colunas do kanban |
| `CRUD` | `/api/kanban-cards/` | Autenticado | Cards do kanban |
| `POST` | `/api/kanban-cards/{id}/move/` | Autenticado | Mover card |

## 📁 Repositório

| Método | Endpoint | Permissão | Descrição |
|--------|----------|-----------|-----------|
| `CRUD` | `/api/categorias-recurso/` | Staff/Público (read) | Categorias de recursos |
| `CRUD` | `/api/recursos/` | Autenticado | Recursos (lookup por slug) |
| `CRUD` | `/api/resource-files/` | Autenticado | Arquivos de recursos |
| `CRUD` | `/api/resource-comments/` | Autenticado | Comentários em recursos |

## ⏱️ Acesso e Ponto

| Método | Endpoint | Permissão | Descrição |
|--------|----------|-----------|-----------|
| `CRUD` | `/api/weekly-hours/` | Admin | Carga horária semanal |
| `CRUD` | `/api/time-logs/` | Admin | Registros de ponto |
| `CRUD` | `/api/sessions/` | Admin | Sessões de trabalho |
| `POST` | `/api/sessions/{id}/close/` | Admin | Fechar sessão ativa |

---

## Filtros e Busca

Todos os endpoints de listagem suportam:

- **Paginação**: `?page=2` (20 itens por página)
- **Busca**: `?search=termo` (nos campos configurados)
- **Ordenação**: `?ordering=campo` ou `?ordering=-campo` (descendente)
- **Filtros**: `?campo=valor` (campos específicos por endpoint)

### Exemplos

```
GET /api/noticias/?search=impressora&ordering=-data_publicacao
GET /api/itens/?categoria=1&ordering=nome
GET /api/eventos/?event_type=workshop&approved=true
GET /api/todo-tasks/?prioridade=alta&concluida=false
GET /api/emprestimos/?usuario=2024123456
```
