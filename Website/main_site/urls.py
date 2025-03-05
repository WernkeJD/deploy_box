from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('stacks/', views.stacks, name="stacks"),
    path('pricing/', views.pricing, name="pricing"),
    path('contact/', views.maintenance, name="maintenance"),
    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),  
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/validate-token/', views.validate_token, name='validate-token'),
    path('verify_user_credentials/', views.verify_user_credentials, name='verify_user_credentials'), 
    path('get_container_access/', views.get_container_access, name='get_container_access'),
    path("me/", views.user_info, name="user-info"),
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)