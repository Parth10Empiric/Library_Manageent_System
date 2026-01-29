from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginAPI,
    BookViewSet,
    StudentDashbordViewSet,
    StudentViewSet,
    AuthorViewSet,
    UserViewSet,
    IssueViewSet,
    FineViewSet,
    StudentFineViewSet
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

router = DefaultRouter()
router.register(r'books', BookViewSet, basename='bookdata')
router.register(r'stddashbord', StudentDashbordViewSet, basename='stddashbord')
router.register(r'student', StudentViewSet, basename='student')
router.register(r'Author', AuthorViewSet, basename='author')
router.register(r'user', UserViewSet, basename='user')
router.register(r'issue', IssueViewSet, basename='issue')
router.register(r'fine', FineViewSet, basename='fine')
router.register(r'stdfine', StudentFineViewSet, basename='stdfine')

urlpatterns = [
    path('login/', LoginAPI.as_view()),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
]
