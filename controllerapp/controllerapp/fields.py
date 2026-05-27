import io
import os
import logging

from django.db.models import ImageField

logger = logging.getLogger(__name__)


class WebPImageField(ImageField):
    """
    Drop-in replacement para ImageField que converte qualquer imagem
    enviada para WebP antes de gravá-la no storage.

    Transparência é preservada (RGBA → WebP com canal alpha).
    Se a conversão falhar por qualquer motivo, o arquivo original é mantido.
    """

    def deconstruct(self):
        # Apresenta-se como ImageField nas migrations — sem mudança de schema no banco.
        name, path, args, kwargs = super().deconstruct()
        path = "django.db.models.ImageField"
        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        fieldfile = getattr(model_instance, self.attname)

        if fieldfile and not fieldfile._committed:
            self._convert_to_webp(fieldfile)

        return super().pre_save(model_instance, add)

    @staticmethod
    def _convert_to_webp(fieldfile):
        from PIL import Image

        try:
            fieldfile.seek(0)
            img = Image.open(fieldfile)
            img.load()

            # Preserva transparência; converte o resto para RGB
            if img.mode in ("RGBA", "LA", "PA"):
                img = img.convert("RGBA")
            elif img.mode != "RGB":
                img = img.convert("RGB")

            buffer = io.BytesIO()
            img.save(buffer, format="WEBP", quality=85, method=4)
            buffer.seek(0)

            old_name = fieldfile.name or "imagem"
            new_name = os.path.splitext(old_name)[0] + ".webp"

            fieldfile.file = buffer
            fieldfile.name = new_name

        except Exception as exc:
            logger.warning("Falha ao converter imagem para WebP: %s", exc)
