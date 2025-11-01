from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Max, Q
from django.utils import timezone
import csv
from datetime import timedelta, datetime
from .models import SubscriptionPlan, User, UserSubscription, Attendance, MonthlyMenu, PaymentProof, MealFeedback, VisitorPayment, VisitorFeedback, PopupNotice, StaffImage, OwnerImage
from .meal_feedback_views import meal_feedback_view, api_meal_feedback, api_meal_feedback_list
from .forms import RegisterForm, ProfileForm, MonthlyMenuForm, CarouselImageForm, MealFeedbackForm, VisitorPaymentForm, VisitorFeedbackForm
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    PaymentProofSerializer,
    AttendanceSerializer,
    MonthlyMenuSerializer,
    PaymentConfigSerializer,
    FeedbackSerializer,
)
from django.utils import timezone
from django.http import HttpResponse
import csv


def get_active_notices_for_user(user):
    """
    Get all currently active popup notices for a given user
    based on datetime and target audience
    """
    now = timezone.now()
    
    # Get notices that are active and within the datetime range
    notices = PopupNotice.objects.filter(
        is_active=True,
        start_datetime__lte=now,
        end_datetime__gte=now
    )
    
    # Filter based on target audience
    if user.is_authenticated:
        # Check if user has active subscription
        has_active_sub = UserSubscription.objects.filter(user=user, active=True).exists()
        
        # Filter notices based on target audience
        filtered_notices = []
        for notice in notices:
            if notice.target_audience == PopupNotice.TARGET_ALL_USERS:
                filtered_notices.append(notice)
            elif notice.target_audience == PopupNotice.TARGET_HOSTELLERS and user.hostel_status == User.HOSTEL_STATUS_HOSTELLER:
                filtered_notices.append(notice)
            elif notice.target_audience == PopupNotice.TARGET_NON_HOSTELLERS and user.hostel_status == User.HOSTEL_STATUS_NON_HOSTELLER:
                filtered_notices.append(notice)
            elif notice.target_audience == PopupNotice.TARGET_ACTIVE_SUBSCRIBERS and has_active_sub:
                filtered_notices.append(notice)
        
        return filtered_notices
    else:
        # For anonymous users, only show "all users" notices
        return notices.filter(target_audience=PopupNotice.TARGET_ALL_USERS)


def home(request):
    plans = SubscriptionPlan.objects.filter(is_active=True)
    from .models import CarouselImage, FoodImage
    carousel_images = CarouselImage.objects.filter(is_active=True).order_by('order', '-created_at')
    food_images = FoodImage.objects.filter(is_active=True).order_by('order', '-created_at')
    
    # Get attendance data for authenticated users
    attendance_data = None
    if request.user.is_authenticated:
        # Get user's active subscription
        active_sub = UserSubscription.objects.filter(user=request.user, active=True).order_by('-created_at').first()
        
        # Get allowed meals from subscription
        allowed_meals = []
        if active_sub:
            allowed_meals = active_sub.plan.included_meals
        
        # Get today's attendance for this user
        today = timezone.localdate()
        today_attendance = Attendance.objects.filter(user=request.user, date=today)
        marked_meals = [att.meal_type for att in today_attendance]
        
        attendance_data = {
            'active_sub': active_sub,
            'allowed_meals': allowed_meals,
            'marked_meals': marked_meals,
        }
    
    # Get active popup notices for the current user
    active_notices = get_active_notices_for_user(request.user)
    
    # Serialize notices to JSON format
    import json
    notices_json = json.dumps([{
        'id': notice.id,
        'title': notice.title,
        'message': notice.message,
        'priority': notice.priority,
        'start_datetime': notice.start_datetime.isoformat(),
        'end_datetime': notice.end_datetime.isoformat(),
    } for notice in active_notices])
    
    # Get payment config for visitor payment section
    from .models import PaymentConfig
    paycfg = PaymentConfig.objects.first()
    
    return render(request, 'home.html', {
        "plans": plans, 
        "carousel_images": carousel_images,
        "food_images": food_images,
        "attendance_data": attendance_data,
        "popup_notices": notices_json,
        "paycfg": paycfg
    })


@require_http_methods(["GET", "POST"])
def visitor_payment(request):
    if request.method == "POST":
        form = VisitorPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks! Payment uploaded.")
            return redirect('home')
        messages.error(request, "Please correct the errors below.")
    else:
        form = VisitorPaymentForm()
    return render(request, 'lms/payments.html', {"visitor_form": form})


@require_http_methods(["POST"])
def visitor_feedback_api(request):
    form = VisitorFeedbackForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "errors": form.errors}, status=400)


def about_view(request):
    staff_members = StaffImage.objects.filter(is_active=True).order_by('-order', '-created_at')
    owners = OwnerImage.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'about.html', {
        'staff_members': staff_members,
        'owners': owners
    })




def menu_view(request):
    """Display the current monthly menu"""
    today = timezone.localdate()
    current_menu = MonthlyMenu.objects.filter(month=today.month, year=today.year).first()
    return render(request, 'menu.html', {"current_menu": current_menu})


@login_required
def attendance_view(request):
    """Display attendance marking page for authenticated users"""
    # Redirect admin users to dashboard
    if request.user.is_staff:
        return redirect('dashboard')
    # Get user's active subscription
    active_sub = UserSubscription.objects.filter(user=request.user, active=True).order_by('-created_at').first()
    
    # Get allowed meals from subscription
    allowed_meals = []
    if active_sub:
        allowed_meals = active_sub.plan.included_meals
    
    # Get today's attendance for this user
    today = timezone.localdate()
    today_attendance = Attendance.objects.filter(user=request.user, date=today)
    marked_meals = [att.meal_type for att in today_attendance]
    
    # Get recent attendance history
    recent_attendance = Attendance.objects.filter(user=request.user).order_by('-date', '-marked_at')[:10]
    
    # Get current time in Kolkata timezone
    import pytz
    kolkata_tz = pytz.timezone('Asia/Kolkata')
    current_time = timezone.now().astimezone(kolkata_tz)
    
    return render(request, 'attendance.html', {
        'active_sub': active_sub,
        'allowed_meals': allowed_meals,
        'marked_meals': marked_meals,
        'recent_attendance': recent_attendance,
        'today': today,
        'current_time': current_time,
    })


@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["GET", "POST"])
def dashboard(request):
    # Handle different admin actions based on form submission
    if request.method == "POST":
        action = request.POST.get("action")
        
        # Handle menu upload
        if action == "upload_menu":
            menu_form = MonthlyMenuForm(request.POST, request.FILES)
            if menu_form.is_valid():
                month = menu_form.cleaned_data['month']
                year = menu_form.cleaned_data['year']
                existing_menu = MonthlyMenu.objects.filter(month=month, year=year).first()
                
                if existing_menu:
                    existing_menu.file = menu_form.cleaned_data.get('file') or existing_menu.file
                    existing_menu.image = menu_form.cleaned_data.get('image') or existing_menu.image
                    existing_menu.text = menu_form.cleaned_data.get('text') or existing_menu.text
                    existing_menu.save()
                    messages.success(request, f"Menu for {month:02d}/{year} updated successfully!")
                else:
                    menu_form.save()
                    messages.success(request, f"Menu for {month:02d}/{year} uploaded successfully!")
            else:
                messages.error(request, "Please correct the errors in the menu form.")
        
        # Handle plan creation
        elif action == "add_plan":
            title = request.POST.get("title", "").strip()
            price = request.POST.get("price")
            billing_period = request.POST.get("billing_period", "monthly")
            features = request.POST.get("features", "")
            included_meals = request.POST.getlist("included_meals")
            is_active = bool(request.POST.get("is_active"))
            if not title or not price:
                messages.error(request, "Title and price are required.")
            else:
                try:
                    SubscriptionPlan.objects.create(
                        title=title,
                        price=price,
                        billing_period=billing_period,
                        features=features,
                        included_meals=included_meals,
                        is_active=is_active,
                    )
                    messages.success(request, "Plan added successfully!")
                except Exception as e:
                    messages.error(request, f"Failed to add plan: {e}")
        
        # Handle carousel image management
        elif action == "add_carousel":
            carousel_form = CarouselImageForm(request.POST, request.FILES)
            if carousel_form.is_valid():
                carousel_form.save()
                messages.success(request, "Carousel image added successfully!")
            else:
                messages.error(request, "Please correct the errors in the carousel form.")
        
        elif action == "delete_carousel":
            carousel_id = request.POST.get("carousel_id")
            try:
                from .models import CarouselImage
                carousel = CarouselImage.objects.get(pk=carousel_id)
                carousel.delete()
                messages.success(request, "Carousel image deleted successfully!")
            except CarouselImage.DoesNotExist:
                messages.error(request, "Carousel image not found")
        
        # Handle food gallery image management
        elif action == "add_food_image":
            title = request.POST.get("title", "").strip()
            image = request.FILES.get("image")
            description = request.POST.get("description", "").strip()
            meal_type = request.POST.get("meal_type", "").strip()
            order = int(request.POST.get("order", 0))
            is_active = bool(request.POST.get("is_active"))
            
            if not title or not image:
                messages.error(request, "Title and image are required.")
            else:
                try:
                    from .models import FoodImage
                    FoodImage.objects.create(
                        title=title,
                        image=image,
                        description=description,
                        meal_type=meal_type or None,
                        order=order,
                        is_active=is_active,
                    )
                    messages.success(request, "Food image added successfully!")
                except Exception as e:
                    messages.error(request, f"Failed to add food image: {e}")
        
        elif action == "delete_food_image":
            food_image_id = request.POST.get("food_image_id")
            try:
                from .models import FoodImage
                food_image = FoodImage.objects.get(pk=food_image_id)
                food_image.delete()
                messages.success(request, "Food image deleted successfully!")
            except FoodImage.DoesNotExist:
                messages.error(request, "Food image not found")
        
        # Handle payment configuration save
        elif action == "save_payment_config":
            from .models import PaymentConfig
            paycfg, created = PaymentConfig.objects.get_or_create(pk=1)
            
            # Update fields if provided
            if request.POST.get('upi_id'):
                paycfg.upi_id = request.POST.get('upi_id')
            
            if request.FILES.get('gpay_qr'):
                paycfg.gpay_qr = request.FILES.get('gpay_qr')
            
            if request.FILES.get('phonepe_qr'):
                paycfg.phonepe_qr = request.FILES.get('phonepe_qr')
            
            paycfg.save()
            messages.success(request, "Payment configuration saved successfully!")
        
        # Handle payment approval/rejection
        elif action in ["approve_payment", "reject_payment", "delete_visitor_payment", "delete_payment_proof", "delete_plan", "delete_visitor_feedback"]:
            payment_id = request.POST.get("payment_id")
            try:
                if action == "delete_visitor_payment":
                    vp_id = request.POST.get("vp_id")
                    from .models import VisitorPayment as VP
                    VP.objects.filter(pk=vp_id).delete()
                    messages.success(request, "Visitor payment deleted.")
                elif action == "delete_payment_proof":
                    PaymentProof.objects.filter(pk=payment_id).delete()
                    messages.success(request, "Payment proof deleted.")
                elif action == "delete_plan":
                    plan_id = request.POST.get("plan_id")
                    from .models import SubscriptionPlan as SP
                    try:
                        plan = SP.objects.get(pk=plan_id)
                        plan_title = plan.title
                        plan.delete()  # This will now cascade delete related UserSubscription and PaymentProof records
                        messages.success(request, f"Plan '{plan_title}' and all related records deleted successfully.")
                    except Exception as e:
                        messages.error(request, f"Cannot delete plan: {e}")
                elif action == "delete_visitor_feedback":
                    vf_id = request.POST.get("vf_id")
                    from .models import VisitorFeedback as VF
                    VF.objects.filter(pk=vf_id).delete()
                    messages.success(request, "Visitor feedback deleted.")
                else:
                    proof = PaymentProof.objects.select_related("subscription_plan", "user").get(pk=payment_id)
                    if action == "approve_payment" and proof.status != "approved":
                        proof.status = "approved"
                        proof.reviewed_by = request.user
                        proof.reviewed_at = timezone.now()
                        proof.txn_id = proof.txn_id or f"TXN-{proof.pk}-{int(proof.reviewed_at.timestamp())}"
                        proof.save()
                        start = timezone.localdate()
                        end = proof.subscription_plan.compute_end_date(start)
                        # Deactivate any existing active subscriptions for this user before creating a new one
                        UserSubscription.objects.filter(user=proof.user, active=True).update(active=False)
                        UserSubscription.objects.create(user=proof.user, plan=proof.subscription_plan, start_date=start, end_date=end, active=True)
                        messages.success(request, "Payment approved and subscription activated.")
                    elif action == "reject_payment" and proof.status != "rejected":
                        proof.status = "rejected"
                        proof.reviewed_by = request.user
                        proof.reviewed_at = timezone.now()
                        proof.save()
                        messages.info(request, "Payment rejected.")
            except PaymentProof.DoesNotExist:
                messages.error(request, "Payment not found")
            
            # Redirect back to dashboard with appropriate section based on action
            from django.http import HttpResponseRedirect
            if action == "delete_plan":
                return HttpResponseRedirect(reverse('dashboard') + '?section=plans')
            else:
                return HttpResponseRedirect(reverse('dashboard') + '?section=payments')
        
        return redirect('dashboard')
    
    # Get all data for the unified admin dashboard
    today_date = timezone.localdate()
    stats = {
        # Exclude staff/admin from user-facing counts
        "users": User.objects.filter(is_staff=False).count(),
        # Count users with at least one active subscription (distinct users)
        "active_subs": UserSubscription.objects.filter(active=True, user__is_staff=False).values('user').distinct().count(),
        "pending_payments": PaymentProof.objects.filter(status="pending").count(),
        # Count distinct users who attended today, not total meal records
        "today_attendance": Attendance.objects.filter(date=today_date, user__is_staff=False).values('user').distinct().count(),
    }
    
    # Get pending payments
    pending_payments = PaymentProof.objects.filter(status="pending").order_by("-submitted_at")[:10]
    # Visitor payments filter
    visitor_period = request.GET.get("visitor_period", "")
    visitor_payments = VisitorPayment.objects.all().order_by("-created_at")
    if visitor_period == "today":
        visitor_payments = visitor_payments.filter(created_at__date=timezone.localdate())
    elif visitor_period == "week":
        start_week = timezone.now() - timedelta(days=7)
        visitor_payments = visitor_payments.filter(created_at__gte=start_week)
    elif visitor_period == "month":
        start_month = timezone.now() - timedelta(days=30)
        visitor_payments = visitor_payments.filter(created_at__gte=start_month)
    
    # Get all subscription plans
    plans = SubscriptionPlan.objects.all().order_by('-is_active', 'title')
    
    # Get current menu
    today = timezone.localdate()
    current_menu = MonthlyMenu.objects.filter(month=today.month, year=today.year).first()
    
    # Get payment config
    from .models import PaymentConfig
    paycfg = PaymentConfig.objects.first()
    
    # Get feedbacks
    from .models import Feedback
    recent_feedbacks = Feedback.objects.all().order_by('-created_at')[:5]
    # Visitor feedbacks (latest 10)
    visitor_feedbacks = VisitorFeedback.objects.all().order_by('-created_at')[:10]
    
    # Get carousel images
    from .models import CarouselImage
    carousel_images = CarouselImage.objects.filter(is_active=True).order_by('order', '-created_at')
    
    # Get food gallery images
    from .models import FoodImage
    food_images = FoodImage.objects.filter(is_active=True).order_by('order', '-created_at')
    
    # Initialize forms
    menu_form = MonthlyMenuForm()
    carousel_form = CarouselImageForm()
    
    # Get current time in Kolkata timezone
    import pytz
    kolkata_tz = pytz.timezone('Asia/Kolkata')
    current_time = timezone.now().astimezone(kolkata_tz)
    
    # LMS Data - Get all users with their attendance info
    all_users_qs = User.objects.filter(is_staff=False)
    # Optional hostel_status filter
    hostel_status = request.GET.get("hostel_status")
    if hostel_status == "all":
        hostel_status = ""
    if hostel_status in [User.HOSTEL_STATUS_HOSTELLER, User.HOSTEL_STATUS_NON_HOSTELLER]:
        all_users_qs = all_users_qs.filter(hostel_status=hostel_status)

    all_users = all_users_qs.annotate(
        total_attendance_count=Count('attendances'),
        last_attendance=Max('attendances__marked_at')
    ).order_by('username')
    
    # Add today's attendance status for each user
    today = timezone.localdate()
    for user in all_users:
        user.today_attendance = Attendance.objects.filter(
            user=user, 
            date=today
        ).first()
        user.active_subscriptions = UserSubscription.objects.filter(user=user, active=True)
    
    # Calculate attendance statistics
    # Count distinct users who attended today, not total meal records
    today_attendance_count = Attendance.objects.filter(date=today, user__is_staff=False).values('user').distinct().count()
    total_users = all_users.count()
    absent_today_count = total_users - today_attendance_count
    attendance_rate = round((today_attendance_count / total_users * 100) if total_users > 0 else 0, 1)
    
    # User Management Statistics (distinct users with active subs, exclude staff)
    active_subscriptions_count = (
        UserSubscription.objects.filter(active=True, user__is_staff=False)
        .values('user').distinct().count()
    )
    no_subscriptions_count = User.objects.filter(is_staff=False).exclude(
        subscriptions__active=True
    ).count()
    
    # New users this month
    current_month = datetime.now().month
    current_year = datetime.now().year
    new_users_count = User.objects.filter(
        date_joined__month=current_month,
        date_joined__year=current_year
    ).count()
    
    return render(request, 'admin_dashboard.html', {
        "stats": stats,
        "pending_payments": pending_payments,
        "plans": plans,
        "current_menu": current_menu,
        "paycfg": paycfg,
        "recent_feedbacks": recent_feedbacks,
        "visitor_feedbacks": visitor_feedbacks,
        "menu_form": menu_form,
        "carousel_images": carousel_images,
        "carousel_form": carousel_form,
        "food_images": food_images,
        "current_time": current_time,
        "visitor_payments": visitor_payments,
        # LMS Data
        "all_users": all_users,
        "selected_hostel_status": hostel_status or "",
        "today_attendance_count": today_attendance_count,
        "absent_today_count": absent_today_count,
        "attendance_rate": attendance_rate,
        # User Management Data
        "active_subscriptions_count": active_subscriptions_count,
        "no_subscriptions_count": no_subscriptions_count,
        "new_users_count": new_users_count,
    })


@require_http_methods(["GET", "POST"])
def plans_list(request):
    # Redirect admin users to dashboard
    if request.user.is_staff:
        return redirect('dashboard')
    
    if request.method == "POST" and request.user.is_staff:
        # Handle plan creation from Plans page
        action = request.POST.get("action")
        if action == "add_plan":
            title = request.POST.get("title", "").strip()
            price = request.POST.get("price")
            billing_period = request.POST.get("billing_period", "monthly")
            features = request.POST.get("features", "")
            included_meals = request.POST.getlist("included_meals")
            is_active = bool(request.POST.get("is_active"))
            
            if not title or not price:
                messages.error(request, "Title and price are required.")
            else:
                try:
                    SubscriptionPlan.objects.create(
                        title=title,
                        price=price,
                        billing_period=billing_period,
                        features=features,
                        included_meals=included_meals,
                        is_active=is_active,
                    )
                    messages.success(request, "Plan added successfully!")
                except Exception as e:
                    messages.error(request, f"Failed to add plan: {e}")
            return redirect('plans_list')
    
    # Show all plans for admins, only active plans for regular users
    if request.user.is_staff:
        plans = SubscriptionPlan.objects.all().order_by('-is_active', 'title')
    else:
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('title')
    # Determine user's current active subscription plan, if any
    active_sub = None
    if request.user.is_authenticated and not request.user.is_staff:
        active_sub = (
            UserSubscription.objects.filter(user=request.user, active=True)
            .order_by('-created_at')
            .first()
        )
    
    return render(request, 'plans.html', {"plans": plans, "active_sub": active_sub})

@login_required
def plan_buy(request, pk: int):
    # Redirect admin users to dashboard
    if request.user.is_staff:
        return redirect('dashboard')
    
    from django.shortcuts import get_object_or_404
    plan = get_object_or_404(SubscriptionPlan, pk=pk, is_active=True)
    from .models import PaymentConfig
    paycfg = PaymentConfig.objects.first()
    return render(request, 'plan_buy.html', {"plan": plan, "paycfg": paycfg})


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to Tanya's Kitchen!")
            return redirect('home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()
    return render(request, 'register.html', {"form": form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        messages.error(request, "Invalid credentials.")
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('profile')
        messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'subscription_detail.html', {"form": form})


# --------- APIs ---------

@api_view(["GET"])
@permission_classes([AllowAny])
def api_plans(request):
    plans = SubscriptionPlan.objects.filter(is_active=True)
    return Response(SubscriptionPlanSerializer(plans, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_my_subscription(request):
    sub = (
        UserSubscription.objects.filter(user=request.user, active=True)
        .order_by("-created_at")
        .first()
    )
    if not sub:
        return Response({"detail": "No active subscription"}, status=404)
    return Response(UserSubscriptionSerializer(sub).data)


def _user_allowed_meals(user):
    sub = (
        UserSubscription.objects.filter(user=user, active=True)
        .order_by("-created_at")
        .first()
    )
    return set(sub.plan.included_meals) if sub else set()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_mark_attendance(request):
    meal = request.data.get("meal_type")
    today = timezone.localdate()
    allowed = _user_allowed_meals(request.user)
    if meal not in allowed:
        return Response({"detail": "Meal not allowed for your plan"}, status=403)
    # prevent duplicates by unique constraint
    att, created = Attendance.objects.get_or_create(user=request.user, date=today, meal_type=meal)
    if not created:
        return Response({"detail": "Already marked"}, status=409)
    return Response(AttendanceSerializer(att).data, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_attendance_list(request):
    qs = Attendance.objects.filter(user=request.user).order_by("-date", "-marked_at")
    return Response(AttendanceSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_current_menu(request):
    today = timezone.localdate()
    menu = MonthlyMenu.objects.filter(month=today.month, year=today.year).first()
    if not menu:
        return Response({"detail": "No menu uploaded"}, status=404)
    return Response(MonthlyMenuSerializer(menu).data)


@api_view(["POST", "GET"])
@permission_classes([IsAuthenticated])
def api_payment_proofs(request):
    if request.method == "POST":
        serializer = PaymentProofSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            obj = serializer.save()
            return Response(PaymentProofSerializer(obj).data, status=201)
        return Response(serializer.errors, status=400)
    # GET
    qs = request.user.payment_proofs.order_by("-submitted_at")
    return Response(PaymentProofSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_payment_config(request):
    from .models import PaymentConfig
    cfg = PaymentConfig.objects.first()
    if not cfg:
        return Response({"detail": "No payment config"}, status=404)
    return Response(PaymentConfigSerializer(cfg).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_feedback(request):
    serializer = FeedbackSerializer(data=request.data)
    if serializer.is_valid():
        obj = serializer.save(user=request.user)
        return Response(FeedbackSerializer(obj).data, status=201)
    return Response(serializer.errors, status=400)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_active_notices(request):
    """
    Get all currently active popup notices for the requesting user
    """
    notices = get_active_notices_for_user(request.user)
    
    notices_data = []
    for notice in notices:
        notices_data.append({
            'id': notice.id,
            'title': notice.title,
            'message': notice.message,
            'priority': notice.priority,
            'start_datetime': notice.start_datetime.isoformat(),
            'end_datetime': notice.end_datetime.isoformat(),
        })
    
    return Response(notices_data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_notices_list(request):
    """
    Get all popup notices for admin dashboard
    """
    if not request.user.is_staff:
        return Response({'success': False, 'message': 'Permission denied'}, status=403)
    
    notices = PopupNotice.objects.all().order_by('-priority', '-created_at')
    
    notices_data = []
    for notice in notices:
        notices_data.append({
            'id': notice.id,
            'title': notice.title,
            'message': notice.message,
            'start_datetime': notice.start_datetime.isoformat(),
            'end_datetime': notice.end_datetime.isoformat(),
            'target_audience': notice.target_audience,
            'is_active': notice.is_active,
            'priority': notice.priority,
            'created_by': notice.created_by.username if notice.created_by else None,
        })
    
    return Response(notices_data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_notice_create(request):
    """
    Create a new popup notice
    """
    if not request.user.is_staff:
        return Response({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        data = request.data
        notice = PopupNotice.objects.create(
            title=data.get('title'),
            message=data.get('message'),
            start_datetime=data.get('start_datetime'),
            end_datetime=data.get('end_datetime'),
            target_audience=data.get('target_audience', 'all'),
            priority=data.get('priority', 0),
            is_active=data.get('is_active', True),
            created_by=request.user
        )
        return Response({'success': True, 'id': notice.id, 'message': 'Notice created successfully'})
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_notice_update(request, notice_id):
    """
    Update an existing popup notice
    """
    if not request.user.is_staff:
        return Response({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        notice = PopupNotice.objects.get(id=notice_id)
        data = request.data
        
        notice.title = data.get('title', notice.title)
        notice.message = data.get('message', notice.message)
        notice.start_datetime = data.get('start_datetime', notice.start_datetime)
        notice.end_datetime = data.get('end_datetime', notice.end_datetime)
        notice.target_audience = data.get('target_audience', notice.target_audience)
        notice.priority = data.get('priority', notice.priority)
        notice.is_active = data.get('is_active', notice.is_active)
        notice.save()
        
        return Response({'success': True, 'message': 'Notice updated successfully'})
    except PopupNotice.DoesNotExist:
        return Response({'success': False, 'message': 'Notice not found'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_notice_delete(request, notice_id):
    """
    Delete a popup notice
    """
    if not request.user.is_staff:
        return Response({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        notice = PopupNotice.objects.get(id=notice_id)
        notice.delete()
        return Response({'success': True, 'message': 'Notice deleted successfully'})
    except PopupNotice.DoesNotExist:
        return Response({'success': False, 'message': 'Notice not found'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=400)


# Staff & Owner API Endpoints
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_staff_list(request):
    """Get all staff members for admin dashboard"""
    if not request.user.is_staff:
        return Response({'success': False, 'message': 'Permission denied'}, status=403)
    
    staff = StaffImage.objects.all().order_by('-order', '-created_at')
    staff_data = []
    for s in staff:
        staff_data.append({
            'id': s.id,
            'name': s.name,
            'role': s.role,
            'description': s.description,
            'image': s.image.url if s.image else None,
            'is_active': s.is_active,
            'order': s.order,
        })
    return Response(staff_data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_staff_create(request):
    """Create a new staff member"""
    if not request.user.is_staff:
        return Response({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        staff = StaffImage.objects.create(
            name=request.POST.get('name'),
            role=request.POST.get('role', ''),
            description=request.POST.get('description', ''),
            image=request.FILES.get('image'),
            order=int(request.POST.get('order', 0)),
            is_active=request.POST.get('is_active') == 'true'
        )
        return Response({'success': True, 'id': staff.id, 'message': 'Staff added successfully'})
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_staff_update(request, staff_id):
    """Update an existing staff member"""
    if not request.user.is_staff:
        return Response({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        staff = StaffImage.objects.get(id=staff_id)
        staff.name = request.POST.get('name', staff.name)
        staff.role = request.POST.get('role', staff.role)
        staff.description = request.POST.get('description', staff.description)
        staff.order = int(request.POST.get('order', staff.order))
        staff.is_active = request.POST.get('is_active') == 'true'
        if request.FILES.get('image'):
            staff.image = request.FILES.get('image')
        staff.save()
        return Response({'success': True, 'message': 'Staff updated successfully'})
    except StaffImage.DoesNotExist:
        return Response({'success': False, 'message': 'Staff not found'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_staff_delete(request, staff_id):
    """Delete a staff member"""
    if not request.user.is_staff:
        return Response({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        staff = StaffImage.objects.get(id=staff_id)
        staff.delete()
        return Response({'success': True, 'message': 'Staff deleted successfully'})
    except StaffImage.DoesNotExist:
        return Response({'success': False, 'message': 'Staff not found'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_owner_list(request):
    """Get all owner information for admin dashboard"""
    if not request.user.is_staff:
        return Response({'success': False, 'message': 'Permission denied'}, status=403)
    
    owners = OwnerImage.objects.all().order_by('-created_at')
    owner_data = []
    for o in owners:
        owner_data.append({
            'id': o.id,
            'name': o.name,
            'title': o.title,
            'description': o.description,
            'image': o.image.url if o.image else None,
            'is_active': o.is_active,
        })
    return Response(owner_data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_owner_create(request):
    """Create owner information"""
    if not request.user.is_staff:
        return Response({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        owner = OwnerImage.objects.create(
            name=request.POST.get('name'),
            title=request.POST.get('title', 'Owner'),
            description=request.POST.get('description', ''),
            image=request.FILES.get('image'),
            is_active=request.POST.get('is_active') == 'true'
        )
        return Response({'success': True, 'id': owner.id, 'message': 'Owner added successfully'})
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_owner_update(request, owner_id):
    """Update owner information"""
    if not request.user.is_staff:
        return Response({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        owner = OwnerImage.objects.get(id=owner_id)
        owner.name = request.POST.get('name', owner.name)
        owner.title = request.POST.get('title', owner.title)
        owner.description = request.POST.get('description', owner.description)
        owner.is_active = request.POST.get('is_active') == 'true'
        if request.FILES.get('image'):
            owner.image = request.FILES.get('image')
        owner.save()
        return Response({'success': True, 'message': 'Owner updated successfully'})
    except OwnerImage.DoesNotExist:
        return Response({'success': False, 'message': 'Owner not found'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_owner_delete(request, owner_id):
    """Delete owner information"""
    if not request.user.is_staff:
        return Response({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        owner = OwnerImage.objects.get(id=owner_id)
        owner.delete()
        return Response({'success': True, 'message': 'Owner deleted successfully'})
    except OwnerImage.DoesNotExist:
        return Response({'success': False, 'message': 'Owner not found'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=400)


# --------- Custom LMS (staff) ---------

def staff_required(view_func):
    return user_passes_test(lambda u: u.is_active and u.is_staff)(view_func)


@staff_required
@require_http_methods(["GET", "POST"])
def lms_dashboard(request):
    stats = {
        "users": User.objects.count(),
        "active_subs": UserSubscription.objects.filter(active=True).count(),
        "pending_payments": request.user.reviewed_payments.none().model.objects.filter(status="pending").count(),
        # Count distinct users who attended today, not total meal records
        "today_attendance": Attendance.objects.filter(date=timezone.localdate()).values('user').distinct().count(),
    }
    pending = PaymentProofSerializer(
        PaymentProofSerializer.Meta.model.objects.filter(status="pending").order_by("-submitted_at")[:10],
        many=True,
    ).data
    
    # Handle menu upload
    menu_form = MonthlyMenuForm()
    current_menu = None
    if request.method == "POST" and "menu_form" in request.POST:
        menu_form = MonthlyMenuForm(request.POST, request.FILES)
        if menu_form.is_valid():
            # Check if menu for this month/year already exists
            month = menu_form.cleaned_data['month']
            year = menu_form.cleaned_data['year']
            existing_menu = MonthlyMenu.objects.filter(month=month, year=year).first()
            
            if existing_menu:
                # Update existing menu
                existing_menu.file = menu_form.cleaned_data.get('file') or existing_menu.file
                existing_menu.image = menu_form.cleaned_data.get('image') or existing_menu.image
                existing_menu.text = menu_form.cleaned_data.get('text') or existing_menu.text
                existing_menu.save()
                messages.success(request, f"Menu for {month:02d}/{year} updated successfully!")
            else:
                # Create new menu
                menu_form.save()
                messages.success(request, f"Menu for {month:02d}/{year} uploaded successfully!")
            
            return redirect('lms_dashboard')
        else:
            messages.error(request, "Please correct the errors in the menu form.")
    
    # Get current month's menu for display
    today = timezone.now()
    current_menu = MonthlyMenu.objects.filter(month=today.month, year=today.year).first()
    
    return render(request, 'lms/dashboard.html', {
        "stats": stats, 
        "pending": pending, 
        "menu_form": menu_form,
        "current_menu": current_menu
    })


@staff_required
@require_http_methods(["GET", "POST"])
def lms_payments(request):
    if request.method == "POST":
        action = request.POST.get("action")
        payment_id = request.POST.get("payment_id")
        try:
            proof = PaymentProofSerializer.Meta.model.objects.select_related("subscription_plan", "user").get(pk=payment_id)
        except PaymentProofSerializer.Meta.model.DoesNotExist:
            messages.error(request, "Payment not found")
            return redirect('lms_payments')
        from django.utils import timezone as tz
        if action == "approve":
            if proof.status != "approved":
                proof.status = "approved"
                proof.reviewed_by = request.user
                proof.reviewed_at = tz.now()
                proof.txn_id = proof.txn_id or f"TXN-{proof.pk}-{int(proof.reviewed_at.timestamp())}"
                proof.save()
                start = tz.localdate()
                end = proof.subscription_plan.compute_end_date(start)
                # Deactivate existing active subscriptions before creating a new one
                UserSubscription.objects.filter(user=proof.user, active=True).update(active=False)
                UserSubscription.objects.create(user=proof.user, plan=proof.subscription_plan, start_date=start, end_date=end, active=True)
                messages.success(request, "Payment approved and subscription activated.")
        elif action == "reject":
            if proof.status != "rejected":
                proof.status = "rejected"
                proof.reviewed_by = request.user
                proof.reviewed_at = tz.now()
                proof.save()
                messages.info(request, "Payment rejected.")
        return redirect('lms_payments')

    qs = PaymentProofSerializer.Meta.model.objects.filter(status="pending").order_by("-submitted_at")
    return render(request, 'lms/payments.html', {"payments": qs})

@staff_required
@login_required
def lms_export_attendance_csv(request):
    """Export all attendance records to CSV with comprehensive data"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Access denied'}, status=403)
    
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="attendance_export.csv"'
        
        writer = csv.writer(response)
        # Enhanced headers with more useful information
        writer.writerow([
            "User ID", "Username", "Full Name", "Email", "Date", 
            "Meal Type", "Marked At", "Weekday"
        ])
        
        # Get attendance records with user information
        attendances = Attendance.objects.select_related("user").order_by('-date', '-marked_at')
        
        for attendance in attendances:
            # Get weekday name
            weekday = attendance.date.strftime('%A')
            
            writer.writerow([
                attendance.user.id,
                attendance.user.username,
                attendance.user.full_name or 'Not provided',
                attendance.user.email or 'Not provided',
                attendance.date.strftime('%Y-%m-%d'),
                attendance.meal_type,
                attendance.marked_at.strftime('%Y-%m-%d %H:%M:%S'),
                weekday
            ])
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Export failed: {str(e)}'}, status=500)


@login_required
def admin_mark_attendance(request):
    """Admin function to mark attendance for any user"""
    print(f"admin_mark_attendance called with method: {request.method}")
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            user_id = data.get('user_id')
            
            if not user_id:
                return JsonResponse({'success': False, 'message': 'User ID required'})
            
            # Get the user
            user = User.objects.get(id=user_id, is_staff=False)
            
            # Check if user has an active subscription
            active_sub = UserSubscription.objects.filter(user=user, active=True).first()
            if not active_sub:
                return JsonResponse({'success': False, 'message': 'User has no active subscription'})
            
            # Check if attendance already marked today
            today = timezone.localdate()
            existing_attendance = Attendance.objects.filter(user=user, date=today).first()
            if existing_attendance:
                return JsonResponse({'success': False, 'message': 'Attendance already marked for today'})
            
            # Mark attendance for all meals in the subscription
            allowed_meals = active_sub.plan.included_meals
            for meal in allowed_meals:
                Attendance.objects.create(
                    user=user,
                    meal_type=meal,  # Use meal_type field
                    date=today,
                    marked_at=timezone.now()
                )
            
            return JsonResponse({'success': True, 'message': 'Attendance marked successfully'})
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    elif request.method == 'GET':
        return JsonResponse({'success': False, 'message': 'GET method not allowed. Use POST.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def student_details(request, user_id):
    """Get detailed student information and attendance history"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Access denied'}, status=403)
    
    try:
        # Get the user with attendance count annotation
        from django.db.models import Count, Max
        user = User.objects.filter(id=user_id, is_staff=False).annotate(
            total_attendance_count=Count('attendances'),
            last_attendance=Max('attendances__marked_at')
        ).first()
        
        if not user:
            return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
        
        # Get user's attendance history (last 30 days)
        thirty_days_ago = timezone.localdate() - timedelta(days=30)
        
        attendance_history = Attendance.objects.filter(
            user=user,
            date__gte=thirty_days_ago
        ).order_by('-date', '-marked_at')
        
        # Get today's attendance
        today = timezone.localdate()
        today_attendance = Attendance.objects.filter(user=user, date=today).first()
        
        # Get active subscriptions
        active_subscriptions = UserSubscription.objects.filter(user=user, active=True)
        
        # Prepare student data
        student_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': getattr(user, 'full_name', ''),
            'mobile_no': getattr(user, 'mobile_no', ''),
            'total_attendance_count': user.total_attendance_count,
            'last_attendance': user.last_attendance.isoformat() if user.last_attendance else None,
            'today_attendance': {
                'id': today_attendance.id,
                'date': today_attendance.date.isoformat(),
                'meal_type': today_attendance.meal_type,
                'marked_at': today_attendance.marked_at.isoformat()
            } if today_attendance else None,
            'active_subscriptions': [
                {
                    'id': sub.id,
                    'plan': {
                        'id': sub.plan.id,
                        'title': sub.plan.title,
                        'included_meals': sub.plan.included_meals
                    }
                }
                for sub in active_subscriptions
            ]
        }
        
        # Prepare attendance history data
        attendance_data = [
            {
                'id': att.id,
                'date': att.date.isoformat(),
                'meal': att.meal_type,  # Use meal_type field
                'marked_at': att.marked_at.isoformat(),
                'meal_type': att.meal_type
            }
            for att in attendance_history
        ]
        
        return JsonResponse({
            'success': True,
            'student': student_data,
            'attendance_history': attendance_data
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["GET", "POST"])
def lms_plans(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        price = request.POST.get("price")
        billing_period = request.POST.get("billing_period", "monthly")
        features = request.POST.get("features", "")
        included_meals = request.POST.getlist("included_meals")
        is_active = bool(request.POST.get("is_active"))
        if not title or not price:
            messages.error(request, "Title and price are required.")
        else:
            try:
                SubscriptionPlan.objects.create(
                    title=title,
                    price=price,
                    billing_period=billing_period,
                    features=features,
                    included_meals=included_meals,
                    is_active=is_active,
                )
                messages.success(request, "Plan added.")
                return redirect('lms_plans')
            except Exception as e:
                messages.error(request, f"Failed to add plan: {e}")

    plans = SubscriptionPlan.objects.all().order_by('-is_active', 'title')
    return render(request, 'lms/plans.html', {"plans": plans})


@login_required
def user_details(request, user_id):
    """Get detailed user information for user management"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Access denied'}, status=403)
    
    try:
        # Get the user with attendance count annotation
        user = User.objects.filter(id=user_id).annotate(
            total_attendance_count=Count('attendances'),
            last_attendance=Max('attendances__marked_at')
        ).first()
        
        if not user:
            return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
        
        # Get active subscriptions
        active_subscriptions = UserSubscription.objects.filter(user=user, active=True)
        
        # Prepare user data
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': getattr(user, 'full_name', ''),
            'mobile_no': getattr(user, 'mobile_no', ''),
            'profile_image': user.profile_image.url if user.profile_image else None,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'total_attendance_count': user.total_attendance_count,
            'last_attendance': user.last_attendance.isoformat() if user.last_attendance else None,
            'active_subscriptions': [
                {
                    'id': sub.id,
                    'plan': {
                        'id': sub.plan.id,
                        'title': sub.plan.title,
                        'price': float(sub.plan.price),
                        'billing_period': sub.plan.billing_period,
                        'included_meals': sub.plan.included_meals
                    }
                }
                for sub in active_subscriptions
            ]
        }
        
        return JsonResponse({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_http_methods(["POST", "PUT", "DELETE"])
def admin_user_crud(request):
    """Admin function to create, update, or delete users"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Access denied'}, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        
        if request.method == 'POST':
            # Create new user
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            full_name = data.get('full_name', '')
            mobile_no = data.get('mobile_no', '')
            is_active = data.get('is_active', True)
            is_staff = data.get('is_staff', False)
            
            if not username or not email or not password:
                return JsonResponse({'success': False, 'message': 'Username, email, and password are required'})
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'message': 'Username already exists'})
            
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'Email already exists'})
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                full_name=full_name,
                mobile_no=mobile_no,
                is_active=is_active,
                is_staff=is_staff
            )
            
            return JsonResponse({'success': True, 'message': 'User created successfully', 'user_id': user.id})
        
        elif request.method == 'PUT':
            # Update existing user
            user_id = data.get('user_id')
            if not user_id:
                return JsonResponse({'success': False, 'message': 'User ID required'})
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'User not found'})
            
            # Update fields
            if 'username' in data:
                if User.objects.filter(username=data['username']).exclude(id=user_id).exists():
                    return JsonResponse({'success': False, 'message': 'Username already exists'})
                user.username = data['username']
            
            if 'email' in data:
                if User.objects.filter(email=data['email']).exclude(id=user_id).exists():
                    return JsonResponse({'success': False, 'message': 'Email already exists'})
                user.email = data['email']
            
            if 'full_name' in data:
                user.full_name = data['full_name'] or ''  # Ensure it's not None
            
            if 'mobile_no' in data:
                user.mobile_no = data['mobile_no'] or ''  # Ensure it's not None
            
            if 'is_active' in data:
                # Ensure boolean conversion
                user.is_active = bool(data['is_active'])
            
            if 'is_staff' in data:
                # Ensure boolean conversion
                user.is_staff = bool(data['is_staff'])
            
            try:
                user.save()
                return JsonResponse({'success': True, 'message': 'User updated successfully'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'Validation error: {str(e)}'})
        
        elif request.method == 'DELETE':
            # Delete user
            user_id = data.get('user_id')
            if not user_id:
                return JsonResponse({'success': False, 'message': 'User ID required'})
            
            try:
                user = User.objects.get(id=user_id)
                # Prevent deleting superusers
                if user.is_superuser:
                    return JsonResponse({'success': False, 'message': 'Cannot delete superuser'})
                # Prevent deleting self
                if user.id == request.user.id:
                    return JsonResponse({'success': False, 'message': 'Cannot delete your own account'})
                
                user.delete()
                return JsonResponse({'success': True, 'message': 'User deleted successfully'})
                
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'User not found'})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def export_users_csv(request):
    """Export all users to CSV with comprehensive data"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Access denied'}, status=403)
    
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        
        writer = csv.writer(response)
        # Enhanced headers with more useful information
        writer.writerow([
            'ID', 'Username', 'Email', 'Full Name', 'Mobile Number', 
            'Is Active', 'Is Staff', 'Date Joined', 'Last Login', 
            'Total Attendance', 'Last Attendance Date', 'Active Subscriptions'
        ])
        
        # Get users with attendance data and subscription info
        users = User.objects.annotate(
            total_attendance_count=Count('attendances'),
            last_attendance_date=Max('attendances__date')
        ).prefetch_related('subscriptions').order_by('username')
        
        for user in users:
            # Get active subscriptions count
            active_subs = user.subscriptions.filter(active=True).count()
            
            # Format last attendance date
            last_attendance = user.last_attendance_date.strftime('%Y-%m-%d') if user.last_attendance_date else 'Never'
            
            writer.writerow([
                user.id,
                user.username,
                user.email or 'Not provided',
                user.full_name or 'Not provided',
                user.mobile_no or 'Not provided',
                'Yes' if user.is_active else 'No',
                'Yes' if user.is_staff else 'No',
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
                user.total_attendance_count,
                last_attendance,
                active_subs
            ])
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Export failed: {str(e)}'}, status=500)


@login_required
def export_meal_feedback_csv(request):
    """Export all meal feedback records to CSV with comprehensive data"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Access denied'}, status=403)
    
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="meal_feedback_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'User ID', 'Username', 'Full Name', 'Meal Type', 'Meal Date',
            'Overall Rating', 'Taste Rating', 'Quantity Rating', 'Hygiene Rating',
            'Comments', 'Is Anonymous', 'Created At', 'Updated At'
        ])
        
        feedbacks = MealFeedback.objects.select_related('user').order_by('-created_at')
        
        for feedback in feedbacks:
            writer.writerow([
                feedback.id,
                feedback.user.id,
                feedback.user.username if not feedback.is_anonymous else 'Anonymous',
                feedback.user.full_name if not feedback.is_anonymous else 'Anonymous',
                feedback.get_meal_type_display(),
                feedback.meal_date.strftime('%Y-%m-%d'),
                feedback.rating,
                feedback.taste_rating or 'N/A',
                feedback.quantity_rating or 'N/A',
                feedback.hygiene_rating or 'N/A',
                feedback.comments or 'No comments',
                'Yes' if feedback.is_anonymous else 'No',
                feedback.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                feedback.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Export failed: {str(e)}'}, status=500)
