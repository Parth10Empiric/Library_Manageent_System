from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import RegexValidator

# Create your models here.
phone_validator = RegexValidator(
    regex=r'^\+?\d{10,15}$',
    message="Enter a valid phone number (10–15 digits)."
)

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sudent_id = models.CharField(max_length=20, unique=True, editable=False)
    department = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, validators=[phone_validator])
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.sudent_id:
            year = timezone.now().year
            last_student = Student.objects.order_by("-id").first()
            last_number = last_student.id if last_student else 0
            self.sudent_id = f"STD{year}-{last_number + 1:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sudent_id} - {self.user.username}"