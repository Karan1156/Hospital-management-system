import datetime
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from django.conf import settings

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    @staticmethod
    def get_auth_url(user, request):
        """Get Google OAuth URL"""
        try:
            # Get settings
            client_id = settings.GOOGLE_CLIENT_ID
            client_secret = settings.GOOGLE_CLIENT_SECRET
            redirect_uri = settings.GOOGLE_REDIRECT_URI
            
            print(f"\n🔍 DEBUG - Connecting with:")
            print(f"Client ID: {client_id[:15]}...")
            print(f"Redirect URI: {redirect_uri}")
            
            # Create flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri]
                    }
                },
                scopes=GoogleCalendarService.SCOPES
            )
            flow.redirect_uri = redirect_uri
            
            # Store user_id in session
            request.session['google_calendar_user_id'] = user.id
            
            # Generate auth URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            print(f"✅ Auth URL generated: {auth_url[:100]}...")
            return auth_url
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    @staticmethod
    def handle_oauth_callback(request):
        """Handle OAuth callback"""
        try:
            code = request.GET.get('code')
            user_id = request.session.get('google_calendar_user_id')
            
            if not code or not user_id:
                return False, "Missing code or user ID"
            
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
            
            # Get settings
            client_id = settings.GOOGLE_CLIENT_ID
            client_secret = settings.GOOGLE_CLIENT_SECRET
            redirect_uri = settings.GOOGLE_REDIRECT_URI
            
            # Create flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri]
                    }
                },
                scopes=GoogleCalendarService.SCOPES
            )
            flow.redirect_uri = redirect_uri
            
            # Exchange code for token
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Save token
            token_data = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            if user.profile.user_type == 'doctor':
                user.doctor_profile.google_calendar_token = str(token_data)
                user.doctor_profile.save()
            else:
                user.patient_profile.google_calendar_token = str(token_data)
                user.patient_profile.save()
            
            return True, "Calendar connected successfully!"
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def disconnect_user(user):
        """Disconnect calendar"""
        try:
            if user.profile.user_type == 'doctor':
                user.doctor_profile.google_calendar_token = ''
                user.doctor_profile.save()
            else:
                user.patient_profile.google_calendar_token = ''
                user.patient_profile.save()
            return True
        except:
            return False