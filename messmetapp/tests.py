from django.test import TestCase
from django.utils import timezone
from .models import User, SubscriptionPlan, UserSubscription, Attendance


class ModelSmokeTests(TestCase):
    def test_create_user_and_plan(self):
        user = User.objects.create_user(username="alice", password="pass12345", full_name="Alice", mobile_no="9999999999")
        plan = SubscriptionPlan.objects.create(title="Monthly All Meals", price=3000, included_meals=["breakfast", "lunch", "dinner"])
        self.assertTrue(user.pk)
        self.assertTrue(plan.pk)

    def test_attendance_unique_per_day_meal(self):
        user = User.objects.create_user(username="bob", password="pass12345", full_name="Bob", mobile_no="8888888888")
        date = timezone.localdate()
        Attendance.objects.create(user=user, date=date, meal_type="lunch")
        with self.assertRaises(Exception):
            Attendance.objects.create(user=user, date=date, meal_type="lunch")

# Create your tests here.
