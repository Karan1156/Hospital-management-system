from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import time, timedelta

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)
    experience_years = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(70)])
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    qualification = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    google_calendar_token = models.TextField(blank=True, help_text="OAuth token for Google Calendar")
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialization}"
    
    def get_upcoming_appointments(self):
        from bookings.models import Booking
        from datetime import datetime
        return Booking.objects.filter(
            slot__doctor=self,
            status='confirmed',
            slot__date__gte=datetime.now().date()
        )

class AvailabilitySlot(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='availability_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['doctor', 'date', 'start_time']
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['doctor', 'date', 'is_booked']),
        ]
    
    def __str__(self):
        return f"{self.doctor} - {self.date} {self.start_time}-{self.end_time}"
    
    def get_duration(self):
        start = timedelta(hours=self.start_time.hour, minutes=self.start_time.minute)
        end = timedelta(hours=self.end_time.hour, minutes=self.end_time.minute)
        return end - start
    
    def is_future(self):
        from django.utils import timezone
        import datetime
        slot_datetime = timezone.make_aware(
            datetime.datetime.combine(self.date, self.start_time)
        )
        return slot_datetime > timezone.now()
    
    def is_past(self):
        from django.utils import timezone
        import datetime
        slot_datetime = timezone.make_aware(
            datetime.datetime.combine(self.date, self.end_time)
        )
        return slot_datetime < timezone.now()