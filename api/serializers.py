from rest_framework.serializers import Serializer, ModelSerializer, ValidationError, BooleanField, SerializerMethodField, CharField

from account.models import Student, User
from book.models import Author, Book, Category
from fines.models import Fine, Payment
from issue.models import Issue

import datetime


class UserSerializer(ModelSerializer):
    status = BooleanField(source='is_active', read_only=True)
    role = SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'last_login', 'date_joined', 'status']

    def get_role(self, obj):
        if obj.is_superuser: return "admin"
        if obj.is_staff: return "staff"
        return "student"
    
class StudentSerializer(ModelSerializer):
    username = CharField(write_only=True)
    password = CharField(write_only=True, style={'input_type': 'password'})
    class Meta:
        model = Student
        fields = ['id', 'sudent_id', 'department', 'name', 'phone', 'created_at', 'username', 'password']
        read_only_fields = ['sudent_id', 'created_at']
        
class BookSerializer(ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'category', 'is_available', 'is_registered']
        read_only_fields = ['is_Available', 'is_registered']
        
class AuthorSerializer(ModelSerializer):
    books = BookSerializer(read_only=True, many=True)
    class Meta:
        model = Author
        fields = ['id', 'name', 'books']
        
class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class FineSerializer(ModelSerializer):
    class Meta:
        model = Fine
        fields = ['id', 'ammount', 'is_paid', 'created_at', 'payment_mode', 'student', 'issue']
        read_only_fields = ['student', 'issue']
        
class StudentFineSerializer(ModelSerializer):
    class Meta:
        model = Fine
        fields = ['id', 'ammount', 'is_paid', 'created_at', 'payment_mode', 'issue']
        read_only_fields = ['issue']
        
class IssueSerializer(ModelSerializer):
    student = StudentSerializer(read_only=True)
    book = BookSerializer(read_only=True)
    fine = FineSerializer(read_only=True)
    class Meta:
        model = Issue
        fields = ['id', 'student', 'book', 'status', 'issue_date', 'return_date', 'fine']
        read_only_fields = ['student', 'status']

class PaymentSerializer(ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        
def check_expiry_month(value):
    if not 1 <= int(value) <= 12:
        raise ValidationError("Invalid expiry month.")


def check_expiry_year(value):
    today = datetime.datetime.now()
    if not int(value) >= today.year:
        raise ValidationError("Invalid expiry year.")


def check_cvc(value):
    if not 3 <= len(value) <= 4:
        raise ValidationError("Invalid cvc number.")


def check_payment_method(value):
    payment_method = value.lower()
    if payment_method not in ["card"]:
        raise ValidationError("Invalid payment_method.")

class CardInformationSerializer(Serializer):
    card_number = CharField(max_length=150, required=True)
    expiry_month = CharField(
        max_length=150,
        required=True,
        validators=[check_expiry_month],
    )
    expiry_year = CharField(
        max_length=150,
        required=True,
        validators=[check_expiry_year],
    )
    cvc = CharField(
        max_length=150,
        required=True,
        validators=[check_cvc],
    )