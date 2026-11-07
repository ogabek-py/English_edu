from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import datetime
import random

class Account(AbstractUser):
    email = models.EmailField(unique=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class PasswordResetCode(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        # Kod 10 daqiqa davomida amal qiladi
        return not self.is_used and self.created_at >= timezone.now() - datetime.timedelta(minutes=10)

    @staticmethod
    def generate_code():
        return str(random.randint(100000, 999999))

class Notification(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.title

