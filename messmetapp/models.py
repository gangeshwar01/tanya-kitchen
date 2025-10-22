from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from django.core.validators import RegexValidator
from datetime import date, timedelta


class User(AbstractUser):
    full_name = models.CharField(max_length=150, blank=True, null=True)
    mobile_no = models.CharField(
        max_length=15,
        validators=[RegexValidator(r"^[0-9+\-()\s]{8,15}$", "Enter a valid phone number.")],
        unique=True,
        blank=True,
        null=True,
    )
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)
    HOSTEL_STATUS_HOSTELLER = "hosteller"
    HOSTEL_STATUS_NON_HOSTELLER = "non_hosteller"
    HOSTEL_STATUS_CHOICES = [
        (HOSTEL_STATUS_HOSTELLER, "Hosteller"),
        (HOSTEL_STATUS_NON_HOSTELLER, "Non-Hosteller"),
    ]
    hostel_status = models.CharField(
        max_length=20,
        choices=HOSTEL_STATUS_CHOICES,
        default=HOSTEL_STATUS_NON_HOSTELLER,
    )

    def __str__(self) -> str:
        return self.username


class SubscriptionPlan(models.Model):
    BILLING_PERIOD_CHOICES = [
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]
    MEAL_BREAKFAST = "breakfast"
    MEAL_LUNCH = "lunch"
    MEAL_DINNER = "dinner"
    MEAL_CHOICES = [
        (MEAL_BREAKFAST, "Breakfast"),
        (MEAL_LUNCH, "Lunch"),
        (MEAL_DINNER, "Dinner"),
    ]

    title = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_period = models.CharField(max_length=20, choices=BILLING_PERIOD_CHOICES, default="monthly")
    features = models.TextField(blank=True)
    included_meals = models.JSONField(default=list)  # list of meal strings from MEAL_CHOICES
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.title} ({self.billing_period})"

    def compute_end_date(self, start: date) -> date:
        if self.billing_period == "monthly":
            # approximate as 30 days for simplicity
            return start + timedelta(days=30)
        if self.billing_period == "quarterly":
            return start + timedelta(days=90)
        if self.billing_period == "yearly":
            return start + timedelta(days=365)
        return start + timedelta(days=30)


class UserSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name="user_subscriptions")
    start_date = models.DateField()
    end_date = models.DateField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.plan.title}"


class PaymentProof(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_proofs")
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name="payment_proofs")
    screenshot = models.ImageField(upload_to="payments/")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    txn_id = models.CharField(max_length=100, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_payments")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self) -> str:
        return f"PaymentProof #{self.pk} - {self.user.username}"


class Attendance(models.Model):
    MEAL_CHOICES = SubscriptionPlan.MEAL_CHOICES

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendances")
    date = models.DateField(default=timezone.localdate)
    meal_type = models.CharField(max_length=20, choices=MEAL_CHOICES)
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "date", "meal_type")
        ordering = ["-date", "-marked_at"]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.date} - {self.meal_type}"


class MonthlyMenu(models.Model):
    month = models.PositiveSmallIntegerField()  # 1-12
    year = models.PositiveSmallIntegerField()
    file = models.FileField(upload_to="menus/", blank=True, null=True)
    image = models.ImageField(upload_to="menus/", blank=True, null=True)
    text = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("month", "year")
        ordering = ["-year", "-month"]

    def __str__(self) -> str:
        return f"Menu {self.month}/{self.year}"


class Notification(models.Model):
    target = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    read_flag = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Notif to {self.target.username}: {self.message[:30]}"


class PaymentConfig(models.Model):
    upi_id = models.CharField(max_length=100, blank=True)
    gpay_qr = models.ImageField(upload_to="payments/qr/", blank=True, null=True)
    phonepe_qr = models.ImageField(upload_to="payments/qr/", blank=True, null=True)
    note = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"Payment Config ({self.upi_id or 'no upi'})"


class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedbacks")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Feedback by {self.user.username}"


class MealFeedback(models.Model):
    RATING_CHOICES = [
        (1, 'Very Poor'),
        (2, 'Poor'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]
    
    MEAL_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="meal_feedbacks")
    meal_type = models.CharField(max_length=20, choices=MEAL_CHOICES)
    meal_date = models.DateField()
    rating = models.IntegerField(choices=RATING_CHOICES)
    taste_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    quantity_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    hygiene_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    comments = models.TextField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ['user', 'meal_type', 'meal_date']

    def __str__(self) -> str:
        return f"{self.user.username} - {self.get_meal_type_display()} ({self.meal_date}) - {self.get_rating_display()}"
    
    @property
    def overall_rating(self):
        """Calculate overall rating from individual ratings"""
        ratings = [self.rating]
        if self.taste_rating:
            ratings.append(self.taste_rating)
        if self.quantity_rating:
            ratings.append(self.quantity_rating)
        if self.hygiene_rating:
            ratings.append(self.hygiene_rating)
        return round(sum(ratings) / len(ratings), 1) if ratings else 0


class CarouselImage(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='carousel/')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self) -> str:
        return self.title

# Create your models here.


class VisitorPayment(models.Model):
    PERIOD_TODAY = 'today'
    PERIOD_WEEK = 'week'
    PERIOD_MONTH = 'month'

    name = models.CharField(max_length=150)
    mobile_no = models.CharField(max_length=20, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    meal_type = models.CharField(max_length=20, choices=SubscriptionPlan.MEAL_CHOICES)
    screenshot = models.ImageField(upload_to='payments/')
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"VisitorPayment {self.name} - {self.amount}"


class VisitorFeedback(models.Model):
    name = models.CharField(max_length=150)
    meal_type = models.CharField(max_length=20, choices=[('breakfast','Breakfast'),('lunch','Lunch'),('dinner','Dinner')])
    meal_date = models.DateField()
    rating = models.PositiveSmallIntegerField()
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"VisitorFeedback {self.name} - {self.meal_type}"
