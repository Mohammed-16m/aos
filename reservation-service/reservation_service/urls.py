"""
URL configuration for reservation_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
import os
from django.views.static import serve

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/reservations/', include('reservations.urls')),
    path('dashboard-admin.html', serve, {'path': 'dashboard-admin.html', 'document_root': FRONTEND_DIR}),
    path('dashboard_client.html', serve, {'path': 'dashboard_client.html', 'document_root': FRONTEND_DIR}),
    path('reservation.html', serve, {'path': 'reservation.html', 'document_root': FRONTEND_DIR}),
    path('confirmation.html', serve, {'path': 'confirmation.html', 'document_root': FRONTEND_DIR}),
]