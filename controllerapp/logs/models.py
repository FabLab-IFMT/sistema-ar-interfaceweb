from django.db import models

# Create your models here.

class Action(models.Model):
    date = models.DateField(auto_now_add = True)
    time = models.TimeField(auto_now_add = True)
    author = models.CharField(max_length=100)
    type = models.TextField()
    param1 = models.TextField()
    param2 = models.TextField()
