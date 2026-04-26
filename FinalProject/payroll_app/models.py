from django.db import models

# Create your models here.

# Create your models here.
class Employee(models.Model):

    id = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    rate = models.FloatField
    overtime = models.FloatField
    allowance = models.FloatField
    
    def getName(self):
        return self.name

    def __str__(self):
        return f"{self.id} - {self.name}"
