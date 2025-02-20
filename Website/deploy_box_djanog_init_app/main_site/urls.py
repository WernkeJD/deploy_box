from django.contrib import admin
from django.urls import path, include
from .views import home, stacks, pricing,maintenance
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', home, name="home"),
    path('stacks/', stacks, name="stacks"),
    path('pricing/', pricing, name="pricing"),
    path('contact/', maintenance, name="maintenance")
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)