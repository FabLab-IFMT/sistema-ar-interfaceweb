from .models import Action


class FormattedAction:
    def __init__(self, action):
        self.date = f"{action.date.day}/{action.date.month}/{action.date.year}"
        self.time = str(action.time)
        self.author = action.author
        
        if action.type == "person_num_changed":
            self.type = "Mudança no número de pessoas"
            self.description = f"Número de pessoas foi de {action.param1} para {action.param2}"

        elif action.type == "temp_config_changed":
            self.type = "Configuração de temperatura alterada"
            self.description = f"Temperatura alterada de {action.param1} °C para {action.param2} °C"

        elif action.type == "sleep_mode_entered":
            self.type = "Modo alterado para ausente"
            self.description = "Equipamentos desligados"

        elif action.type == "exit_sleep_mode":
            self.type = "Saindo do modo ausente"
            self.description = "Equipamentos ligados"

        elif action.type == "turn_on":
            self.type = f"O controle {action.author} ligou"
            self.descrition = "Ativo e pronto para receber comandos"
        
        elif action.type == "error":
            self.type = "Ocorreu um erro"
            self.description = f"Um erro não especificado ocorreu: {action.param1} {action.param2}"

        elif action.type == "command_error":
            self.type = f"Erro ao executar comando: {action.param1}"
            self.description = f"Um erro ocorreu que impossibilitou o comando '{action.param1}' de ser executado."

        elif action.type == "init_error":
            self.type = "Erro ao inicializar o controle"
            self.description = "Um problema impediu o controle de ligar"

        elif action.type == "shutdown_error":
            self.type = "Erro ao desligar o controle"
            self.description = "Ocorreu um problema ao desligar o controle"

        else:
            self.type = "Ação indefinida"
            self.description = f"Parâmetro 1: '{action.param1}'  Parâmetro 2: '{action.param2}'"


def create_log(type, **kwargs):
    author = kwargs.get("author")
    param1 = kwargs.get("param1")
    param2 = kwargs.get ("param2")

    if not author: author = "Desconhecido"
    if not param1: param1 = "Parâmetro 1 não especificado"
    if not param2: param2 = "Parâmetro 2 não especificado"

    Action.objects.create(author=author, type=type, param1=param1, param2=param2 )

    
        