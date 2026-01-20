import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Fine, Payment
from django.contrib import messages
from django.urls import reverse

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    fine_id = request.POST.get("fine_id")
    fine = Fine.objects.get(id=fine_id)

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
        success_url = (settings.BASE_URL + reverse("payment_success") + "?session_id={CHECKOUT_SESSION_ID}" ),
        cancel_url = settings.BASE_URL + reverse("stddash"),
        metadata={
            "fine_id": str(fine.id),
        },
    )

    payment = Payment.objects.create(
        student=fine.student,
        stripe_payment_intent_id=session.payment_intent,
        amount=fine.ammount,
        status="created",
    )
    payment.fines.add(fine)

    return JsonResponse({"url": session.url})



def payment_success(request):
    session_id = request.GET.get("session_id")

    if not session_id or session_id.startswith("{"):
        return render(request, "payment_failed.html")

    session = stripe.checkout.Session.retrieve(session_id)

    fine_id = session.metadata.get("fine_id")
    fine = Fine.objects.get(id=fine_id)

    # ✅ Mark fine paid
    fine.is_paid = True
    fine.payment_mode = "online"
    fine.save()

    # ✅ Get the correct Payment using fine relation
    payment = Payment.objects.filter(fines=fine).latest("created_at")

    # ✅ Update payment details
    payment.stripe_payment_intent_id = session.payment_intent
    payment.status = "succeeded"
    payment.save()

    messages.success(request, "✅ Payment successful! Fine has been cleared.")

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

    # 🔐 Stripe minimum safeguard
    if total_amount < 50:
        total_amount = 50

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
        success_url = (settings.BASE_URL + reverse("payment_success") + "?session_id={CHECKOUT_SESSION_ID}" ),
        cancel_url = settings.BASE_URL + reverse("stddash"),
        metadata={
            "fine_ids": ",".join(str(f.id) for f in unpaid_fines),
        },
    )

    payment = Payment.objects.create(
        student=student,
        amount=total_amount,
        status="created",
    )
    payment.fines.add(*unpaid_fines)

    return JsonResponse({"url": session.url})

def total_payment_success(request):
    session_id = request.GET.get("session_id")

    if not session_id or session_id.startswith("{"):
        return redirect("stddash")

    session = stripe.checkout.Session.retrieve(session_id)

    fine_ids = session.metadata.get("fine_ids", "")
    fine_ids = fine_ids.split(",")

    fines = Fine.objects.filter(id__in=fine_ids)

    fines.update(is_paid=True, payment_mode="online")

    payment = Payment.objects.filter(fines__in=fines).latest("created_at")
    payment.status = "succeeded"
    payment.stripe_payment_intent_id = session.payment_intent
    payment.save()

    from django.contrib import messages
    messages.success(request, "✅ Total fine payment successful!")

    return redirect("stddash")
