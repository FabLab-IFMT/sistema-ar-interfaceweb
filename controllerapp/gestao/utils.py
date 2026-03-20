"""
Utilitários de imagem para o painel de gestão FabLab.
"""
import sys
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile


def convert_to_webp(image_file, quality: int = 82, max_width: int = 1920) -> InMemoryUploadedFile:
    """
    Converte qualquer imagem enviada via upload para o formato WebP.

    - quality: 0-100 (82 = boa qualidade, arquivo leve)
    - max_width: redimensiona se maior que este valor mantendo aspecto

    Retorna um InMemoryUploadedFile pronto para ser atribuído a um ImageField.
    """
    from PIL import Image

    # Abre a imagem a partir do arquivo enviado
    img = Image.open(image_file)

    # Corrige orientação EXIF (fotos de celular giradas)
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # Redimensiona se necessário (mantém proporção)
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    # WebP suporta RGBA (transparência) — converte apenas modos incompatíveis
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGBA' if 'transparency' in img.info else 'RGB')

    # Salva em memória como WebP
    output = BytesIO()
    img.save(output, format='WEBP', quality=quality, method=6)
    output.seek(0)

    # Monta o nome do arquivo com extensão .webp
    original_name = getattr(image_file, 'name', 'imagem')
    stem = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name
    webp_name = f"{stem}.webp"

    return InMemoryUploadedFile(
        file=output,
        field_name='ImageField',
        name=webp_name,
        content_type='image/webp',
        size=sys.getsizeof(output),
        charset=None,
    )
