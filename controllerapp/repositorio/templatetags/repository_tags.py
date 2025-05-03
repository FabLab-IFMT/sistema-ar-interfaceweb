from django import template
from django.template.defaultfilters import stringfilter
import re

register = template.Library()

@register.filter
@stringfilter
def split(value, arg):
    """
    Divide uma string pelo argumento fornecido.
    
    Exemplo de uso:
    {% for item in value|split:"," %}
        {{ item }}
    {% endfor %}
    """
    return value.split(arg)

@register.filter
@stringfilter
def trim(value):
    """Remove espaços em branco no início e fim de uma string."""
    return value.strip()

@register.filter
@stringfilter
def youtube_embed_url(url):
    """Converte uma URL do YouTube em uma URL de incorporação."""
    youtube_regex = r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([^&]+)'
    match = re.search(youtube_regex, url)
    if match:
        video_id = match.group(4)
        return f'https://www.youtube.com/embed/{video_id}'
    return url

@register.filter
@stringfilter
def get_language_from_ext(ext):
    """Retorna a linguagem de programação a partir da extensão do arquivo."""
    ext = ext.lower().lstrip('.')
    language_map = {
        'py': 'python',
        'js': 'javascript',
        'html': 'html',
        'css': 'css',
        'java': 'java',
        'c': 'c',
        'cpp': 'cpp',
        'php': 'php',
        'rb': 'ruby',
        'go': 'go',
        'ts': 'typescript',
        'json': 'json',
        'xml': 'xml',
        'md': 'markdown',
    }
    return language_map.get(ext, 'plaintext')
