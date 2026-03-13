from django import forms
from .models import AvailabilitySlot
from datetime import datetime

class AvailabilitySlotForm(forms.ModelForm):
    class Meta:
        model = AvailabilitySlot
        fields = ['date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if date and start_time and end_time:
            if end_time <= start_time:
                raise forms.ValidationError("End time must be after start time")
            
            slot_datetime = datetime.combine(date, start_time)
            if slot_datetime <= datetime.now():
                raise forms.ValidationError("Cannot create slots in the past")
        
        return cleaned_data