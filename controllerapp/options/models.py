from django.db import models

# Create your models here.
class Material(models.Model):
    Nome_do_meterial = models.CharField(max_length=100)
    imagem_do_material = models.ImageField(upload_to='materials/')
    descrição_do_material = models.TextField()

    def __str__(self):
        return self.Nome_do_meterial
