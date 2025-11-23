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
    
    # Page-specific SEO data with unique brand-focused titles
    seo_data = {
        'home': {
            'title': "Tanya's Kitchen | Dehradun's #1 Home-Cooked Meal Subscription Service | Fresh Daily Meals",
            'description': "Tanya's Kitchen is Dehradun's premier meal subscription service, delivering fresh, nutritious home-cooked meals daily. Choose from flexible breakfast, lunch, and dinner plans. Experience authentic Indian cuisine with Tanya's Kitchen - your trusted partner for healthy, affordable meals in Uttarakhand.",
            'keywords': "Tanya's Kitchen, Tanya Kitchen Dehradun, meal subscription Dehradun, home-cooked meals Uttarakhand, mess food service Dehradun, daily meal delivery, breakfast lunch dinner plans, affordable meal subscription, Indian food Dehradun, healthy meals Dehradun",
            'og_type': 'website',
        },
        'about': {
            'title': "About Tanya's Kitchen | Dehradun's Trusted Meal Provider Since 2024",
            'description': "Discover Tanya's Kitchen - Dehradun's leading meal subscription service. Learn about our mission to deliver fresh, nutritious home-cooked meals. Located in Imperial Heights, Dehradun, we serve authentic Indian cuisine with flexible meal plans for breakfast, lunch, and dinner.",
            'keywords': "about Tanya's Kitchen, Tanya Kitchen story, meal provider Dehradun, mess food service Uttarakhand, our mission, food service Dehradun",
            'og_type': 'website',
        },
        'menu': {
            'title': "Tanya's Kitchen Monthly Menu | Fresh Breakfast, Lunch & Dinner Plans | Dehradun",
            'description': "Explore Tanya's Kitchen monthly menu featuring diverse, nutritious meals. Our menu includes traditional Indian breakfast, wholesome lunch, and delicious dinner options. All meals are prepared fresh daily with locally sourced ingredients in Dehradun.",
            'keywords': "Tanya's Kitchen menu, monthly menu Dehradun, breakfast menu, lunch menu, dinner menu, meal plans menu, food menu Dehradun",
            'og_type': 'website',
        },
        'plans': {
            'title': "Tanya's Kitchen Subscription Plans | Affordable Meal Plans in Dehradun | Monthly, Quarterly & Yearly",
            'description': "Choose from Tanya's Kitchen flexible meal subscription plans. Affordable monthly, quarterly, and yearly options for breakfast, lunch, and dinner. Start your meal subscription today and enjoy fresh, home-cooked meals delivered daily in Dehradun.",
            'keywords': "Tanya's Kitchen plans, meal subscription plans Dehradun, affordable meal plans, monthly meal subscription, quarterly plans, yearly meal plans, breakfast lunch dinner plans",
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

