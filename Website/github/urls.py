from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("auth", views.github_login, name="github_login"),
    path("auth/callback", views.github_callback, name="github_callback"),
    path("logout", views.logout, name="logout"),
    path("repos", views.list_repos, name="list_repos"),
    path("webhooks/create", views.create_github_webhook, name="create_webhook"),
    path("webhooks/<int:webhook_id>", views.github_webhook, name="webhook"),
]
