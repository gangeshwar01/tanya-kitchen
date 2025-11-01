from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about_view, name='about'),
    path('menu/', views.menu_view, name='menu'),
    path('attendance/', views.attendance_view, name='attendance'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('plans/', views.plans_list, name='plans_list'),
    path('plans/<int:pk>/buy/', views.plan_buy, name='plan_buy'),
    # Visitor
    path('visitor/payment/', views.visitor_payment, name='visitor_payment'),
    path('api/visitor/feedback/', views.visitor_feedback_api, name='visitor_feedback_api'),
    # APIs
    path('api/plans/', views.api_plans, name='api_plans'),
    path('api/me/subscription/', views.api_my_subscription, name='api_my_subscription'),
    path('api/attendance/mark/', views.api_mark_attendance, name='api_mark_attendance'),
    path('api/attendance/', views.api_attendance_list, name='api_attendance_list'),
    path('api/menu/current/', views.api_current_menu, name='api_current_menu'),
    path('api/payments/', views.api_payment_proofs, name='api_payment_proofs'),
    path('api/payments/config/', views.api_payment_config, name='api_payment_config'),
    path('api/feedback/', views.api_feedback, name='api_feedback'),
    path('api/notices/active/', views.api_active_notices, name='api_active_notices'),
    path('api/notices/list/', views.api_notices_list, name='api_notices_list'),
    path('api/notices/create/', views.api_notice_create, name='api_notice_create'),
    path('api/notices/update/<int:notice_id>/', views.api_notice_update, name='api_notice_update'),
    path('api/notices/delete/<int:notice_id>/', views.api_notice_delete, name='api_notice_delete'),
    # Staff & Owner APIs
    path('api/staff/list/', views.api_staff_list, name='api_staff_list'),
    path('api/staff/create/', views.api_staff_create, name='api_staff_create'),
    path('api/staff/update/<int:staff_id>/', views.api_staff_update, name='api_staff_update'),
    path('api/staff/delete/<int:staff_id>/', views.api_staff_delete, name='api_staff_delete'),
    path('api/owner/list/', views.api_owner_list, name='api_owner_list'),
    path('api/owner/create/', views.api_owner_create, name='api_owner_create'),
    path('api/owner/update/<int:owner_id>/', views.api_owner_update, name='api_owner_update'),
    path('api/owner/delete/<int:owner_id>/', views.api_owner_delete, name='api_owner_delete'),
    # Admin APIs
    path('api/admin/mark-attendance/', views.admin_mark_attendance, name='admin_mark_attendance'),
    path('api/admin/mark-attendance', views.admin_mark_attendance, name='admin_mark_attendance_no_slash'),
    path('api/student-details/<int:user_id>/', views.student_details, name='student_details'),
    # User Management APIs
    path('api/user-details/<int:user_id>/', views.user_details, name='user_details'),
    path('api/admin/user/', views.admin_user_crud, name='admin_user_crud'),
    # Meal Feedback
    path('meal-feedback/', views.meal_feedback_view, name='meal_feedback'),
    path('api/meal-feedback/', views.api_meal_feedback, name='api_meal_feedback'),
    path('api/meal-feedback-list/', views.api_meal_feedback_list, name='api_meal_feedback_list'),
]


