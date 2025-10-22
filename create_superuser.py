#!/usr/bin/env python
"""
Django script to create or update superuser
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messmet.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_or_update_superuser():
    username = 'tanya'
    email = 'tanya@admin.com'
    password = '34tanya@admin'
    
    try:
        # Try to get existing user
        user = User.objects.get(username=username)
        print(f"Updating existing user: {username}")
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"Successfully updated superuser: {username}")
    except User.DoesNotExist:
        # Create new superuser
        print(f"Creating new superuser: {username}")
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            full_name='Tanya Admin'
        )
        print(f"Successfully created superuser: {username}")
    
    print(f"Username: {username}")
    print(f"Password: {password}")

if __name__ == '__main__':
    create_or_update_superuser()
