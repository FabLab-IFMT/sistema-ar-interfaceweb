from django import template
import re

register = template.Library()

@register.filter
def split_first_sentence(text):
    """Extrai a primeira frase de um texto para usar como título"""
    # Procura por ponto seguido de espaço ou fim da string
    match = re.search(r'^([^.!?]+[.!?])', text)
    if match:
        return match.group(1).strip()
    # Se não encontrou ponto, retorna o texto até 50 caracteres
    return text[:50] + '...' if len(text) > 50 else text

@register.filter
def remove_first_sentence(text):
    """Remove a primeira frase de um texto para usar como restante do conteúdo"""
    # Procura por ponto seguido de espaço e retorna o que vem depois
    match = re.search(r'^[^.!?]+[.!?]\s*(.*)', text)
    if match:
        return match.group(1).strip()
    return ''