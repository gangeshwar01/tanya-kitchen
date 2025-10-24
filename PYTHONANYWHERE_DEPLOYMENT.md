# PythonAnywhere MySQL Deployment Guide

This guide will help you deploy your Django application on PythonAnywhere with MySQL database.

## Database Configuration

Based on your PythonAnywhere account:
- **Host:** `gangeshwar.mysql.pythonanywhere-services.com`
- **Username:** `gangeshwar`
- **Database:** `gangeshwar$tanya`
- **Port:** `3306`

## Deployment Steps

### 1. Upload Your Code to PythonAnywhere

1. Clone your repository or upload files via the Files tab in PythonAnywhere
2. Place your project in your home directory (e.g., `/home/gangeshwar/Tanya-Kitchen/`)

### 2. Set Up Virtual Environment

In the Bash console on PythonAnywhere:

```bash
cd /home/gangeshwar/Tanya-Kitchen
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** If `mysqlclient` installation fails, use `pymysql` instead:
```bash
pip install pymysql
```

Then add this to the top of your `messmet/wsgi.py`:
```python
import pymysql
pymysql.install_as_MySQLdb()
```

### 3. Configure Environment Variables

In PythonAnywhere's Web tab:

1. Go to your web app configuration
2. Scroll to "Environment variables"
3. Add the following variables:

```
DB_NAME=gangeshwar$tanya
DB_USER=gangeshwar
DB_PASSWORD=your_mysql_password
DB_HOST=gangeshwar.mysql.pythonanywhere-services.com
DB_PORT=3306
DEBUG=False
SECRET_KEY=your-secret-key-here
```

**Important:** 
- Replace `your_mysql_password` with your actual MySQL password
- Replace `your-secret-key-here` with a secure random string
- To find your MySQL password, check your PythonAnywhere account settings

### 4. Get Your MySQL Password

1. Go to the **Databases** tab in PythonAnywhere
2. Click on your database name (`gangeshwar$tanya`)
3. Your password might be displayed there, or check the PythonAnywhere documentation

### 5. Configure Static Files

In your PythonAnywhere web app settings:

1. Scroll to "Static files"
2. Add these mappings:
   - **URL:** `/static/` → **Directory:** `/home/gangeshwar/Tanya-Kitchen/staticfiles`
   - **URL:** `/media/` → **Directory:** `/home/gangeshwar/Tanya-Kitchen/media`

### 6. Configure WSGI File

1. In the Web tab, click on the WSGI file link
2. Update it to point to your Django application:

```python
import os
import sys

# Add your project directory to the Python path
path = '/home/gangeshwar/Tanya-Kitchen'
if path not in sys.path:
    sys.path.insert(0, path)

# Activate virtual environment
activate_this = '/home/gangeshwar/Tanya-Kitchen/venv/bin/activate_this.py'
with open(activate_this) as f:
    exec(f.read(), {'__file__': activate_this})

# Import Django WSGI application
os.environ['DJANGO_SETTINGS_MODULE'] = 'messmet.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 7. Run Migrations

In the Bash console:

```bash
cd /home/gangeshwar/Tanya-Kitchen
source venv/bin/activate
python manage.py migrate
```

### 8. Create Superuser (if needed)

```bash
python manage.py createsuperuser
```

### 9. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 10. Reload Your Web App

Click the **Reload** button in the Web tab.

## Troubleshooting

### MySQL Connection Error

If you get connection errors, check:
1. Database name includes the `$` symbol (no escaping needed in Django)
2. Password is correct in environment variables
3. Host address is exactly as shown

### mysqlclient Installation Error

**Alternative:** Use `pymysql`:
1. Install: `pip install pymysql`
2. Add to top of `messmet/wsgi.py`:
```python
import pymysql
pymysql.install_as_MySQLdb()
```

### Static Files Not Loading

Make sure:
1. Static files mapping is correct in Web tab
2. Ran `collectstatic` command
3. STATIC_ROOT is set correctly in settings.py

### Database "Unknown database" Error

Make sure the database name in environment variables matches exactly:
- Use: `gangeshwar$tanya` (not `gangeshwar\$tanya`)

### Allowed Hosts Error

Add your PythonAnywhere domain to ALLOWED_HOSTS in settings.py:
```python
ALLOWED_HOSTS = ['www.tanya-kitchen.casa', 'gangeshwar.pythonanywhere.com']
```

## Environment Variables Summary

For your PythonAnywhere web app, set these in "Environment variables":

```
DB_NAME=gangeshwar$tanya
DB_USER=gangeshwar
DB_PASSWORD=<your_password>
DB_HOST=gangeshwar.mysql.pythonanywhere-services.com
DB_PORT=3306
SECRET_KEY=<your_secret_key>
DEBUG=False
```

## Quick Reference

**Database Connection String Format:**
```
mysql://gangeshwar:password@gangeshwar.mysql.pythonanywhere-services.com:3306/gangeshwar$tanya
```

You can also use this format as `DATABASE_URL` environment variable if preferred.

