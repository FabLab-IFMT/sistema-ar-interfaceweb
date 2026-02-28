DEFAULT_ROLES = [
    {
        "code": "admin",
        "name": "Administrador",
        "description": "Acesso total à área interna e capacidade de delegar cargos.",
        "is_staff_equivalent": True,
    },
    {
        "code": "gestor",
        "name": "Gestor",
        "description": "Pode gerenciar projetos, inventário e processos operacionais.",
        "is_staff_equivalent": True,
    },
    {
        "code": "jornalista",
        "name": "Jornalista",
        "description": "Pode publicar notícias e editar conteúdos de comunicação.",
        "is_staff_equivalent": True,
    },
    {
        "code": "secretario",
        "name": "Secretário",
        "description": "Pode acompanhar inscrições, visitas e rotinas administrativas.",
        "is_staff_equivalent": True,
    },
    {
        "code": "pesquisador",
        "name": "Pesquisador",
        "description": "Pode navegar por projetos e recursos para pesquisa sem editar.",
        "is_staff_equivalent": False,
    },
]
