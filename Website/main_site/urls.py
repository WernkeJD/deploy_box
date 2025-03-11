from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("stacks/", views.stacks, name="stacks"),
    path("pricing/", views.pricing, name="pricing"),
    path("contact/", views.maintenance, name="maintenance"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
