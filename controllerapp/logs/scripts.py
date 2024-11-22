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
        
        else:
            self.type = "Ação indefinida"
            self.description = f"Parâmetro 1: '{action.param1}'  Parâmetro 2: '{action.param2}'"