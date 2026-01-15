from django.db import models
from book.models import Book
from account.models import Student
from datetime import date, timedelta

# Create your models here.

def seven_days_hence():
    return date.today() + timedelta(days=14)

class Issue(models.Model):
    CHOICES = (
        ('requested', 'Requested'),
        ('issued', 'Issued'),
        ('returned', 'Returned'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    issue_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(default=seven_days_hence)
    status = models.CharField(max_length=20, choices=CHOICES, default='requested')


