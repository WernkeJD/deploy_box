from django.urls import path
from . import views

urlpatterns = [
    path("", views.testing, name="testing"),
    path("stacks", views.stack_operations, name="add_stacks"),
    path("stacks/<int:stack_id>/deploy", views.stack_operations, name="deploy_stacks"),
    path("stacks/<int:stack_id>", views.stack_operations, name="get_update_stack"),
    path(
        "stacks/<int:stack_id>/download", views.stack_operations, name="download_stack"
    ),
]
