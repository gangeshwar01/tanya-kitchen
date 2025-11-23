from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """
    Sitemap for static pages that don't require authentication
    """
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        # Return list of URL names for public pages
        return [
            'home',
            'about',
            'menu',
            'plans_list',
            'login',
            'register',
            'meal_feedback',
            'visitor_payment',
        ]

    def location(self, item):
        return reverse(item)

