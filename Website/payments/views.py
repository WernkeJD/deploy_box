from django.conf import settings
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView
from django.http import HttpResponse
from api.models import Stacks
from django.contrib.auth.models import User
import json
import time
import stripe
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from accounts.decorators.oauth_required import oauth_required
from django.shortcuts import render
from accounts.models import UserProfile

stripe.api_key = settings.STRIPE_SECRET_KEY


@oauth_required
def home_page_view(request):
    return render(request, "payments-home.html")


@oauth_required
def add_card_view(request):
    return render(request, "payments-add-card.html")


@oauth_required
def success_view(request):
    return render(request, "payments-success.html")


@oauth_required
def cancelled_view(request):
    return render(request, "payments-cancelled.html")


@csrf_exempt
def stripe_config(request):
    if request.method == "GET":
        stripe_config = {"publicKey": settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)


@csrf_exempt
def create_checkout_session(request):
    if request.method == "GET":
        domain_url = "http://localhost:8000/"
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [payment_intent_data] - capture the payment later
            # [customer_email] - prefill the email input in the form
            # For full details see https://stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
            checkout_session = stripe.checkout.Session.create(
                client_reference_id="1",
                success_url=domain_url
                + "payments/success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=domain_url + "payments/cancelled/",
                payment_method_types=["card"],
                mode="payment",
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": "Premium MERN Stack",
                            },
                            "unit_amount": 200,
                        },
                        "quantity": 1,
                    }
                ],
            )
            return JsonResponse({"sessionId": checkout_session["id"]})
        except Exception as e:
            return JsonResponse({"error": str(e)})


def create_stripe_user(user: User):
    try:
        # Create a customer
        customer = stripe.Customer.create(
            name=f"{user.first_name} {user.last_name}",
            email=user.email,
        )

        return customer.id

        return JsonResponse({"customer_id": customer.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def create_subscription(request):
    if request.method == "POST":
        data = json.loads(request.body)
        customer_id = data.get("customer_id")  # The customer ID created earlier
        price_id = "price_1R1GKgC8awKXIVJaWsiksB7O"  # The ID for the metered plan

        print(data)

        try:
            # Create the subscription for the customer
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[
                    {
                        "price": price_id,
                    }
                ],
                expand=["latest_invoice.payment_intent"],
            )

            return JsonResponse(
                {
                    "subscription_id": subscription.id,
                    "client_secret": subscription.latest_invoice.payment_intent.client_secret,
                }
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


def record_usage(subscription_item_id, quantity):
    try:
        stripe.UsageRecord.create(
            subscription_item=subscription_item_id,
            quantity=quantity,  # Number of resources consumed
            timestamp=int(time.time()),  # Current timestamp
            action="increment",  # Add usage incrementally
        )
    except Exception as e:
        print(f"Error recording usage: {e}")


@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        print("Payment was successful.")

        data = json.loads(payload)

        user = data["data"]["object"]["client_reference_id"]
        stack_type = "MEAN"
        variant = "PRO"
        version = "0.0.1"

        print(json.dumps(data, indent=2))
        print(user)

        if not type or not variant or not version:
            return HttpResponse(status=400)

        # Check if the stack already exists
        if Stacks.objects.filter(
            user=user, type=stack_type, variant=variant, version=version
        ).exists():
            return HttpResponse(status=400)

        user_obj = User.objects.get(id=user)
        Stacks.objects.create(
            user=user_obj, type=stack_type, variant=variant, version=version
        )
        return HttpResponse(status=200)

    return HttpResponse(status=200)
