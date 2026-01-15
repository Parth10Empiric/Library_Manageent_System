from django.urls import path, include
from book import views

urlpatterns = [
    path('book_req/<int:book_id>/', views.request_issue, name='request_issue'), 
]
