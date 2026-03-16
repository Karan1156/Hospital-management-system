from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from .models import Booking
from .forms import BookingForm
from doctors.models import AvailabilitySlot, DoctorProfile
from datetime import datetime
import requests
from django.conf import settings
import json
import threading
import time

# Email notification function with retry logic
def send_email_notification(booking_data):
    """Send email with retry logic"""
    max_retries = 3
    email_url = settings.SERVERLESS_EMAIL_URL
    
    if not email_url:
        print("⚠️ No email URL configured")
        return False
    
    for attempt in range(max_retries):
        try:
            print(f"📧 Sending email (attempt {attempt + 1}/{max_retries})")
            
            response = requests.post(
                email_url,
                json=booking_data,
                timeout=10,  # Increased timeout
                headers={'Connection': 'close'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ Email sent successfully (attempt {attempt + 1})")
                    return True
                else:
                    print(f"❌ Email failed: {result.get('message', 'Unknown error')}")
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"⚠️ Connection error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait 2 seconds before retry
        except requests.exceptions.Timeout:
            print(f"⚠️ Timeout error (attempt {attempt + 1})")
            if attempt < max_retries - 1:
                time.sleep(2)
        except Exception as e:
            print(f"⚠️ Unexpected error: {e}")
            break
    
    print("❌ All email attempts failed")
    return False


@login_required
@transaction.atomic
def book_appointment(request):
    if request.user.profile.user_type != 'patient':
        messages.error(request, 'Only patients can book appointments.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        print("="*50)
        print("BOOKING ATTEMPT")
        print(f"Patient: {request.user.username}")
        print("POST data:", request.POST)
        print("="*50)
        
        form = BookingForm(request.POST, user=request.user)  # Pass user to form
        
        if form.is_valid():
            print("Form is valid")
            doctor = form.cleaned_data['doctor']
            time_slot = form.cleaned_data['time_slot']
            symptoms = form.cleaned_data['symptoms']
            
            print(f"Doctor: {doctor.user.username} (ID: {doctor.id})")
            print(f"Time slot: {time_slot} (ID: {time_slot.id})")
            print(f"Slot date: {time_slot.date}, time: {time_slot.start_time}-{time_slot.end_time}")
            print(f"Slot booked status: {time_slot.is_booked}")
            
            try:
                with transaction.atomic():
                    # Get the slot and lock it for update
                    slot = AvailabilitySlot.objects.select_for_update().get(
                        id=time_slot.id,
                        is_booked=False
                    )
                    
                    print(f"Slot found and locked: {slot.date} {slot.start_time}-{slot.end_time}")
                    
                    # Create booking
                    booking = Booking.objects.create(
                        patient=request.user,
                        slot=slot,
                        symptoms=symptoms,
                        status='confirmed'
                    )
                    
                    # Mark slot as booked
                    slot.is_booked = True
                    slot.save()
                    
                    print(f"✅ Booking created successfully! ID: {booking.id}")
                    
                # Send email in background thread (don't block the response)
                email_data = {
                    'action': 'BOOKING_CONFIRMATION',
                    'patient_email': request.user.email,
                    'doctor_email': doctor.user.email,
                    'patient_name': request.user.get_full_name(),
                    'doctor_name': doctor.user.get_full_name(),
                    'appointment_date': str(slot.date),
                    'appointment_time': f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}",
                    'booking_id': booking.id
                }
                
                # Start email thread
                email_thread = threading.Thread(
                    target=send_email_notification,
                    args=(email_data,)
                )
                email_thread.daemon = True
                email_thread.start()
                
                messages.success(request, '✅ Appointment booked successfully! Confirmation email will be sent.')
                return redirect('patient_appointments')
                
            except AvailabilitySlot.DoesNotExist:
                print(f"❌ Slot {time_slot.id} not found or already booked")
                messages.error(request, 'Sorry, this time slot is no longer available.')
                return redirect('book_appointment')
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'An error occurred: {str(e)}')
                return redirect('book_appointment')
        else:
            print("Form is invalid")
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = BookingForm(user=request.user)
    
    # Get all available doctors for the dropdown
    doctors = DoctorProfile.objects.filter(is_available=True)
    
    context = {
        'form': form,
        'doctors': doctors,
    }
    return render(request, 'bookings/book_appointment.html', context)


@login_required
def get_time_slots(request):
    """AJAX view to get available time slots for selected doctor and date"""
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')
    
    print(f"get_time_slots called - doctor: {doctor_id}, date: {date_str}")
    
    if doctor_id and date_str:
        try:
            # Parse date
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Get available slots
            slots = AvailabilitySlot.objects.filter(
                doctor_id=doctor_id,
                date=date_obj,
                is_booked=False
            ).order_by('start_time')
            
            print(f"Found {slots.count()} available slots")
            
            slots_data = [{
                'id': slot.id,
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'display': f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
            } for slot in slots]
            
            return JsonResponse({'slots': slots_data})
            
        except Exception as e:
            print(f"Error in get_time_slots: {e}")
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'slots': []})


@login_required
def cancel_booking(request, booking_id):
    if request.user.profile.user_type != 'patient':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    booking = get_object_or_404(Booking, id=booking_id, patient=request.user)
    
    if booking.status == 'confirmed':
        with transaction.atomic():
            booking.cancel_booking()
        
        messages.success(request, 'Appointment cancelled successfully.')
        
        # Send cancellation email in background
        email_data = {
            'action': 'BOOKING_CANCELLED',
            'patient_email': request.user.email,
            'doctor_email': booking.slot.doctor.user.email,
            'patient_name': request.user.get_full_name(),
            'doctor_name': booking.slot.doctor.user.get_full_name(),
            'appointment_date': str(booking.slot.date),
            'appointment_time': f"{booking.slot.start_time.strftime('%H:%M')} - {booking.slot.end_time.strftime('%H:%M')}",
            'booking_id': booking.id
        }
        
        email_thread = threading.Thread(
            target=send_email_notification,
            args=(email_data,)
        )
        email_thread.daemon = True
        email_thread.start()
        
    else:
        messages.error(request, 'This appointment cannot be cancelled.')
    
    return redirect('patient_appointments')


@login_required
def booking_detail(request, booking_id):
    """View booking details"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user has permission to view this booking
    if request.user != booking.patient and request.user != booking.slot.doctor.user:
        messages.error(request, 'You do not have permission to view this booking.')
        return redirect('dashboard')
    
    context = {
        'booking': booking,
        'is_patient': request.user == booking.patient,
        'is_doctor': request.user == booking.slot.doctor.user,
    }
    return render(request, 'bookings/booking_detail.html', context)