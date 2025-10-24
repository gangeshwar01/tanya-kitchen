"""
WSGI config for messmet project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

# Set environment variables for PythonAnywhere
# Update these values with your actual credentials
os.environ['DB_NAME'] = 'gangeshwar$tanya'
os.environ['DB_USER'] = 'gangeshwar'
os.environ['DB_PASSWORD'] = 'YOUR_MYSQL_PASSWORD_HERE'  # Replace with your actual password
os.environ['DB_HOST'] = 'gangeshwar.mysql.pythonanywhere-services.com'
os.environ['DB_PORT'] = '3306'
os.environ['SECRET_KEY'] = 'YOUR_SECRET_KEY_HERE'  # Replace with a secure random string
os.environ['DEBUG'] = 'False'

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messmet.settings')

application = get_wsgi_application()
