from django.urls import path, include
from . import views

urlpatterns = [
    path("pay/fine/<int:fine_id>/", views.create_single_fine_payment),
    path("pay/fine/all/", views.create_total_fine_payment),
    path("payment/confirm/", views.confirm_payment),
]
