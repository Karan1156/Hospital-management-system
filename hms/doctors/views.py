from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DoctorProfile, AvailabilitySlot
from bookings.models import Booking
from .forms import AvailabilitySlotForm
from datetime import datetime

@login_required
def doctor_dashboard(request):
    if request.user.profile.user_type != 'doctor':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    doctor_profile = DoctorProfile.objects.get(user=request.user)
    
    upcoming_slots = AvailabilitySlot.objects.filter(
        doctor=doctor_profile,
        date__gte=datetime.now().date(),
        is_booked=False
    ).order_by('date', 'start_time')
    
    booked_slots = AvailabilitySlot.objects.filter(
        doctor=doctor_profile,
        is_booked=True,
        date__gte=datetime.now().date()
    ).order_by('date', 'start_time')
    
    context = {
        'doctor_profile': doctor_profile,
        'upcoming_slots': upcoming_slots,
        'booked_slots': booked_slots,
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