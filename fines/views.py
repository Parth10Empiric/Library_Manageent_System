import stripe
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Fine, Payment
from django.views.decorators.http import require_POST
import json

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def create_single_fine_payment(request, fine_id):
    student = request.user.student
    fine = Fine.objects.get(id=fine_id, student=student, is_paid=False)

    intent = stripe.PaymentIntent.create(
        amount=int(fine.ammount * 100),
        currency="inr",
        metadata={
            "fine_id": fine.id,
            "student_id": student.id
        }
    )

    payment = Payment.objects.create(
        student=student,
        stripe_payment_intent_id=intent.id,
        amount=fine.ammount
    )
    payment.fines.add(fine)

    return JsonResponse({
        "client_secret": intent.client_secret,
        "public_key": settings.STRIPE_PUBLIC_KEY
    })


@login_required
def create_total_fine_payment(request):
    student = request.user.student
    fines = Fine.objects.filter(student=student, is_paid=False)

    total_amount = sum(f.ammount for f in fines)

    intent = stripe.PaymentIntent.create(
        amount=int(total_amount * 100),
        currency="inr",
        metadata={"student_id": student.id}
    )

    payment = Payment.objects.create(
        student=student,
        stripe_payment_intent_id=intent.id,
        amount=total_amount
    )
    payment.fines.set(fines)

    return JsonResponse({
        "client_secret": intent.client_secret,
        "public_key": settings.STRIPE_PUBLIC_KEY
    })


@require_POST
@login_required
def confirm_payment(request):
    data = json.loads(request.body)
    intent_id = data.get("payment_intent_id")

    payment = Payment.objects.get(
        stripe_payment_intent_id=intent_id,
        student=request.user.student
    )

    payment.status = "succeeded"
    payment.save()

    payment.fines.update(is_paid=True)

    return JsonResponse({
        "success": True,
        "message": "Payment successful"
    })