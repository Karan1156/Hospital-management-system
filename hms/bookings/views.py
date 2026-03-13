from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from .models import Booking
from .forms import BookingForm
from doctors.models import AvailabilitySlot
from datetime import datetime
import requests
from django.conf import settings
import threading
import time

def send_email_notification(booking_data):
    try:
        requests.post(settings.SERVERLESS_EMAIL_URL, json=booking_data, timeout=5)
    except:
        pass

@login_required
@transaction.atomic
def book_appointment(request):
    if request.user.profile.user_type != 'patient':
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = BookingForm(request.POST, user=request.user)
        
        if form.is_valid():
            doctor = form.cleaned_data['doctor']
            time_slot = form.cleaned_data['time_slot']
            symptoms = form.cleaned_data['symptoms']
            
            try:
                with transaction.atomic():
                    slot = AvailabilitySlot.objects.select_for_update().get(
                        id=time_slot.id,
                        is_booked=False
                    )
                    
                    booking = Booking.objects.create(
                        patient=request.user,
                        slot=slot,
                        symptoms=symptoms,
                        status='confirmed'
                    )
                    
                    slot.is_booked = True
                    slot.save()
                
                # Send email in background
                email_data = {
                    'action': 'BOOKING_CONFIRMATION',
                    'patient_email': request.user.email,
                    'doctor_email': doctor.user.email,
                    'patient_name': request.user.get_full_name(),
                    'doctor_name': doctor.user.get_full_name(),
                    'appointment_date': str(slot.date),
                    'appointment_time': f"{slot.start_time} - {slot.end_time}",
                    'booking_id': booking.id
                }
                
                threading.Thread(target=send_email_notification, args=(email_data,)).start()
                
                messages.success(request, 'Appointment booked!')
                return redirect('patient_appointments')
                
            except AvailabilitySlot.DoesNotExist:
                messages.error(request, 'Slot no longer available')
                return redirect('book_appointment')
    else:
        form = BookingForm(user=request.user)
    
    return render(request, 'bookings/book_appointment.html', {'form': form})

@login_required
def get_time_slots(request):
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')
    
    if doctor_id and date_str:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        slots = AvailabilitySlot.objects.filter(
            doctor_id=doctor_id,
            date=date_obj,
            is_booked=False
        ).order_by('start_time')
        
        slots_data = [{
            'id': slot.id,
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'display': f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
        } for slot in slots]
        
        return JsonResponse({'slots': slots_data})
    
    return JsonResponse({'slots': []})

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, patient=request.user)
    
    if booking.status == 'confirmed':
        with transaction.atomic():
            booking.cancel_booking()
        messages.success(request, 'Booking cancelled')
    
    return redirect('patient_appointments')