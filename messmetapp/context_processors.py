"""
Context processor for SEO meta tags and structured data
"""
from django.conf import settings


def seo_context(request):
    """
    Provides SEO-related context variables for templates
    """
    # Get the current path to determine page-specific SEO
    current_path = request.path
    
    # Base site information
    site_name = "Tanya's Kitchen"
    site_url = "https://www.tanya-kitchen.casa"
    default_description = "Your trusted partner for nutritious, home-style meals. We deliver fresh, healthy breakfast, lunch, and dinner options with flexible subscription plans that fit your lifestyle and budget."
    default_keywords = "mess food, meal subscription, home-cooked meals, Dehradun, Uttarakhand, breakfast, lunch, dinner, meal plans, food delivery"
    
    # Page-specific SEO data
    seo_data = {
        'home': {
            'title': "Tanya's Kitchen - Fresh Home-Cooked Meals | Meal Subscription Service",
            'description': default_description,
            'keywords': default_keywords,
            'og_type': 'website',
        },
        'about': {
            'title': "About Us - Tanya's Kitchen | Our Story & Mission",
            'description': "Learn about Tanya's Kitchen - your trusted partner for fresh, nutritious meals in Dehradun. Discover our mission, values, and commitment to quality home-cooked food.",
            'keywords': "about tanya kitchen, mess food service, meal provider Dehradun, our story",
            'og_type': 'website',
        },
        'menu': {
            'title': "Monthly Menu - Tanya's Kitchen | View Our Meal Plans",
            'description': "Browse our monthly menu featuring delicious breakfast, lunch, and dinner options. Fresh, nutritious meals prepared daily with love and care.",
            'keywords': "monthly menu, meal menu, food menu, breakfast menu, lunch menu, dinner menu",
            'og_type': 'website',
        },
        'plans': {
            'title': "Subscription Plans - Tanya's Kitchen | Flexible Meal Plans",
            'description': "Choose from our flexible meal subscription plans - monthly, quarterly, or yearly. Affordable pricing for breakfast, lunch, and dinner options.",
            'keywords': "meal subscription plans, food plans, pricing, meal packages, subscription service",
            'og_type': 'website',
        },
        'login': {
            'title': "Login - Tanya's Kitchen | Access Your Account",
            'description': "Login to your Tanya's Kitchen account to manage your meal subscription, view attendance, and access exclusive features.",
            'keywords': "login, account access, user login",
            'og_type': 'website',
        },
        'register': {
            'title': "Register - Tanya's Kitchen | Create Your Account",
            'description': "Create your Tanya's Kitchen account to start enjoying fresh, home-cooked meals. Sign up today and choose from our flexible meal plans.",
            'keywords': "register, sign up, create account, new user",
            'og_type': 'website',
        },
        'meal_feedback': {
            'title': "Meal Feedback - Tanya's Kitchen | Share Your Thoughts",
            'description': "Share your feedback about our meals to help us improve. Your opinion matters and helps us serve you better.",
            'keywords': "meal feedback, food review, customer feedback, rate meals",
            'og_type': 'website',
        },
    }
    
    # Determine which page we're on
    page_key = 'home'
    for key in seo_data.keys():
        if f'/{key}/' in current_path or (key == 'home' and current_path == '/'):
            page_key = key
            break
    
    # Get page-specific SEO or use defaults
    page_seo = seo_data.get(page_key, seo_data['home'])
    
    return {
        'seo_title': page_seo.get('title', f"{site_name} - Fresh Home-Cooked Meals"),
        'seo_description': page_seo.get('description', default_description),
        'seo_keywords': page_seo.get('keywords', default_keywords),
        'seo_og_type': page_seo.get('og_type', 'website'),
        'site_name': site_name,
        'site_url': site_url,
        'canonical_url': f"{site_url}{current_path}",
    }

