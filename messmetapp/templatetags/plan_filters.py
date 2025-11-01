from django import template

register = template.Library()

@register.filter(name='format_features')
def format_features(features_text):
    """
    Format features text to display properly as a list.
    Handles both comma-separated and newline-separated features.
    """
    if not features_text:
        return ""
    
    # Split by newline first
    if '\n' in features_text:
        features = [f.strip() for f in features_text.split('\n') if f.strip()]
    # Otherwise split by comma
    elif ',' in features_text:
        features = [f.strip() for f in features_text.split(',') if f.strip()]
    else:
        features = [features_text.strip()]
    
    # Return HTML with bullet points
    return '\n'.join([f'• {feature}' for feature in features])

