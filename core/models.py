from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

def two_weeks_from_now():
    return timezone.now() + timedelta(weeks=2)

def user_upload_path(instance, filename):
    return f'user_{instance.owner.id}/{filename}'

class Document(models.Model):
    owner       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title       = models.CharField(max_length=255)
    file        = models.FileField(upload_to=user_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expires_at  = models.DateTimeField(default=two_weeks_from_now)
    file_size   = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.title} ({self.owner.username})'

    def days_until_expiry(self):
        delta = self.expires_at - timezone.now()
        return max(delta.days, 0)

    def is_expired(self):
        return timezone.now() > self.expires_at