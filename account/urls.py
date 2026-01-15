from django.urls import path, include
from . import views

urlpatterns = [
    path('login/', views.login_view, name="login" ),
    path('addstd/', views.add_student_view, name="addstd")
]
