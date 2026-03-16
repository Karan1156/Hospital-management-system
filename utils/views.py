from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .google_calendar import GoogleCalendarService

@login_required
def connect_google_calendar(request):
    """Connect Google Calendar"""
    try:
        # Check credentials
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            messages.error(request, 'Google Calendar is not configured.')
            return redirect('dashboard')
        
        # Get auth URL
        auth_url = GoogleCalendarService.get_auth_url(request.user, request)
        
        if auth_url:
            return redirect(auth_url)
        else:
            messages.error(request, 'Failed to connect to Google.')
            return redirect('dashboard')
            
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('dashboard')

@login_required
def oauth2callback(request):
    """OAuth callback"""
    try:
        # Check for error
        if 'error' in request.GET:
            messages.error(request, f'Google error: {request.GET["error"]}')
            return redirect('dashboard')
        
        # Handle callback
        success, message = GoogleCalendarService.handle_oauth_callback(request)
        
        if success:
            messages.success(request, 'Calendar connected!')
        else:
            messages.error(request, f'Failed: {message}')
            
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('dashboard')

@login_required
def disconnect_google_calendar(request):
    """Disconnect calendar"""
    try:
        GoogleCalendarService.disconnect_user(request.user)
        messages.success(request, 'Calendar disconnected.')
    except:
        messages.error(request, 'Failed to disconnect.')
    
    return redirect('dashboard')