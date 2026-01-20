from django.urls import path
from . import views

urlpatterns = [
    path("issues/", views.issue_management_view, name="admin_issues"),
    path("books/", views.book_management_view, name="admin_books"),
    path("books/addBook", views.add_book_view, name="add_book"),
    path("authors/", views.author_management_view, name="admin_authors"),
    path("fines/", views.fine_management_view, name="admin_fines"),
    path("fines/<int:fine_id>/toggle-cash/", views.toggle_cash_payment, name="toggle_cash_payment"),
    path("students/", views.student_management_view, name="admin_students"),
    path("users/", views.user_management_view, name="admin_users"),
    path("users/changepassword/<int:ouserid>", views.user_changepassword_view, name="changepassword"),
    path("books/delete/<int:book_id>/", views.delete_book_view, name="delete_book"),
    path("authors/delete/<int:author_id>/", views.delete_author_view, name="delete_author"),
    path("students/delete/<int:student_id>/", views.delete_student_view, name="delete_student"),
    path("students/edit/<int:student_id>/", views.edit_student_view, name="editstudent"),

]
