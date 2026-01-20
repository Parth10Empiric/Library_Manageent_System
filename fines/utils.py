from datetime import date
from .models import Fine

FINE_PER_DAY = 35


def update_fines():
    from issue.models import Issue

    today = date.today()

    overdue_issues = Issue.objects.filter(
        status="issued",
        return_date__lt=today
    )

    for issue in overdue_issues:
        days_late = (today - issue.return_date).days
        amount = days_late * FINE_PER_DAY

        fine, created = Fine.objects.get_or_create(
            issue=issue,
            defaults={
                "student": issue.student,
                "ammount": amount,
            }
        )

        if not created and not fine.is_paid:
            fine.ammount = amount
            fine.save()
