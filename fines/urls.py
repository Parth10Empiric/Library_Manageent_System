from django.urls import path, include
from . import views

urlpatterns = [
    path("create-intent/", views.create_checkout_session, name="create_checkout"),
    path("success/", views.payment_success, name="payment_success"),
    path("total-create-intent/", views.create_total_checkout_session),
    path("total-success/", views.total_payment_success),
]
