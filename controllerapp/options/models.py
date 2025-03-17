from django.db import models

# Create your models here.
class Material(models.Model):
    Nome_do_meterial = models.CharField(max_length=100)
    imagem_do_material = models.ImageField(upload_to='materials/')
    descrição_do_material = models.TextField()

    def __str__(self):
        return self.Nome_do_meterial

class Membro(models.Model):
    nome = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    foto = models.ImageField(upload_to='membros/', blank=True)
    bio = models.TextField(blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    lattes = models.URLField(blank=True)
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0)
    data_entrada = models.DateField(auto_now_add=True)
    
    class Meta:
        ordering = ['ordem', 'nome']
        verbose_name = 'Membro'
        verbose_name_plural = 'Membros'
    
    def __str__(self):
        return self.nome
