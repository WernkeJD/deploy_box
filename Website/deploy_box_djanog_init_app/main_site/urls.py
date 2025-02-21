from django.contrib import admin
from django.urls import path, include
from .views import home, stacks, pricing,maintenance
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', home, name="home"),
    path('stacks/', stacks, name="stacks"),
    path('pricing/', pricing, name="pricing"),
    path('contact/', maintenance, name="maintenance"),
    path('signup/', views.signup, name='signup'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),  
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'), 
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)