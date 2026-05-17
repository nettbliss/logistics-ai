from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('dispatcher', 'Диспетчер'),
        ('driver', 'Водитель'),
        ('client', 'Клиент'),
        ('manager', 'Руководитель'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    phone = models.CharField(max_length=20, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"