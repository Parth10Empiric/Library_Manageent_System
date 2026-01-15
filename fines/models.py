from django.db import models
from account.models import Student
from issue.models import Issue

# Create your models here.
class Fine(models.Model):
    ammount = models.DecimalField(max_digits=10, decimal_places=2)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    is_paid = models.BooleanField(default=False)
    issue = models.OneToOneField(Issue, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Fine - {self.student.sudent_id}"
    
class Payment(models.Model):
    fine = models.ForeignKey(Fine, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    amount = models.IntegerField()
    status = models.CharField(max_length=50, default='Created')  # Created, Success, Failed
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.razorpay_order_id} - {self.status}"