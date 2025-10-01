# create_superuser.py
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_portal.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')