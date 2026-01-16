from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from .models import Issue
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from book.models import Book, Author, Category
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Count

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
            "admin/partials/admin_issue_rows.html",
            {"issues": issues},
            request=request
        )
        return JsonResponse({"html": html})

    return render(request, "admin/issue_management.html", {'issues': issues})

@staff_member_required
def book_management_view(request):
    books_qs = Book.objects.all().order_by('-id')

    search_w = request.GET.get("w")

    if search_w:
        books_qs = books_qs.filter(
            Q(title__icontains=search_w) |
            Q(author__name__icontains=search_w)
        )

    paginator = Paginator(books_qs, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        rows_html = render_to_string(
            "admin/partials/admin_book_rows.html",
            {"books":page_obj},
            request=request
        )

        pagination_html = render_to_string(
            "admin/partials/admin_book_pagination.html",
            {"books":page_obj},
            request=request
        )
            
        return JsonResponse({
            "rows":rows_html,
            "pagination":pagination_html,   
        })
    
    return render(request, "admin/book_management.html", {"books":page_obj})

@staff_member_required
@require_POST
def delete_book_view(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    book.delete()
    return JsonResponse({"status":"success"})

@staff_member_required
@require_POST
def delete_author_view(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    author.delete()
    return JsonResponse({"status":"success"})

@staff_member_required
def author_management_view(request):
    authors = Author.objects.annotate(book_count=Count('book')).exclude(name__contains=';')

    search_w = request.GET.get("w")

    if search_w:
        authors = authors.filter(name__icontains=search_w)

    paginator = Paginator(authors, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        row_html = render_to_string(
            "admin/partials/admin_author_rows.html",
            {"authors":page_obj},
            request=request
        )
        pagination_html = render_to_string(
            "admin/partials/admin_author_pagination.html",
            {"authors":page_obj},
            request=request
        )
            
        return JsonResponse({
            "rows":row_html,
            "pagination":pagination_html
            })
    
    return render(request, "admin/author_management.html", {"authors":page_obj})

@staff_member_required
def fine_management_view(request):
    return render(request, "admin/fine_management.html")

@staff_member_required
def student_management_view(request):
    return render(request, "admin/student_management.html")

@staff_member_required
def user_management_view(request):
    return render(request, "admin/user_management.html")

@staff_member_required
def add_book_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        author_name = request.POST.get('author')
        category_name = request.POST.get('category')

        author, _ = Author.objects.get_or_create(name = author_name.strip())
        category, _ = Category.objects.get_or_create(name = category_name.strip())
        Book.objects.create(
            title = title,
            author = author,
            category = category,
        )
        messages.success(request, "Book Added Succesfully")
        return redirect('admindash')

    return render(request, "admin/partials/add_book.html")