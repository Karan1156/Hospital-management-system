from django.urls import path
from . import views

urlpatterns = [
    path('book/', views.book_appointment, name='book_appointment'),
    path('get-time-slots/', views.get_time_slots, name='get_time_slots'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
]