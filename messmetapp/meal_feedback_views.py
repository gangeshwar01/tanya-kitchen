from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg
from django.utils import timezone
from .models import MealFeedback
from .forms import MealFeedbackForm


@login_required
def meal_feedback_view(request):
    """Display meal feedback form and handle submissions"""
    if request.user.is_staff:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = MealFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('meal_feedback')
    else:
        form = MealFeedbackForm()
    
    # Get user's recent feedback
    recent_feedback = MealFeedback.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    return render(request, 'meal_feedback.html', {
        'form': form,
        'recent_feedback': recent_feedback
    })


@login_required
def api_meal_feedback(request):
    """API endpoint for meal feedback"""
    if request.method == 'POST':
        form = MealFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            return JsonResponse({'success': True, 'message': 'Feedback submitted successfully'})
        else:
            return JsonResponse({'success': False, 'message': 'Please correct the errors', 'errors': form.errors})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def api_meal_feedback_list(request):
    """API endpoint to get meal feedback list"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Access denied'}, status=403)
    
    try:
        # Get filter parameters
        meal_type = request.GET.get('meal_type', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        rating_min = request.GET.get('rating_min', '')
        
        # Build query
        feedbacks = MealFeedback.objects.select_related('user').order_by('-created_at')
        
        if meal_type:
            feedbacks = feedbacks.filter(meal_type=meal_type)
        if date_from:
            feedbacks = feedbacks.filter(meal_date__gte=date_from)
        if date_to:
            feedbacks = feedbacks.filter(meal_date__lte=date_to)
        if rating_min:
            feedbacks = feedbacks.filter(rating__gte=int(rating_min))
        
        # Pagination
        page = int(request.GET.get('page', 1))
        per_page = 20
        start = (page - 1) * per_page
        end = start + per_page
        
        feedbacks_page = feedbacks[start:end]
        
        # Calculate statistics
        total_feedbacks = feedbacks.count()
        avg_rating = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0.0
        today_feedback = feedbacks.filter(created_at__date=timezone.localdate()).count()
        low_ratings = feedbacks.filter(rating__lte=2).count()
        
        # Prepare response data
        feedback_data = []
        for feedback in feedbacks_page:
            feedback_data.append({
                'id': feedback.id,
                'user': {
                    'username': feedback.user.username if not feedback.is_anonymous else 'Anonymous',
                    'full_name': feedback.user.full_name if not feedback.is_anonymous else 'Anonymous',
                    'profile_image': feedback.user.profile_image.url if feedback.user.profile_image and not feedback.is_anonymous else None
                },
                'meal_type': feedback.get_meal_type_display(),
                'meal_date': feedback.meal_date.strftime('%Y-%m-%d'),
                'rating': feedback.rating,
                'taste_rating': feedback.taste_rating,
                'quantity_rating': feedback.quantity_rating,
                'hygiene_rating': feedback.hygiene_rating,
                'overall_rating': feedback.overall_rating,
                'comments': feedback.comments,
                'is_anonymous': feedback.is_anonymous,
                'created_at': feedback.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'success': True,
            'feedbacks': feedback_data,
            'total': total_feedbacks,
            'avg_rating': round(avg_rating, 1),
            'today_feedback': today_feedback,
            'low_ratings': low_ratings,
            'page': page,
            'per_page': per_page,
            'has_next': end < total_feedbacks,
            'has_prev': page > 1
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)
