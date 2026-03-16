from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DoctorProfile, AvailabilitySlot
from bookings.models import Booking
from .forms import AvailabilitySlotForm
from datetime import datetime,date


@login_required
def doctor_dashboard(request):
    if request.user.profile.user_type != 'doctor':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    try:
        doctor_profile = DoctorProfile.objects.get(user=request.user)
    except DoctorProfile.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('dashboard')
    
    # Get current date for filtering
    today = date.today()
    
    # Get available slots (future, not booked)
    upcoming_slots = AvailabilitySlot.objects.filter(
        doctor=doctor_profile,
        date__gte=today,
        is_booked=False
    ).order_by('date', 'start_time')
    
    # Get booked slots (future, booked)
    booked_slots = AvailabilitySlot.objects.filter(
        doctor=doctor_profile,
        date__gte=today,
        is_booked=True
    ).order_by('date', 'start_time')
    
    # Get upcoming appointments
    upcoming_appointments = Booking.objects.filter(
        slot__doctor=doctor_profile,
        status='confirmed',
        slot__date__gte=today
    ).select_related('patient', 'slot').order_by('slot__date', 'slot__start_time')[:5]
    
    # Get today's appointments count
    today_appointments = Booking.objects.filter(
        slot__doctor=doctor_profile,
        status='confirmed',
        slot__date=today
    ).count()
    
    # Get total patients (unique patients who have booked)
    total_patients = Booking.objects.filter(
        slot__doctor=doctor_profile,
        status='completed'
    ).values('patient').distinct().count()
    
    context = {
        'doctor_profile': doctor_profile,
        'upcoming_slots': upcoming_slots,
        'booked_slots': booked_slots,
        'upcoming_appointments': upcoming_appointments,
        'today_appointments': today_appointments,
        'total_patients': total_patients,
    }
    
    return render(request, 'doctors/dashboard.html', context)
@login_required
def add_availability(request):
    if request.user.profile.user_type != 'doctor':
        return redirect('dashboard')
    
    doctor_profile = DoctorProfile.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = AvailabilitySlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.doctor = doctor_profile
            slot.save()
            messages.success(request, 'Availability slot added!')
            return redirect('doctor_dashboard')
    else:
        form = AvailabilitySlotForm()
    
    return render(request, 'doctors/add_availability.html', {'form': form})

@login_required
def delete_availability(request, slot_id):
    if request.user.profile.user_type != 'doctor':
        return redirect('dashboard')
    
    slot = get_object_or_404(AvailabilitySlot, id=slot_id, doctor__user=request.user)
    
    if not slot.is_booked:
        slot.delete()
        messages.success(request, 'Slot deleted!')
    
    return redirect('doctor_dashboard')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import DoctorProfile, AvailabilitySlot
from bookings.models import Booking
from .forms import AvailabilitySlotForm
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@login_required
def add_availability(request):
    print("="*50)
    print("ADD AVAILABILITY VIEW CALLED")
    print(f"User: {request.user.username}")
    print(f"Is authenticated: {request.user.is_authenticated}")
    print(f"User type: {request.user.profile.user_type}")
    print(f"Request method: {request.method}")
    print("="*50)
    
    # Check if user is doctor
    if request.user.profile.user_type != 'doctor':
        print(f"ACCESS DENIED - User is {request.user.profile.user_type}, not doctor")
        messages.error(request, 'Access denied. Only doctors can add availability.')
        return redirect('dashboard')
    
    # Get doctor profile
    try:
        doctor_profile = DoctorProfile.objects.get(user=request.user)
        print(f"Doctor profile found: {doctor_profile}")
        print(f"Doctor specialization: {doctor_profile.specialization}")
        print(f"Doctor ID: {doctor_profile.id}")
    except DoctorProfile.DoesNotExist:
        print("ERROR: Doctor profile does not exist for this user!")
        messages.error(request, 'Doctor profile not found. Please contact support.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        print("\nPROCESSING POST REQUEST")
        print("POST data:", request.POST)
        
        # Create form instance with POST data
        form = AvailabilitySlotForm(request.POST)
        print("Form created")
        
        # Add doctor to form's initial data for validation
        form.doctor = doctor_profile
        
        if form.is_valid():
            print("FORM IS VALID")
            print("Cleaned data:", form.cleaned_data)
            
            # Create slot but don't save yet
            slot = form.save(commit=False)
            slot.doctor = doctor_profile
            slot.is_booked = False
            
            # Additional validation
            print(f"Slot date: {slot.date}")
            print(f"Start time: {slot.start_time}")
            print(f"End time: {slot.end_time}")
            
            # Check if slot is in the future
            slot_datetime = datetime.combine(slot.date, slot.start_time)
            if slot_datetime <= datetime.now():
                print("ERROR: Slot is in the past")
                messages.error(request, 'Cannot create slots in the past.')
                return render(request, 'doctors/add_availability.html', {'form': form})
            
            # Check for overlapping slots
            overlapping = AvailabilitySlot.objects.filter(
                doctor=doctor_profile,
                date=slot.date,
                start_time__lt=slot.end_time,
                end_time__gt=slot.start_time
            ).exists()
            
            if overlapping:
                print("ERROR: Overlapping slot exists")
                messages.error(request, 'This time slot overlaps with an existing slot.')
                return render(request, 'doctors/add_availability.html', {'form': form})
            
            # Save the slot
            try:
                slot.save()
                print(f"SLOT SAVED SUCCESSFULLY! ID: {slot.id}")
                messages.success(request, f'Availability slot added successfully for {slot.date} at {slot.start_time}!')
                return redirect('doctor_dashboard')
            except Exception as e:
                print(f"ERROR SAVING SLOT: {e}")
                messages.error(request, f'Error saving slot: {str(e)}')
                return render(request, 'doctors/add_availability.html', {'form': form})
        else:
            print("FORM IS INVALID")
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        print("\nGET REQUEST - Displaying empty form")
        form = AvailabilitySlotForm()
    
    return render(request, 'doctors/add_availability.html', {'form': form})