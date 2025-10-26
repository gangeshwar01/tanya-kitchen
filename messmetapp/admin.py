from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, SubscriptionPlan, UserSubscription, PaymentProof, Attendance, MonthlyMenu, Notification, PaymentConfig, Feedback, CarouselImage, FoodImage, PopupNotice


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Profile", {"fields": ("full_name", "mobile_no", "profile_image")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Profile", {"fields": ("full_name", "mobile_no", "profile_image")}),
    )
    list_display = ("username", "full_name", "mobile_no", "email", "is_staff")
    search_fields = ("username", "full_name", "mobile_no", "email")


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "billing_period", "is_active")
    list_filter = ("billing_period", "is_active")
    search_fields = ("title",)


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "start_date", "end_date", "active")
    list_filter = ("active", "plan__billing_period")
    search_fields = ("user__username", "plan__title")



    @admin.action(description="Approve selected payments and activate subscription")
    def approve_payments(self, request, queryset):
        from django.utils import timezone
        count = 0
        for proof in queryset.select_related("subscription_plan", "user"):
            if proof.status == PaymentProof.STATUS_APPROVED:
                continue
            proof.status = PaymentProof.STATUS_APPROVED
            proof.reviewed_by = request.user
            proof.reviewed_at = timezone.now()
            proof.txn_id = proof.txn_id or f"TXN-{proof.pk}-{int(proof.reviewed_at.timestamp())}"
            proof.save()

            # create/activate subscription
            start = timezone.localdate()
            end = proof.subscription_plan.compute_end_date(start)
            UserSubscription.objects.create(
                user=proof.user,
                plan=proof.subscription_plan,
                start_date=start,
                end_date=end,
                active=True,
            )
            count += 1
        self.message_user(request, f"Approved and activated {count} payment(s).")

    @admin.action(description="Reject selected payments")
    def reject_payments(self, request, queryset):
        from django.utils import timezone
        updated = queryset.exclude(status=PaymentProof.STATUS_REJECTED).update(
            status=PaymentProof.STATUS_REJECTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"Rejected {updated} payment(s).")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "meal_type", "marked_at")
    list_filter = ("meal_type", "date")
    search_fields = ("user__username",)


@admin.register(MonthlyMenu)
class MonthlyMenuAdmin(admin.ModelAdmin):
    list_display = ("month", "year", "uploaded_at")
    list_filter = ("year", "month")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("target", "message", "read_flag", "created_at")
    list_filter = ("read_flag",)
    search_fields = ("target__username", "message")


@admin.register(PaymentConfig)
class PaymentConfigAdmin(admin.ModelAdmin):
    list_display = ("upi_id", "note")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__username", "message")


@admin.register(CarouselImage)
class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "order", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "description")
    list_editable = ("is_active", "order")


@admin.register(FoodImage)
class FoodImageAdmin(admin.ModelAdmin):
    list_display = ("title", "meal_type", "is_active", "order", "created_at")
    list_filter = ("meal_type", "is_active", "created_at")
    search_fields = ("title", "description")
    list_editable = ("is_active", "order")
    fieldsets = (
        (None, {
            'fields': ('title', 'image', 'description')
        }),
        ('Settings', {
            'fields': ('meal_type', 'is_active', 'order')
        }),
    )


@admin.register(PopupNotice)
class PopupNoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "start_datetime", "end_datetime", "target_audience", "is_active", "priority", "created_by")
    list_filter = ("is_active", "target_audience", "start_datetime", "end_datetime")
    search_fields = ("title", "message")
    list_editable = ("is_active", "priority")
    readonly_fields = ("created_by", "created_at", "updated_at")
    fieldsets = (
        ("Notice Content", {
            'fields': ('title', 'message')
        }),
        ("Schedule & Targeting", {
            'fields': ('start_datetime', 'end_datetime', 'target_audience', 'priority')
        }),
        ("Status", {
            'fields': ('is_active',)
        }),
        ("Metadata", {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# Register your models here.
