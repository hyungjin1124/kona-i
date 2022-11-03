from django.db import models

# Create your models here.
class Menu(models.Model):
    menu = models.CharField(max_length=100)
    menuId = models.CharField(max_length=100)
    placeId = models.CharField(max_length=100)
    placeName = models.CharField(max_length=100)
    merchantId = models.CharField(max_length=100)

    def __str__(self):
        return self.menu

