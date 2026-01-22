from django.urls import path
from . import views

urlpatterns = [
    path("create-intent/", views.create_checkout_session, name="create_checkout"),
    path("success/", views.payment_success, name="payment_success"),
    path("create-total-intent/", views.create_total_checkout_session, name="create_total_payment_intent"),
    path("total-success/", views.total_payment_success, name="total_payment_success"),
]
