from django import template

register = template.Library()

@register.filter(name='abs')
def absolute_value(value):
    """Returns the absolute value of a number"""
    try:
        return abs(int(value))
    except (ValueError, TypeError):
        return value

@register.filter(name='deve_iterar')
def deve_iterar(value):
    """
    Verifica se deve continuar a iterar.
    Retorna True se o valor for diferente de zero ou vazio.
    """
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip() != ''
    if isinstance(value, (list, tuple, dict)):
        return len(value) > 0
    return bool(value)