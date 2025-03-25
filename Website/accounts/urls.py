from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import include

urlpatterns = [
    path("protected-view", views.protected_view, name="protected_view"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("callback/", views.oauth2_callback, name="callback"),
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
]
