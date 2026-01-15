from django.contrib import admin
from .models import Fine, Payment

# Register your models here.

admin.site.register(Fine)
admin.site.register(Payment)