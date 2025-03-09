from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('stacks/', views.stacks, name="stacks"),
    path('', views.home, name="home"),
    path('pricing/', views.pricing, name="pricing"),
    path('contact/', views.maintenance, name="maintenance"),
    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/validate-token/', views.validate_token, name='validate-token'),
    path('api/get_available_stacks', views.get_available_stacks, name='get_available_stacks'),
    path('api/get_available_deployments', views.get_available_deployments, name='get_available_deployments'),
    path('api/add_stack', views.add_stack, name='add_stack'),
    path('api/upload_deployment', views.upload_deployment, name='upload_deployment'),
    path('api/download_stack/<int:stack_id>', views.download_stack, name='download_stack'),
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)