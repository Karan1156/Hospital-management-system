from django import forms
from doctors.models import DoctorProfile, AvailabilitySlot
from datetime import datetime

class BookingForm(forms.Form):
    doctor = forms.ModelChoiceField(
        queryset=DoctorProfile.objects.filter(is_available=True),
        empty_label="Select a Doctor",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    time_slot = forms.ModelChoiceField(
        queryset=AvailabilitySlot.objects.none(),
        empty_label="Select a Time Slot",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    symptoms = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
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
            except:
                pass