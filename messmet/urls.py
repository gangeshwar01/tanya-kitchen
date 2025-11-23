"""
URL configuration for messmet project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from messmetapp import views
from messmetapp.sitemap import StaticViewSitemap

sitemaps = {
    'static': StaticViewSitemap(),
}

urlpatterns = [
    # SEO URLs (must be early to avoid conflicts)
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django_sitemap'),
    # Export URLs (must be before admin URLs to avoid conflicts)
    path('admin/export/attendance.csv', views.lms_export_attendance_csv, name='lms_export_attendance_csv'),
    path('admin/export/users.csv', views.export_users_csv, name='export_users_csv'),
    path('admin/export/meal-feedback.csv', views.export_meal_feedback_csv, name='export_meal_feedback_csv'),
    # Admin URLs
    path('admin/', admin.site.urls),
    # App URLs
    path('', include('messmetapp.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
