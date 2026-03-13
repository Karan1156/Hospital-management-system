from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PatientProfile
from bookings.models import Booking

@login_required
def patient_dashboard(request):
    if request.user.profile.user_type != 'patient':
        return redirect('dashboard')
    
    patient_profile = PatientProfile.objects.get(user=request.user)
    upcoming_appointments = Booking.objects.filter(
        patient=request.user,
        status='confirmed'
    ).select_related('slot__doctor')[:5]
    
    return render(request, 'patients/dashboard.html', {
        'patient_profile': patient_profile,
        'upcoming_appointments': upcoming_appointments
    })

@login_required
def patient_profile(request):
    profile = PatientProfile.objects.get(user=request.user)
    
    if request.method == 'POST':
        profile.blood_group = request.POST.get('blood_group', profile.blood_group)
        profile.emergency_contact = request.POST.get('emergency_contact', profile.emergency_contact)
        profile.address = request.POST.get('address', profile.address)
        profile.medical_history = request.POST.get('medical_history', profile.medical_history)
        profile.save()
        messages.success(request, 'Profile updated!')
        return redirect('patient_profile')
    
    return render(request, 'patients/profile.html', {'profile': profile})

@login_required
def patient_appointments(request):
    appointments = Booking.objects.filter(
        patient=request.user
    ).select_related('slot__doctor').order_by('-slot__date')
    
    return render(request, 'patients/appointments.html', {'appointments': appointments})