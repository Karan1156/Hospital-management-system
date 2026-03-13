from django.db import models
from django.contrib.auth.models import User
from doctors.models import AvailabilitySlot

class Booking(models.Model):
    STATUS_CHOICES = (
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_bookings')
    slot = models.OneToOneField(AvailabilitySlot, on_delete=models.CASCADE, related_name='booking')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    symptoms = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    patient_calendar_event_id = models.CharField(max_length=255, blank=True)
    doctor_calendar_event_id = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Booking {self.id}"
    
    def cancel_booking(self):
        self.status = 'cancelled'
        self.slot.is_booked = False
        self.slot.save()
        self.save()