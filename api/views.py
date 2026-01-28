from django.contrib.auth import authenticate, login
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.utils.timezone import now
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.transaction import atomic

from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView, CreateAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework.mixins import ListModelMixin, UpdateModelMixin

from .serializers import StudentFineSerializer, BookSerializer, UserSerializer, CardInformationSerializer, PaymentSerializer, IssueSerializer, FineSerializer, StudentSerializer, Issue, AuthorSerializer
from .permissions import IsStudent, IsAdminOrStudentRequest, IsAdmin
from library_management_system import settings
from book.models import Author, Book
from fines.models import Fine, Payment
from account.models import Student, User

import stripe

# Create your views here.

class LoginAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = authenticate(
            username=request.data.get('username'),
            password=request.data.get('password')
        )
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            
            login(request, user)   
            return Response({
                "message": "Login successful",
                "token": token.key,
            }, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class BookViewSet(ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrStudentRequest] 
    
    filterset_fields = {
        'title': ['icontains'],
        'author': ['exact'],
        'category': ['exact'],
    }

    @action(detail=True, methods=['GET'], url_path='request-issue')
    def request_issue(self, request, pk=None):
        book = self.get_object()
        
        if request.user.is_staff:
            return Response(
                {"error": "Staff members are not allowed to request books."}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        student = get_object_or_404(Student, user=request.user)
        
        if not book.is_available:
            return Response({'error': 'Book is already issued'}, status=status.HTTP_400_BAD_REQUEST)
            
        if book.is_registered:
            return Response({'error': 'Book is already requested'}, status=status.HTTP_400_BAD_REQUEST)

        book.is_registered = True
        book.save()
        
        Issue.objects.create(
            student=student,
            book=book,
            status='requested'
        )
        
        return Response({
            'status': 'success', 
            'message': f'Issue request for "{book.title}" sent successfully.'
        }, status=status.HTTP_201_CREATED)
    
class StudentDashbordViewSet(ListModelMixin, GenericViewSet):
    serializer_class = IssueSerializer
    permission_classes = [IsStudent]
    
    def get_queryset(self):
        student = get_object_or_404(Student, user = self.request.user)
        queryset = Issue.objects.filter(student=student).select_related('book')
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        student = get_object_or_404(Student, user=request.user)
        
        unpaid_fine = Fine.objects.filter(student=student, is_paid=False)
        aggregation = unpaid_fine.aggregate(total=Sum('ammount'))
        total_fine = aggregation['total'] or 0

        return Response({
            'issues': serializer.data,
            'total_fine': total_fine,
            'unpaid_fines': FineSerializer(unpaid_fine, many=True).data,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
            'student_id': student.id
        })

class StudentViewSet(ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAdmin]
    
    filterset_fields = {
        'sudent_id': ['icontains'],
        'department': ['exact'],
    }
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        password = request.data.get('password')
        
        try:
            validate_password(password)
        except ValidationError as e:
            return Response({"Password-Error":list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
            
        username = serializer.validated_data.pop('username')
        if User.objects.filter(username=username).exists():
            return Response({"username-error":"Username Alredy Exist"})
        password = serializer.validated_data.pop('password')
        
        user = User.objects.create_user(username=username, password=password)
        serializer.save(user=user)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
class AuthorViewSet(ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAdmin]
    
class UserViewSet(ListModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    
    @action(detail=True, methods=['post'])
    def set_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get("password")
        if not new_password:
            return Response({"error": "Password is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validate_password(new_password)
        except ValidationError as e:
            return Response({"Password-Error":list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        return Response({"status": "password set successfully"})

class IssueViewSet(ModelViewSet):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    permission_classes = [IsAdmin]
    
    filterset_fields = {
        'status': ['exact'],
    }
    
    http_method_names = ['get']
    
    @action(detail=True, methods=['get'], url_path='mark-issue')
    def issue(self, request, pk=None):
        issue = self.get_object()
        
        if not request.user.is_staff:
            return Response(
                {"error": "Only Staff members are allowed to Issued books."}, 
                status=status.HTTP_403_FORBIDDEN
            )
                    
        if issue.status == 'issued':
            return Response({'error': 'Book is already issued'}, status=status.HTTP_400_BAD_REQUEST)
            
        if issue.status == 'returned':
            return Response({'error': 'Book is Alredy Returned, You can not perform any action'}, status=status.HTTP_400_BAD_REQUEST)

        issue.status = 'issued'
        issue.issue_date = now().date()
        issue.book.is_available = False
        issue.book.is_registered = False
        issue.book.save()
        issue.save()
                               
        return Response({
            'status': 'success', 
            'message': f'Book "{issue.book.title}" issued successfully.'
        }, status=status.HTTP_201_CREATED)
        
    @action(detail=True, methods=['get'], url_path='mark-return')
    def mark_return(self, request, pk=None):
        issue = self.get_object()
        
        if not request.user.is_staff:
            return Response(
                {"error": "Only Staff members are allowed to Issued books."}, 
                status=status.HTTP_403_FORBIDDEN
            )
                    
        if issue.status == 'requested':
            return Response({'error': 'Book is not issued, issue first'}, status=status.HTTP_400_BAD_REQUEST)
            
        if issue.status == 'returned':
            return Response({'error': 'Book is Alredy Returned, You can not perform any action'}, status=status.HTTP_400_BAD_REQUEST)

        issue.status = 'returned'
        issue.return_date = now().date()
        issue.book.is_available = True
        issue.book.is_registered = False
        issue.book.save()
        issue.save()
                               
        return Response({
            'status': 'success', 
            'message': f'Book "{issue.book.title}" returned successfully.'
        }, status=status.HTTP_201_CREATED)
    
    
class FineViewSet(ModelViewSet):
    queryset = Fine.objects.all()
    serializer_class = FineSerializer
    permission_classes = [IsAdmin]
    
    http_method_names = ['get']
    
    filterset_fields = {
        'is_paid': ['exact'],
        'payment_mode': ['exact'],
    }
    
    @action(detail=True, methods=['get'], url_path='paid-cash')
    def paid_cash(self, request, pk=None):
        fine = self.get_object()
        
        if fine.is_paid:
            return Response({
                "success": False,
                "message": f'Fine already paid By "{fine.payment_mode}".'
            }, status=status.HTTP_400_BAD_REQUEST)

        fine.is_paid = True
        fine.payment_mode = "cash"
        fine.save()
                               
        return Response({
            'status': 'success', 
            'message': f'Fine "{fine.ammount}" Paid By "{fine.payment_mode}" successfully.'
        }, status=status.HTTP_200_OK)
        
    

# class PaymentAPI(APIView):
#     serializer_class = CardInformationSerializer

#     def post(self, request, fine_id): 
#         serializer = self.serializer_class(data=request.data)
#         response_data = {}
        
#         if serializer.is_valid():
#             data_dict = serializer.data
            
#             try:
#                 fine = get_object_or_404(Fine, pk=fine_id)
#             except Fine.DoesNotExist:
#                 return Response(
#                     {'error': 'Fine not found.', 'status': status.HTTP_404_NOT_FOUND},
#                     status=status.HTTP_404_NOT_FOUND
#                 )
            
#             if fine.is_paid:
#                 return Response({
#                     "success": False,
#                     "message": f'Fine already paid By "{fine.payment_mode}".'
#                 }, status=status.HTTP_400_BAD_REQUEST)
                
#             stripe.api_key = settings.STRIPE_PUBLIC_KEY
            
#             transaction_result = self.stripe_card_payment(data_dict=data_dict, fine_amount=fine.ammount)
            
#             if transaction_result.get('status') == status.HTTP_200_OK:
#                 fine.is_paid = True
#                 fine.payment_mode = "online" 
#                 fine.save()
#                 transaction_result['message'] = f"Online Payment Success for Fine ID {fine_id}."
                
#             response_data = transaction_result

#         else:
#             response_data = {
#                 'errors': serializer.errors, 
#                 'status': status.HTTP_400_BAD_REQUEST
#             }
                
#         return Response(response_data, status=response_data.get('status'))

#     def stripe_card_payment(self, data_dict, fine_amount): 
#         # Stripe expects amounts in the lowest common denominator (e.g., paise for INR)
#         amount_in_lowest_unit = int(float(fine_amount) * 100) 

#         response = {}
#         try:
#             # 1. Create a Payment Method securely on Stripe's server
#             payment_method = stripe.PaymentMethod.create(
#                 type="card",
#                 card={
#                     "number": data_dict['card_number'],
#                     "exp_month": data_dict['expiry_month'],
#                     "exp_year": data_dict['expiry_year'],
#                     "cvc": data_dict['cvc'],
#                 },
#             )

#             # 2. Create the Payment Intent with the correct amount
#             payment_intent = stripe.PaymentIntent.create(
#                 amount=amount_in_lowest_unit, 
#                 currency='inr', 
#                 payment_method=payment_method.id,
#                 confirm=True, 
#                 description=f"Payment for Fine Amount {fine_amount}", 
#             )
            
#             if payment_intent.status == 'succeeded':
#                 response = {
#                     'message': "Card Payment Success",
#                     'status': status.HTTP_200_OK,
#                     "payment_intent_id": payment_intent.id,
#                     "amount_paid": fine_amount
#                 }
#             elif payment_intent.status == 'requires_action':
#                  # Handle 3D Secure or other required actions (requires front-end integration)
#                  response = {
#                     'message': "Payment requires user action (e.g., 3DS authentication).",
#                     'status': status.HTTP_402_PAYMENT_REQUIRED,
#                     "client_secret": payment_intent.client_secret
#                 }
#             else:
#                 response = {
#                     'message': f"Card Payment Failed: Status is {payment_intent.status}",
#                     'status': status.HTTP_400_BAD_REQUEST,
#                     'last_error': payment_intent.last_payment_error.message if payment_intent.last_payment_error else 'Unknown Error'
#                 }
        
#         except stripe.error.CardError as e:
#             # Handle specific Stripe card errors
#             response = {
#                 'error': f"Stripe Card Error: {e.user_message}",
#                 'code': e.code,
#                 'status': status.HTTP_400_BAD_REQUEST,
#             }
#         except stripe.error.StripeError as e:
#             # Handle other general Stripe API errors
#              response = {
#                 'error': f"Stripe API Error: {str(e)}",
#                 'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
#             }
#         except Exception as e:
#             # Handle unexpected errors
#             response = {
#                 'error': f"An unexpected error occurred: {str(e)}",
#                 'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
#             }
        
#         return response

class StudentFineViewSet(ModelViewSet):
    serializer_class = StudentFineSerializer
    permission_classes = [IsStudent]
    
    http_method_names = ['get']
    
    def get_queryset(self):
        student = get_object_or_404(Student, user = self.request.user)
        queryset = Fine.objects.filter(student=student)
        
        return queryset
    
    @action(detail=True, methods=['get', 'post'], url_path='pay-online')
    def pay_online(self, request, pk=None):
        fine = self.get_object()
        
        if fine.is_paid:
            return Response({
                "success": False,
                "message": f'Fine already paid By "{fine.payment_mode}".'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = CardInformationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        stripe.api_key = settings.STRIPE_SECRET_KEY
        data = serializer.validated_data
        
        try:
            stripe_amount = int(fine.ammount * 100)
            
            # pm = stripe.PaymentMethod.create(
            #     type="card",
            #     card={
            #         "number": data['card_number'],
            #         "exp_month": data['expiry_month'],
            #         "exp_year": data['expiry_year'],
            #         "cvc": data['cvc'],
            #     },
            # )
            pm = stripe.PaymentMethod.create(
                type="card",
                card={"token": request.data.get('card_number')}, 
            )
            
            intent = stripe.PaymentIntent.create(
                amount=stripe_amount,
                currency='inr',
                payment_method=pm.id,
                confirm=True,
                off_session=True,
            )
            
            if intent.status == 'succeeded':
                with atomic():
                    payment_record = Payment.objects.create(
                        student=fine.student,
                        stripe_payment_intent_id=intent.id,
                        amount=fine.ammount,
                        status="succeeded"
                    )
                    payment_record.fines.add(fine)

                    fine.is_paid = True
                    fine.payment_mode = "online"
                    fine.save()

                return Response({
                    "message": f'"{fine.ammount}" Payment successful',
                    "intent_id": intent.id
                }, status=status.HTTP_200_OK)

            return Response({"error": f"Payment status: {intent.status}"}, status=status.HTTP_400_BAD_REQUEST)

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

