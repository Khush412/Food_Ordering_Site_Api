from django.db import models
from django.contrib.auth.models import User

class Rider(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    aadhaar_card = models.FileField(upload_to='riders/aadhaar_cards/')
    driving_license = models.FileField(upload_to='riders/driving_licenses/')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    on_duty = models.BooleanField(default=False)  # 👈 Add this line

    def __str__(self):
        return self.name

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"