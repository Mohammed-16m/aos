import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')
django.setup()

from users.models import User

# Créer ADMIN
if not User.objects.filter(email='admin@gmail.com').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@gmail.com',
        password='admin123',
        role='ADMIN'
    )
    print('✅ Admin créé')
else:
    print('ℹ️ Admin déjà existant')