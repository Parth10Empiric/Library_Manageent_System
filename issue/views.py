from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import Issue
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q


# Create your views here.

@staff_member_required
def issue_management_view(request):

    issues = Issue.objects.select_related('student', 'book').all()

    issue_id = request.GET.get("issue_id")
    action = request.GET.get("action")
    status_query = request.GET.get("status")
    search_w = request.GET.get("w")

    if search_w:
        issues = issues.filter(
            Q(student__name__icontains=search_w) |
            Q(student__user__username__icontains=search_w)
        )

    if status_query:
        issues = issues.filter(status=status_query)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and issue_id and action:
        issue = get_object_or_404(Issue, id=issue_id)

        if action == 'issue':
            issue.status = 'issued'
            issue.issue_date = now().date()
            issue.book.is_available = False
            issue.book.save()

        elif action == 'return':
            issue.status = 'returned'
            issue.return_date = now().date()
            issue.book.is_available = True
            issue.book.save()

        issue.save()

        return JsonResponse({
            "status": "success",
            "new_status_raw": issue.status,
            "issue_date": issue.issue_date.strftime("%d-%b-%Y") if issue.issue_date else "-",
            "return_date": issue.return_date.strftime("%d-%b-%Y") if issue.return_date else "-",
        })
    
    elif request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string(
            "dashbord/partials/issue_rows.html",
            {"issues": issues},
            request=request
        )
        return JsonResponse({"html": html})

    return render(request, "admin/issue_management.html", {'issues': issues})

@staff_member_required
def book_management_view(request):
    return render(request, "admin/book_management.html")

@staff_member_required
def author_management_view(request):
    return render(request, "admin/author_management.html")

@staff_member_required
def fine_management_view(request):
    return render(request, "admin/fine_management.html")

@staff_member_required
def student_management_view(request):
    return render(request, "admin/student_management.html")

@staff_member_required
def user_management_view(request):
    return render(request, "admin/user_management.html")