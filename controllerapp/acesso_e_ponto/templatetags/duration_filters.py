from django import template

register = template.Library()

@register.filter
def divisibleby(value, arg):
    """
    Retorna o resultado da divisão inteira de value por arg
    """
    try:
        value = int(float(value))
        arg = int(float(arg))
        if arg == 0:
            return 0
        return value // arg
    except (ValueError, TypeError):
        return 0
    
@register.filter
def mod(value, arg):
    """
    Retorna o resto da divisão de value por arg
    """
    try:
        value = int(float(value))
        arg = int(float(arg))
        if arg == 0:
            return 0
        return value % arg
    except (ValueError, TypeError):
        return 0

@register.filter
def format_duration(seconds):
    """
    Formata segundos em formato legível (horas e minutos)
    """
    try:
        seconds = int(float(seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}min"
        else:
            return f"{minutes}min"
    except (ValueError, TypeError):
        return "0min"
