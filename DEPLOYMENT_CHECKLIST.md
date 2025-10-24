# PythonAnywhere Deployment Checklist

## ✅ Configuration Complete

Your project has been configured for MySQL on PythonAnywhere:

- ✅ Database settings updated in `settings.py`
- ✅ MySQL dependencies added to `requirements.txt`
- ✅ Configuration defaults set for PythonAnywhere environment

## 📋 Deployment Steps

### 1. On PythonAnywhere Console (Bash)

```bash
# Navigate to your project
cd /home/gangeshwar/Tanya-Kitchen

# Create and activate virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (if needed)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### 2. Configure Web App (PythonAnywhere Web Tab)

**Environment Variables:**
```
DB_NAME=gangeshwar$tanya
DB_USER=gangeshwar
DB_PASSWORD=<your_mysql_password>
DB_HOST=gangeshwar.mysql.pythonanywhere-services.com
DB_PORT=3306
SECRET_KEY=<generate_a_secure_key>
DEBUG=False
```

**Static Files Mapping:**
- URL: `/static/` → Directory: `/home/gangeshwar/Tanya-Kitchen/staticfiles`
- URL: `/media/` → Directory: `/home/gangeshwar/Tanya-Kitchen/media`

**WSGI Configuration:**
- Point to: `/home/gangeshwar/Tanya-Kitchen/messmet/wsgi.py`

### 3. Update ALLOWED_HOSTS

Make sure your PythonAnywhere domain is added in `settings.py`:
```python
ALLOWED_HOSTS = ['www.tanya-kitchen.casa', 'gangeshwar.pythonanywhere.com']
```

### 4. Reload Web App

Click the **Reload** button in the Web tab.

## 🔑 Important Notes

1. **MySQL Password:** Get your MySQL password from PythonAnywhere's Databases tab
2. **Database Name:** Must be exactly `gangeshwar$tanya` (with $, not escaped)
3. **Virtual Environment:** Always activate it before running Django commands
4. **Static Files:** Must run `collectstatic` after code changes

## 🐛 If mysqlclient Fails

Install `pymysql` instead:
```bash
pip install pymysql
```

Then add to the top of `messmet/wsgi.py`:
```python
import pymysql
pymysql.install_as_MySQLdb()
```

## 📚 Full Documentation

- See `PYTHONANYWHERE_DEPLOYMENT.md` for detailed instructions
- See `MYSQL_SETUP.md` for general MySQL setup information

