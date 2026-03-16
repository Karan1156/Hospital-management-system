from django.db import models
from django.contrib.auth.models import User
from doctors.models import AvailabilitySlot
from django.utils import timezone
from datetime import datetime

class Booking(models.Model):
    STATUS_CHOICES = (
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    )
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_bookings', limit_choices_to={'profile__user_type': 'patient'})
    slot = models.OneToOneField(AvailabilitySlot, on_delete=models.CASCADE, related_name='booking')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    symptoms = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Google Calendar event IDs
    patient_calendar_event_id = models.CharField(max_length=255, blank=True)
    doctor_calendar_event_id = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['slot', 'status']),
        ]
    
    def __str__(self):
        return f"Booking {self.id} - {self.patient.get_full_name()} with Dr. {self.slot.doctor.user.get_full_name()}"
    
    def cancel_booking(self):
        from django.utils import timezone
        self.status = 'cancelled'
        self.slot.is_booked = False
        self.slot.save()
        self.save()
    
    def complete_booking(self):
        self.status = 'completed'
        self.save()
    
    def reschedule(self, new_slot):
        if not new_slot.is_booked:
            # Free up old slot
            self.slot.is_booked = False
            self.slot.save()
            
            # Book new slot
            new_slot.is_booked = True
            new_slot.save()
            
            # Update booking
            self.slot = new_slot
            self.status = 'rescheduled'
            self.save()
            return True
        return False
    
    def get_doctor(self):
        return self.slot.doctor
    
    def get_appointment_datetime(self):
        return datetime.combine(self.slot.date, self.slot.start_time)
    
    @classmethod
    def get_patient_future_bookings(cls, patient):
        """Get all future confirmed bookings for a patient"""
        return cls.objects.filter(
            patient=patient,
            status='confirmed',
            slot__date__gte=timezone.now().date()
        ).order_by('slot__date', 'slot__start_time')
    
    @classmethod
    def get_patient_bookings_on_date(cls, patient, date):
        """Get all patient bookings on a specific date"""
        return cls.objects.filter(
            patient=patient,
            status='confirmed',
            slot__date=date
        )
    
    def overlaps_with(self, other_booking):
        """Check if this booking overlaps with another booking"""
        if self.slot.date != other_booking.slot.date:
            return False
        
        return not (self.slot.end_time <= other_booking.slot.start_time or 
                   self.slot.start_time >= other_booking.slot.end_time)