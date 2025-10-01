from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, MonthlyMenu, CarouselImage, MealFeedback, VisitorPayment, VisitorFeedback


class RegisterForm(UserCreationForm):
    full_name = forms.CharField(max_length=150)
    mobile_no = forms.CharField(max_length=15)
    profile_image = forms.ImageField(required=False)
    hostel_status = forms.ChoiceField(
        choices=[
            (User.HOSTEL_STATUS_HOSTELLER, "Hosteller"),
            (User.HOSTEL_STATUS_NON_HOSTELLER, "Non-Hosteller"),
        ],
        initial=User.HOSTEL_STATUS_NON_HOSTELLER,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "full_name", "mobile_no", "profile_image", "hostel_status")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "username": "Enter username",
            "full_name": "Enter your full name",
            "mobile_no": "Enter mobile number",
            "password1": "Create a password",
            "password2": "Confirm password",
        }
        for name, field in self.fields.items():
            attrs = field.widget.attrs
            if name in placeholders:
                attrs["placeholder"] = placeholders[name]
            # ensure consistent styling hooks
            attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.full_name = self.cleaned_data.get("full_name")
        user.mobile_no = self.cleaned_data.get("mobile_no")
        user.profile_image = self.cleaned_data.get("profile_image")
        user.hostel_status = self.cleaned_data.get("hostel_status")
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("full_name", "mobile_no", "profile_image", "email")


class MonthlyMenuForm(forms.ModelForm):
    class Meta:
        model = MonthlyMenu
        fields = ("month", "year", "file", "image", "text")
        widgets = {
            "month": forms.Select(choices=[(i, f"{i:02d}") for i in range(1, 13)]),
            "year": forms.NumberInput(attrs={"min": 2024, "max": 2030}),
            "text": forms.Textarea(attrs={"rows": 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["month"].widget.attrs.update({"class": "form-control"})
        self.fields["year"].widget.attrs.update({"class": "form-control"})
        self.fields["file"].widget.attrs.update({"class": "form-control"})
        self.fields["image"].widget.attrs.update({"class": "form-control"})
        self.fields["text"].widget.attrs.update({"class": "form-control"})


class CarouselImageForm(forms.ModelForm):
    class Meta:
        model = CarouselImage
        fields = ("title", "image", "description", "is_active", "order")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["image"].widget.attrs.update({"class": "form-control"})
        self.fields["description"].widget.attrs.update({"class": "form-control"})
        self.fields["order"].widget.attrs.update({"class": "form-control"})


class MealFeedbackForm(forms.ModelForm):
    class Meta:
        model = MealFeedback
        fields = ("meal_type", "meal_date", "rating", "taste_rating", "quantity_rating", "hygiene_rating", "comments", "is_anonymous")
        widgets = {
            "meal_type": forms.Select(attrs={"class": "form-control"}),
            "meal_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "rating": forms.Select(attrs={"class": "form-control"}),
            "taste_rating": forms.Select(attrs={"class": "form-control"}),
            "quantity_rating": forms.Select(attrs={"class": "form-control"}),
            "hygiene_rating": forms.Select(attrs={"class": "form-control"}),
            "comments": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Share your thoughts about the meal..."}),
            "is_anonymous": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date to today
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['meal_date'].initial = timezone.localdate()
        
        # Make individual ratings optional
        self.fields['taste_rating'].required = False
        self.fields['quantity_rating'].required = False
        self.fields['hygiene_rating'].required = False


class VisitorPaymentForm(forms.ModelForm):
    class Meta:
        model = VisitorPayment
        fields = ("name", "mobile_no", "amount", "meal_type", "screenshot", "note")
        widgets = {
            "meal_type": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", "form-control")


class VisitorFeedbackForm(forms.ModelForm):
    class Meta:
        model = VisitorFeedback
        fields = ("name", "meal_type", "meal_date", "rating", "comments")
        widgets = {
            "meal_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "meal_type": forms.Select(attrs={"class": "form-control"}),
            "comments": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
