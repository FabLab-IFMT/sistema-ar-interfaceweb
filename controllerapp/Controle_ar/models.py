from django.db import models

class CarouselImage(models.Model):
    image = models.ImageField(upload_to='carousel/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField(default=True, help_text="Marque para exibir essa imagem no carrossel.")
    title = models.CharField(max_length=255, blank=True, null=True, help_text="Título da imagem.")
    description = models.TextField(blank=True, null=True, help_text="Descrição exibida junto da imagem.")
    link = models.CharField(max_length=255, blank=True, null=True, help_text="Link para tornar a imagem clicável.")

    def __str__(self):
        return self.caption or f"Imagem {self.pk}"
