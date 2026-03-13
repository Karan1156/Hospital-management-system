import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from django.conf import settings

class GoogleCalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    @staticmethod
    def get_credentials(user):
        token_data = None
        if hasattr(user, 'doctor_profile'):
            token_data = user.doctor_profile.google_calendar_token
        elif hasattr(user, 'patient_profile'):
            token_data = user.patient_profile.google_calendar_token
        
        if not token_data:
            return None
        
        import ast
        return Credentials.from_authorized_user_info(ast.literal_eval(token_data))
    
    @staticmethod
    def save_credentials(user, credentials):
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
    
    @staticmethod
    def create_event(booking, user_type):
        user = booking.patient if user_type == 'patient' else booking.slot.doctor.user
        credentials = GoogleCalendarService.get_credentials(user)
        
        if not credentials:
            return None
        
        service = build('calendar', 'v3', credentials=credentials)
        
        summary = f"Appointment with Dr. {booking.slot.doctor.user.get_full_name()}" if user_type == 'patient' else f"Appointment with {booking.patient.get_full_name()}"
        
        start = datetime.datetime.combine(booking.slot.date, booking.slot.start_time)
        end = datetime.datetime.combine(booking.slot.date, booking.slot.end_time)
        
        event = {
            'summary': summary,
            'start': {'dateTime': start.isoformat(), 'timeZone': 'UTC'},
            'end': {'dateTime': end.isoformat(), 'timeZone': 'UTC'},
        }
        
        event = service.events().insert(calendarId='primary', body=event).execute()
        return event.get('id')