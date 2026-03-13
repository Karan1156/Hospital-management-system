from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, DoctorRegistrationForm, PatientRegistrationForm, LoginForm
from doctors.models import DoctorProfile
from patients.models import PatientProfile
from bookings.models import Booking
from django.utils import timezone
import requests
from django.conf import settings

def home(request):
    return render(request, 'accounts/home.html')

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        
        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password1'])
            user.save()
            
            user_type = user_form.cleaned_data['user_type']
            user.profile.user_type = user_type
            user.profile.save()
            
            if user_type == 'doctor':
                doctor_form = DoctorRegistrationForm(request.POST)
                if doctor_form.is_valid():
                    doctor_profile = doctor_form.save(commit=False)
                    doctor_profile.user = user
                    doctor_profile.save()
                    messages.success(request, 'Doctor account created! Please login.')
                    
                    # Send welcome email
                    try:
                        requests.post(settings.SERVERLESS_EMAIL_URL, json={
                            'action': 'SIGNUP_WELCOME',
                            'email': user.email,
                            'name': user.get_full_name(),
                            'user_type': 'doctor'
                        }, timeout=2)
                    except:
                        pass
                        
            else:
                patient_form = PatientRegistrationForm(request.POST)
                if patient_form.is_valid():
                    patient_profile = patient_form.save(commit=False)
                    patient_profile.user = user
                    patient_profile.save()
                    messages.success(request, 'Patient account created! Please login.')
                    
                    try:
                        requests.post(settings.SERVERLESS_EMAIL_URL, json={
                            'action': 'SIGNUP_WELCOME',
                            'email': user.email,
                            'name': user.get_full_name(),
                            'user_type': 'patient'
                        }, timeout=2)
                    except:
                        pass
            
            return redirect('login')
    else:
        user_form = UserRegistrationForm()
        doctor_form = DoctorRegistrationForm()
        patient_form = PatientRegistrationForm()
    
    return render(request, 'accounts/register.html', {
        'user_form': user_form,
        'doctor_form': doctor_form,
        'patient_form': patient_form
    })

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    user = request.user
    context = {}
    
    if user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user=user)
        upcoming_appointments = Booking.objects.filter(
            slot__doctor=doctor_profile,
            status='confirmed',
            slot__date__gte=timezone.now().date()
        )[:5]
        
        context.update({
            'upcoming_appointments': upcoming_appointments,
            'doctor_profile': doctor_profile
        })
        return render(request, 'doctors/dashboard.html', context)
    
    else:
        upcoming_appointments = Booking.objects.filter(
            patient=user,
            status='confirmed',
            slot__date__gte=timezone.now().date()
        )[:5]
        
        context.update({
            'upcoming_appointments': upcoming_appointments
        })
        return render(request, 'patients/dashboard.html', context)