from rest_framework import serializers
from .models import (
    SubscriptionPlan,
    UserSubscription,
    PaymentProof,
    Attendance,
    MonthlyMenu,
    User,
    PaymentConfig,
    Feedback,
)


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "id",
            "title",
            "price",
            "billing_period",
            "features",
            "included_meals",
            "is_active",
        ]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "full_name", "mobile_no", "email", "profile_image"]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = UserSubscription
        fields = [
            "id",
            "user",
            "plan",
            "start_date",
            "end_date",
            "active",
            "created_at",
        ]


class PaymentProofSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentProof
        fields = [
            "id",
            "subscription_plan",
            "screenshot",
            "status",
            "txn_id",
            "submitted_at",
            "reviewed_by",
            "reviewed_at",
            "note",
        ]
        read_only_fields = ("status", "txn_id", "submitted_at", "reviewed_by", "reviewed_at")

    def create(self, validated_data):
        user = self.context["request"].user
        return PaymentProof.objects.create(user=user, **validated_data)


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ["id", "date", "meal_type", "marked_at"]
        read_only_fields = ("marked_at",)


class MonthlyMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyMenu
        fields = ["id", "month", "year", "file", "image", "text", "uploaded_at"]


class PaymentConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentConfig
        fields = ["upi_id", "gpay_qr", "phonepe_qr", "note"]


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ["id", "message", "created_at"]

