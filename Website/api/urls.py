from django.urls import path
from . import views

urlpatterns = [
    path("", views.testing, name="testing"),
    path("stacks", views.stack_operations, name="add_stacks"),
    path("stacks/<int:stack_id>", views.stack_operations, name="get_update_stack"),
    path(
        "stacks/<int:stack_id>/download", views.stack_operations, name="download_stack"
    ),
    path("deployments/", views.deployment_operations, name="add_deployments"),
    path(
        "deployments/<int:deployment_id>",
        views.deployment_operations,
        name="get_update_deployment",
    ),
    path(
        "deployments/<int:deployment_id>/key",
        views.deployment_operations,
        name="get_deployment_google_cli_key",
    ),
    path(
        "get_deployment_details/<int:deployment_id>",
        views.get_deployment_details,
        name="get_deployment_details",
    ),
]
