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

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from .forms import UserRegistrationForm, DoctorRegistrationForm, PatientRegistrationForm, LoginForm
from doctors.models import DoctorProfile
from patients.models import PatientProfile
from bookings.models import Booking
from django.utils import timezone
import requests
from django.conf import settings

def register(request):
    # Initialize forms
    user_form = UserRegistrationForm(request.POST or None)
    doctor_form = DoctorRegistrationForm(request.POST or None)
    patient_form = PatientRegistrationForm(request.POST or None)
    
    if request.method == 'POST':
        print("="*50)
        print("Registration attempt with data:")
        print(f"Username: {request.POST.get('username')}")
        print(f"Email: {request.POST.get('email')}")
        print(f"User Type: {request.POST.get('user_type')}")
        print("="*50)
        
        # Check if username already exists
        from django.contrib.auth.models import User
        username = request.POST.get('username')
        email = request.POST.get('email')
        
        if username and User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" is already taken. Please choose another one.')
            return render(request, 'accounts/register.html', {
                'user_form': user_form,
                'doctor_form': doctor_form,
                'patient_form': patient_form
            })
        
        if email and User.objects.filter(email=email).exists():
            messages.error(request, f'Email "{email}" is already registered. Please use another email or login.')
            return render(request, 'accounts/register.html', {
                'user_form': user_form,
                'doctor_form': doctor_form,
                'patient_form': patient_form
            })
        
        # Validate user form
        if user_form.is_valid():
            print("User form is valid")
            user_type = user_form.cleaned_data['user_type']
            
            # Check doctor-specific unique fields
            if user_type == 'doctor':
                license_number = request.POST.get('license_number')
                if license_number and DoctorProfile.objects.filter(license_number=license_number).exists():
                    messages.error(request, f'License number "{license_number}" is already registered. Please check and try again.')
                    return render(request, 'accounts/register.html', {
                        'user_form': user_form,
                        'doctor_form': doctor_form,
                        'patient_form': patient_form
                    })
                
                if not doctor_form.is_valid():
                    print("Doctor form errors:", doctor_form.errors)
                    for field, errors in doctor_form.errors.items():
                        for error in errors:
                            messages.error(request, f"{field}: {error}")
                    return render(request, 'accounts/register.html', {
                        'user_form': user_form,
                        'doctor_form': doctor_form,
                        'patient_form': patient_form
                    })
            
            # Check patient-specific fields
            elif user_type == 'patient':
                if not patient_form.is_valid():
                    print("Patient form errors:", patient_form.errors)
                    for field, errors in patient_form.errors.items():
                        for error in errors:
                            messages.error(request, f"{field}: {error}")
                    return render(request, 'accounts/register.html', {
                        'user_form': user_form,
                        'doctor_form': doctor_form,
                        'patient_form': patient_form
                    })
            
            # Create user
            try:
                user = user_form.save(commit=False)
                user.set_password(user_form.cleaned_data['password1'])
                user.save()
                
                # Update profile with user type
                user.profile.user_type = user_type
                user.profile.save()
                
                # Create doctor or patient profile
                if user_type == 'doctor':
                    doctor_profile = doctor_form.save(commit=False)
                    doctor_profile.user = user
                    doctor_profile.save()
                    messages.success(request, 'Doctor account created successfully! Please login.')
                    print(f"Doctor account created: {user.username}")
                    
                else:  # patient
                    patient_profile = patient_form.save(commit=False)
                    patient_profile.user = user
                    patient_profile.save()
                    messages.success(request, 'Patient account created successfully! Please login.')
                    print(f"Patient account created: {user.username}")
                
                # Try to send welcome email (don't block registration if it fails)
                try:
                    if settings.SERVERLESS_EMAIL_URL:
                        requests.post(settings.SERVERLESS_EMAIL_URL, json={
                            'action': 'SIGNUP_WELCOME',
                            'email': user.email,
                            'name': user.get_full_name(),
                            'user_type': user_type
                        }, timeout=2)
                except Exception as e:
                    print(f"Email notification failed (non-critical): {e}")
                
                return redirect('login')
                
            except IntegrityError as e:
                print(f"Database integrity error: {e}")
                messages.error(request, 'Registration failed due to duplicate information. Please check your details.')
                if user.pk:
                    user.delete()
                return render(request, 'accounts/register.html', {
                    'user_form': user_form,
                    'doctor_form': doctor_form,
                    'patient_form': patient_form
                })
                
        else:
            print("User form errors:", user_form.errors)
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
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