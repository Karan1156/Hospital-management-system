from django import forms
from .models import Booking
from doctors.models import DoctorProfile, AvailabilitySlot
from datetime import datetime, timedelta

class BookingForm(forms.Form):
    doctor = forms.ModelChoiceField(
        queryset=DoctorProfile.objects.filter(is_available=True),
        empty_label="Select a Doctor",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_doctor'
        })
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'id': 'id_date',
            'min': datetime.now().date().isoformat()
        })
    )
    time_slot = forms.ModelChoiceField(
        queryset=AvailabilitySlot.objects.none(),
        empty_label="Select a Time Slot",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_time_slot'
        })
    )
    symptoms = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Describe your symptoms (optional)'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if 'doctor' in self.data and 'date' in self.data:
            try:
                doctor_id = int(self.data.get('doctor'))
                date_str = self.data.get('date')
                
                if doctor_id and date_str:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    self.fields['time_slot'].queryset = AvailabilitySlot.objects.filter(
                        doctor_id=doctor_id,
                        date=date_obj,
                        is_booked=False
                    ).order_by('start_time')
                    
            except (ValueError, TypeError) as e:
                print(f"Error filtering time slots: {e}")
                self.fields['time_slot'].queryset = AvailabilitySlot.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        date = cleaned_data.get('date')
        time_slot = cleaned_data.get('time_slot')
        
        if not self.user:
            raise forms.ValidationError("User not authenticated")
        
        # Rule 1: Check if patient already has a booking at the same time
        if time_slot:
            # Check for overlapping appointments for this patient
            overlapping = Booking.objects.filter(
                patient=self.user,
                status='confirmed',
                slot__date=time_slot.date
            ).exclude(
                slot__end_time__lte=time_slot.start_time
            ).exclude(
                slot__start_time__gte=time_slot.end_time
            )
            
            if overlapping.exists():
                raise forms.ValidationError(
                    "You already have an appointment during this time period. "
                    "Please choose a different time."
                )
        
        # Rule 2: Prevent booking too many future appointments (optional)
        future_bookings = Booking.objects.filter(
            patient=self.user,
            status='confirmed',
            slot__date__gte=datetime.now().date()
        ).count()
        
        if future_bookings >= 3:  # Limit to 3 future appointments
            raise forms.ValidationError(
                "You already have 3 future appointments. "
                "Please complete or cancel existing appointments before booking new ones."
            )
        
        # Rule 3: Prevent booking same day multiple times
        same_day_bookings = Booking.objects.filter(
            patient=self.user,
            status='confirmed',
            slot__date=date
        ).count()
        
        if same_day_bookings >= 2:  # Limit to 2 appointments per day
            raise forms.ValidationError(
                "You can only book 2 appointments per day. "
                "You already have appointments booked on this date."
            )
        
        return cleaned_data