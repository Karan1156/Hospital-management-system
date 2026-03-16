from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .models import PatientProfile
from bookings.models import Booking
from doctors.models import DoctorProfile
from datetime import date
from django.contrib import messages

@login_required
def patient_dashboard(request):
    if request.user.profile.user_type != 'patient':
        return redirect('dashboard')
    
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        patient_profile = None
    
    # Get upcoming appointments
    upcoming_appointments = Booking.objects.filter(
        patient=request.user,
        status='confirmed',
        slot__date__gte=date.today()
    ).select_related('slot__doctor', 'slot__doctor__user').order_by('slot__date', 'slot__start_time')[:5]
    
    # Get available doctors
    doctors = DoctorProfile.objects.filter(is_available=True).select_related('user')[:6]
    
    context = {
        'patient_profile': patient_profile,
        'upcoming_appointments': upcoming_appointments,
        'doctors': doctors,
        'now': date.today(),
    }
    return render(request, 'patients/dashboard.html', context)

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