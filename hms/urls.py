from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('doctor/', include('doctors.urls')),
    path('patient/', include('patients.urls')),
    path('bookings/', include('bookings.urls')),
    path('calendar/', include('utils.urls')),  # THIS LINE IS CRITICAL
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)