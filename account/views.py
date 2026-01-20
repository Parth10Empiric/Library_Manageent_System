from django.shortcuts import render, redirect, get_object_or_404
from book.models import Book, Author, Category
from issue.models import Issue
from fines.models import Fine
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import Student
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_GET
from library_management_system import settings
from fines.utils import update_fines

# Create your views here.

def login_view(request):
    if request.user.is_authenticated:
        if user.is_staff:
            return redirect('admindash')
        else:
            return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username= username, password = password)

        if user is not None:
            login(request, user)
            messages.success(request, "login successfully")

            if user.is_staff:
                return redirect('admindash')
            else:
                return redirect('home')
            
        else:
            messages.error(request, "Invalid Username & Password")
            return render(request,"auth/login.html")

    return render(request,"auth/login.html")

def home_view(request):
    books = Book.objects.all()

    title = request.GET.get('s_title')
    author = request.GET.get('s_author')
    category = request.GET.get('s_category')
    sort = request.GET.get('sort')

    if title:
        books = books.filter(title__icontains=title)
    if author:
        books = books.filter(author__name__icontains = author)
    if category:
        books = books.filter(category__name__icontains = category)

    if sort == 'name_asc':
        books = books.order_by('title')
    elif sort == 'author_asc':
        books = books.order_by('author')
    else:
        books = books.order_by('-id')

    paginator = Paginator(books, 9) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.user.is_authenticated and not request.user.is_staff:
        student = Student.objects.get(user=request.user)
        issues = Issue.objects.filter(student=student)

        issue_dict = {issue.book_id: issue.status for issue in issues}

        for book in page_obj:
            book.student_issue_status = issue_dict.get(book.id)
    else:
        for book in page_obj:
            book.student_issue_status = None

    context = {
        "books": page_obj,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string("book_list.html", context, request=request)
        return JsonResponse({"html":html})
    
    return render(request, "home.html", context)

@require_GET
def book_detail_by_title(request):
    title = request.GET.get("title")
    book = Book.objects.select_related("author", "category").get(title=title)
    return JsonResponse({
        "author": book.author.name,
        "category": book.category.name,
    })

@require_GET
def smart_search(request):
    term = request.GET.get("term", "")
    author = request.GET.get("author")
    category = request.GET.get("category")
    search_type = request.GET.get("type")

    books = Book.objects.select_related("author", "category")

    if author:
        books = books.filter(author__name=author)

    if category:
        books = books.filter(category__name=category)

    if search_type == "title":
        titles = books.filter(title__icontains=term).values_list("title", flat=True).distinct()
        return JsonResponse(list(titles[:10]), safe=False)

    if search_type == "author":
        authors = Author.objects.filter(name__icontains=term).values_list("name", flat=True).distinct()
        if category:
            authors = authors.filter(book__category__name=category)
        return JsonResponse(list(authors[:10]), safe=False)

    if search_type == "category":
        categories = Category.objects.filter(name__icontains=term).values_list("name", flat=True).distinct()
        return JsonResponse(list(categories[:10]), safe=False)

    return JsonResponse([], safe=False)

def suggest_book(request):
    query = request.GET.get('term', '')
    if query:
        books = Book.objects.filter(title__icontains=query).values_list('title',flat=True)
        return JsonResponse(list(books), safe=False)
    return JsonResponse([], safe=False)


# add student
@staff_member_required
def add_student_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        name = request.POST.get('name')
        studentId = request.POST.get('student_id')
        department = request.POST.get('department')
        phone = request.POST.get('phone')

        if User.objects.filter(username=username).exists():
            messages.error(request, "user alredy available")
        elif Student.objects.filter(sudent_id= studentId).exists():
            messages.error(request, "UserId available")
        else:
            new_user = User.objects.create_user(username=username, password=password)

            Student.objects.create(
                user = new_user,
                sudent_id = studentId,
                department = department,
                name = name,
                phone = phone,
            )
            messages.success(request, "Add Student successfully")
            return redirect('admindash')
        
    return render(request, "auth/addstudent.html")




# dashboed
def std_dashbord_view(request):
    update_fines()
    student = Student.objects.get(user = request.user)
    issues = Issue.objects.filter(student = student).select_related('book')
    unpaid_fine = Fine.objects.filter(student = student, is_paid=False)
    total_fine = unpaid_fine.aggregate(
        totle = Sum('ammount')
    )['totle'] or 0

    status_filter = request.GET.get('status','all')
    if status_filter == 'issued':
        issues = issues.filter(status='issued')
    elif status_filter == 'requested':
        issues = issues.filter(status='requested')

    contex = {
        'student': student,
        'issues':issues,
        'unpaid_fine': unpaid_fine,
        'totle_fine': total_fine,
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'dashbord/partials/issue_rows.html', contex)
    return render(request, "dashbord/student_dashbord.html", contex)

@staff_member_required
def admin_dashbord_view(request):
    return render(request, "dashbord/admin_dashbord.html")

# def request_issue(request, book_id):
#     book = get_object_or_404(Book, id=book_id)
#     book.is_registered = True
#     book.save()
#     messages.success(request, "Request Sent")
#     return JsonResponse({'status': 'success'})


@login_required
def request_issue(request, book_id):
    student = Student.objects.get(user=request.user)
    book = get_object_or_404(Book, id=book_id)

    Issue.objects.create(
        student=student,
        book=book,
        status='requested'
    )

    return JsonResponse({
        'status': 'success',
        'message': 'Request sent'
    })

@login_required
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('home')