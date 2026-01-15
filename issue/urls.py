from django.urls import path
from . import views

urlpatterns = [
    path("issues/", views.issue_management_view, name="admin_issues"),
    path("books/", views.book_management_view, name="admin_books"),
    path("authors/", views.author_management_view, name="admin_authors"),
    path("fines/", views.fine_management_view, name="admin_fines"),
    path("students/", views.student_management_view, name="admin_students"),
    path("users/", views.user_management_view, name="admin_users"),
    path("books/delete/<int:book_id>/", views.delete_book_view, name="delete_book"),

]
