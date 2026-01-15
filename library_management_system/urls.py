"""
URL configuration for library_management_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from account import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', views.home_view, name="home" ),
    path('auth/', include("account.urls")),
    path('stddash/', views.std_dashbord_view, name="stddash" ),
    path('admindash/', views.admin_dashbord_view, name="admindash" ),
    path('book_req/<int:book_id>/', views.request_issue, name='request_issue'), 
    path('admindash/manage/', include("issue.urls")),
    path('logout/', views.logout_view, name="logout"),
    
]
