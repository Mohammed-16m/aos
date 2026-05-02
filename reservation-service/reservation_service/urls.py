from django.contrib import admin
from django.urls import path, include
from django.views.static import serve
import os

FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'frontend'
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/reservations/', include('reservations.urls')),
    path('reservations/dashboard/', serve, {
        'path': 'dashboard_client.html',
        'document_root': FRONTEND_DIR
    }),
    path('reservations/dashboard-admin/', serve, {
        'path': 'dashboard-admin.html',
        'document_root': FRONTEND_DIR
    }),
    path('reservations/creer/', serve, {
        'path': 'reservation.html',
        'document_root': FRONTEND_DIR
    }),
]