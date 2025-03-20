from django.urls import path

from . import views

urlpatterns = [
    path("", views.home_page_view, name="home"),
    path("config/", views.stripe_config),
    path("create-checkout-session/", views.create_checkout_session),
    path("create-payment-method/", views.create_stripe_user),
    path("create-subscription/", views.create_subscription),
    path("create-intent/", views.create_intent),
    path("save-payment-method/", views.save_payment_method),
    path("add-card/", views.add_card_view),
    path("success/", views.success_view),
    path("cancelled/", views.cancelled_view),
    path("webhook", views.stripe_webhook),
    path("webhook/", views.stripe_webhook),
    path("create-invoice/", views.create_invoice),
]
