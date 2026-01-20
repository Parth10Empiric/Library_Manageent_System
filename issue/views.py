from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from .models import Issue
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q, Count, Sum
from book.models import Book, Author, Category
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib import messages
from account.models import Student
from fines.models import Fine, Payment
import json

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
            issue.book.is_registered = False
            issue.book.save()

        elif action == 'return':
            issue.status = 'returned'
            issue.return_date = now().date()
            issue.book.is_available = True
            issue.book.is_registered = False
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
def author_detail(request, author_id):
    author = Author.objects.get(id=author_id)
    books = Book.objects.filter(author=author)

    data = {
        "name": author.name,
        "book_count": books.count(),
        "books": list(books.values_list('title', flat=True))
    }

    return JsonResponse(data)

@staff_member_required
def fine_management_view(request):
    fines = Fine.objects.all()

    bookword = request.GET.get("bookword")
    stdword = request.GET.get("stdword")
    finestatus = request.GET.get("finestatus")

    if finestatus:
        if finestatus == "paid":
            fines = fines.filter(is_paid=True)

        if finestatus == "unpaid":
            fines=fines.filter(is_paid=False)
    
    if stdword:
        fines = fines.filter(
            Q(student__sudent_id__icontains=stdword) |
            Q(student__user__username__icontains=stdword)
        )

    if bookword:
        fines = fines.filter(
            Q(issue__book__title__icontains=bookword)
        )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string(
            "admin/partials/fines_rows.html",
            {"fines":fines},
            request=request
        )
        return JsonResponse({"html": html})
    
    return render(request, "admin/fine_management.html", {"fines":fines})


@staff_member_required
@require_POST
def toggle_cash_payment(request, fine_id):
    fine = get_object_or_404(Fine, id=fine_id)

    data = json.loads(request.body.decode("utf-8"))
    is_paid = data.get("is_paid")

    if is_paid:
        print("llllllllllllllllll")
        fine.is_paid = True
        fine.payment_mode = "cash"
    else:
        print("ffffffffffffffffffffffffff")
        fine.is_paid = False
        fine.payment_mode = None

    fine.save()

    row_html = render_to_string(
        "admin/partials/fines_rows.html",
        {"fines": [fine]},
        request=request
    )

    return JsonResponse({
        "success": True,
        "fine_id": fine.id,
        "row_html": row_html
    })


@staff_member_required
def student_management_view(request):
    students = Student.objects.select_related('user').annotate(
        issue_count = Count('issue', filter = Q(issue__status = 'issued'),distinct = True),
        totle_fine = Sum('issue__fine__ammount', filter= Q(issue__fine__is_paid=False))
    )

    department_query = request.GET.get("department")
    search_w = request.GET.get("w")

    if department_query:
        students = students.filter(department=department_query)
    
    if search_w:
        students = students.filter(
            Q(sudent_id__icontains=search_w) |
            Q(user__username__icontains=search_w)
        )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string(
            "admin/partials/students_rows.html",
            {"students": students},
            request=request
        )
        return JsonResponse({"html": html})

    return render(request, "admin/student_management.html", {"students":students})

@staff_member_required
@require_POST
def delete_student_view(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    user = student.user
    user.delete()
    # student.delete()
    return JsonResponse({"status":"success"})

@staff_member_required
def edit_student_view(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":

        if Student.objects.filter(sudent_id= request.POST.get("student_id")).exclude(id=student.id).exists():
            messages.error(request, "StudentId alredy available")
        else :
            student.sudent_id = request.POST.get("student_id")
            student.name = request.POST.get("name")
            student.department = request.POST.get("department")
            student.user.email = request.POST.get("email")

            student.user.save()
            student.save()
        
            messages.success(request, "Student details updated successfully.")
            return redirect("admindash")
    
    return render(request, "admin/edit_student.html", {"student":student})

@staff_member_required
def user_management_view(request):
    allusers = User.objects.all()

    status_query = request.GET.get("status")
    roll_query = request.GET.get("roll")
    search_w = request.GET.get("w")

    if status_query:
        if status_query == "active":
            allusers = allusers.filter(is_active=True)
        elif status_query == "inactive":
            allusers = allusers.filter(is_active=False)

    if roll_query:
        if roll_query == "admin":
            allusers = allusers.filter(is_superuser=True)

        elif roll_query == "staff":
            allusers = allusers.filter(is_staff=True, is_superuser=False)

        elif roll_query == "student":
            allusers = allusers.filter(is_staff=False, is_superuser=False)
    
    if search_w:
        allusers = allusers.filter(
            Q(username__icontains=search_w) 
        )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string(
            "admin/partials/user_row.html",
            {"allusers": allusers},
            request=request
        )
        return JsonResponse({"html": html})
    return render(request, "admin/user_management.html", {"allusers":allusers})

@staff_member_required
def user_changepassword_view(request, ouserid):

    ouser = get_object_or_404(User, id=ouserid)

    if request.method == 'POST':
        password = request.POST.get('password')
        cpassword = request.POST.get('cpassword')

        if password != cpassword:
            messages.error(request, "Password must be same")
        else:
            ouser.set_password(password)
            ouser.save()
            messages.success(request, "Password Change Successfully")
            return redirect("admindash")
    return render(request, "admin/partials/changepassword.html",{"ouser":ouser})

@staff_member_required
@require_POST
def add_book_view(request):
    title = request.POST.get('title')
    author_name = request.POST.get('author')
    category_name = request.POST.get('category')

    if not title or not author_name or not category_name:
       return JsonResponse({
           "success": False,
           "message": "All fields are required"
       }, status=400)
    
    author, _ = Author.objects.get_or_create(name = author_name.strip())
    category, _ = Category.objects.get_or_create(name = category_name.strip())
    Book.objects.create(
        title = title,
        author = author,
        category = category,
    )
    return JsonResponse({
       "success": True,
       "message": "Book added successfully"
    })
