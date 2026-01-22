import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Fine, Payment
from django.contrib import messages
from django.urls import reverse
from django.db import transaction

stripe.api_key = settings.STRIPE_SECRET_KEY



def create_checkout_session(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    fine_id = request.POST.get("fine_id")

    try:
        with transaction.atomic():
            fine = Fine.objects.select_for_update().get(id=fine_id)

            if fine.is_paid:
                return JsonResponse({
                    "error": f"Fine already paid via {fine.payment_mode}."
                }, status=400)

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                mode="payment",
                line_items=[{
                    "price_data": {
                        "currency": "inr",
                        "unit_amount": int(fine.ammount * 100),
                        "product_data": {
                            "name": "Library Fine Payment",
                        },
                    },
                    "quantity": 1,
                }],
                success_url=settings.BASE_URL + reverse("payment_success") + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=settings.BASE_URL + reverse("stddash"),
                metadata={"fine_id": str(fine.id)},
            )

            payment = Payment.objects.create(
                student=fine.student,
                amount=fine.ammount,
                status="created",
                stripe_payment_intent_id=session.payment_intent,
            )
            payment.fines.add(fine)

        return JsonResponse({"url": session.url})

    except Fine.DoesNotExist:
        return JsonResponse({"error": "Fine not found"}, status=404)

def payment_success(request):
    session_id = request.GET.get("session_id")

    if not session_id:
        messages.error(request, "❌ Payment failed or cancelled.")
        return redirect("stddash")

    session = stripe.checkout.Session.retrieve(session_id)
    fine_id = session.metadata.get("fine_id")

    try:
        with transaction.atomic():
            fine = Fine.objects.select_for_update().get(id=fine_id)

            if fine.is_paid:
                messages.warning(
                    request,
                    f"⚠️ Fine was already paid via {fine.payment_mode}."
                )
                return redirect("stddash")

            fine.is_paid = True
            fine.payment_mode = "online"
            fine.save()

            payment = Payment.objects.filter(fines=fine).latest("created_at")
            payment.status = "succeeded"
            payment.stripe_payment_intent_id = session.payment_intent
            payment.save()

        messages.success(request, "✅ Payment successful! Fine cleared.")
        return redirect("stddash")

    except Fine.DoesNotExist:
        messages.error(request, "❌ Fine not found.")
        return redirect("stddash")

def create_total_checkout_session(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    student = request.user.student

    unpaid_fines = Fine.objects.filter(
        student=student,
        is_paid=False
    )

    if not unpaid_fines.exists():
        return JsonResponse({"error": "No unpaid fines"}, status=400)

    total_amount = sum(f.ammount for f in unpaid_fines)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "inr",
                "unit_amount": int(total_amount * 100),
                "product_data": {
                    "name": "Library – Total Fine Payment",
                },
            },
            "quantity": 1,
        }],
        success_url=(
            settings.BASE_URL +
            reverse("total_payment_success") +
            "?session_id={CHECKOUT_SESSION_ID}"
        ),
        cancel_url=settings.BASE_URL + reverse("stddash"),
    )

    # ✅ Save Payment using SESSION ID
    payment = Payment.objects.create(
        student=student,
        amount=total_amount,
        status="created",
        stripe_session_id=session.id,
    )

    payment.fines.add(*unpaid_fines)

    return JsonResponse({"url": session.url})


def total_payment_success(request):
    session_id = request.GET.get("session_id")

    if not session_id:
        messages.error(request, "Invalid payment session.")
        return redirect("stddash")

    session = stripe.checkout.Session.retrieve(session_id)

    # ✅ Find payment using session ID (SAFE)
    try:
        payment = Payment.objects.get(stripe_session_id=session_id)
    except Payment.DoesNotExist:
        messages.error(request, "Payment record not found.")
        return redirect("stddash")

    # 🛑 Prevent double execution
    if payment.status == "succeeded":
        messages.info(request, "Payment already processed.")
        return redirect("stddash")

    # ✅ Save payment intent AFTER success
    payment.stripe_payment_intent_id = session.payment_intent
    payment.status = "succeeded"
    payment.save()

    # ✅ Mark all fines paid
    payment.fines.update(
        is_paid=True,
        payment_mode="online"
    )

    messages.success(request, "✅ Total fine payment successful!")
    return redirect("stddash")
