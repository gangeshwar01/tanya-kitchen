# MySQL Database Setup Guide

This project has been configured to use MySQL instead of SQLite.

## Prerequisites

- MySQL Server installed and running on your system
- Python development headers (for mysqlclient)

### Installing MySQL Server

**Windows:**
- Download and install MySQL from: https://dev.mysql.com/downloads/installer/
- Or use XAMPP/WAMP which includes MySQL

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install mysql-server
sudo mysql_secure_installation
```

**macOS:**
```bash
brew install mysql
brew services start mysql
```

## Installation Steps

### 1. Install Python Dependencies

First, install the required MySQL client library:

```bash
pip install -r requirements.txt
```

**Note:** On Windows, you may need to install the Microsoft Visual C++ Build Tools or use a pre-compiled wheel.

**Alternative:** If `mysqlclient` installation fails, you can use `pymysql`:
```bash
pip install pymysql
```

Then add this to your `settings.py` imports:
```python
import pymysql
pymysql.install_as_MySQLdb()
```

### 2. Create MySQL Database

Connect to MySQL and create a database:

```bash
mysql -u root -p
```

Then run:
```sql
CREATE DATABASE messmet_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'messmet_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON messmet_db.* TO 'messmet_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Configure Environment Variables

**For Local Development:**

Create a `.env` file in the project root (or set environment variables):

```env
DB_NAME=messmet_db
DB_USER=messmet_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

**For Production (using DATABASE_URL):**

```env
DATABASE_URL=mysql://username:password@host:port/database_name
```

Example:
```env
DATABASE_URL=mysql://messmet_user:your_password@localhost:3306/messmet_db
```

### 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (if needed)

```bash
python manage.py createsuperuser
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

## Troubleshooting

### Issue: mysqlclient installation fails on Windows

**Solution:** Install the MySQL Connector:
1. Download from: https://dev.mysql.com/downloads/connector/python/
2. Or use `pymysql` as an alternative (see above)

### Issue: "Access denied for user"

**Solution:** Check your MySQL credentials and ensure the user has proper permissions:
```sql
GRANT ALL PRIVILEGES ON messmet_db.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;
```

### Issue: "Unknown character set"

**Solution:** Ensure your MySQL version supports utf8mb4 (MySQL 5.5.3+).

### Issue: Migration errors

**Solution:** If migrating from SQLite, you may need to drop and recreate tables:
```bash
python manage.py flush  # WARNING: This deletes all data
python manage.py migrate
```

## Data Migration from SQLite

If you need to migrate existing data from SQLite to MySQL:

1. Export data from SQLite:
```bash
python manage.py dumpdata > data.json
```

2. Update database settings to MySQL

3. Import data:
```bash
python manage.py loaddata data.json
```

## Render.com Deployment

For deployment on Render.com with MySQL:

1. Create a MySQL database on Render
2. Set the `DATABASE_URL` environment variable in Render dashboard
3. Deploy your application

The application will automatically use the MySQL database when `DATABASE_URL` is set.

