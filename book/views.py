from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import Book

# Create your views here.

# def request_issue(request, book_id):
#     book = get_object_or_404(Book, id=book_id)
#     book.is_register = True
#     book.save()
#     messages.success(request, "Request Sent")
#     return render(request, 'home.html')
#     return redirect('home')