from django.db import models
from account.models import Student
from issue.models import Issue

# Create your models here.
class Fine(models.Model):
    
    PAYMENT_MODE_CHOICES = (
        ("online", "Online"),
        ("cash", "Cash"),
    )

    ammount = models.DecimalField(max_digits=10, decimal_places=2)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    is_paid = models.BooleanField(default=False)
    issue = models.OneToOneField(Issue, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    payment_mode = models.CharField(
        max_length=10,
        choices=PAYMENT_MODE_CHOICES,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"Fine - {self.student.sudent_id}"
    
class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)

    stripe_payment_intent_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    fines = models.ManyToManyField(Fine)

    status = models.CharField(
        max_length=30,
        choices=[
            ("created", "Created"),
            ("succeeded", "Succeeded"),
            ("failed", "Failed"),
        ],
        default="created"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.stripe_payment_intent_id} - {self.status}"
