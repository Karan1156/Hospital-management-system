from django.urls import path
from . import views

urlpatterns = [
    path('connect/', views.connect_google_calendar, name='connect_calendar'),
    path('oauth2callback/', views.oauth2callback, name='oauth2callback'),
    path('disconnect/', views.disconnect_google_calendar, name='disconnect_calendar'),
]