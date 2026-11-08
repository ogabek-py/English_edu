from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import datetime
import random

class Account(AbstractUser):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )
    email = models.EmailField(unique=True)
    is_approved = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    last_activity = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username

class UserActivity(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=100) # e.g., 'lesson_completed', 'word_learned', 'login'
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "User activities"

class UserProgress(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='progress')
    total_lessons_completed = models.IntegerField(default=0)
    total_words_learned = models.IntegerField(default=0)
    learning_streak = models.IntegerField(default=0)
    last_streak_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} progress"

class AuditLog(models.Model):
    action = models.CharField(max_length=255)
    admin = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    target_user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name='audit_targets')
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

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

