from django.db import models
from django.contrib.auth.models import User

class PatientProfile(models.Model):
    BLOOD_GROUPS = (
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField()
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUPS, blank=True)
    emergency_contact = models.CharField(max_length=15)
    address = models.TextField()
    medical_history = models.TextField(blank=True)
    google_calendar_token = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Patient"