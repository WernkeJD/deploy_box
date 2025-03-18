from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("main_site.urls", "main_site"), "main_site")),
    path("accounts/", include(("accounts.urls", "accounts"), "accounts")),
    path("api/", include(("api.urls", "api"), "api")),
    path("payments/", include(("payments.urls", "payments"), "payments")),
    path("github/", include(("github.urls", "github"), "github")),
    path("__reload__/", include("django_browser_reload.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
