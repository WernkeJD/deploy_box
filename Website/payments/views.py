from django.conf import settings
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from api.models import Stacks
from django.contrib.auth.models import User
from accounts.models import UserProfile
from api.models import AvailableStacks
import json
import time
import stripe
from accounts.decorators.oauth_required import oauth_required
from django.shortcuts import render

stripe.api_key = settings.STRIPE_SECRET_KEY


@oauth_required
def home_page_view(request):
    return render(request, "payments-home.html")


@oauth_required
def add_card_view(request):
    return render(
        request,
        "payments-add-card.html",
        {"stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY},
    )


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

def create_stripe_user(user: User):
    # Create a new customer in Stripe
    try:
        customer = stripe.Customer.create(
            name=f"{user.first_name} {user.last_name}",
            email=user.email,
        )

        return customer.id

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@oauth_required
def create_intent(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)

        intent = stripe.SetupIntent.create(
            customer=user_profile.stripe_customer_id,
        )
        print(intent.client_secret)
        return JsonResponse({"client_secret": intent.client_secret})
    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@oauth_required
def save_payment_method(request):
    try:
        payment_method_id = request.POST.get("payment_method")

        user_profile = UserProfile.objects.get(user=request.user)
        customer_id = user_profile.stripe_customer_id

        # Attach the payment method to the customer
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_id,  # Use the current logged-in user's Stripe customer ID
        )

        # Optionally, you can set this payment method as the default for subscriptions
        stripe.customers.update(
            customer_id,  # Use the current logged-in user's Stripe customer ID
            invoice_settings={"default_payment_method": payment_method_id},
        )

        return JsonResponse({"status": "Payment method saved successfully"})

    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def create_checkout_session(request):
    if request.method == "GET":
        domain_url = settings.HOST
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            checkout_session = stripe.checkout.Session.create(
                customer=UserProfile.objects.get(user_id= request.user.id).stripe_customer_id,
                metadata={
                    "user_id": request.user.id,
                    "stack_id": "2",
                },
                success_url=domain_url
                + "/payments/success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=domain_url + "/payments/cancelled",
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
                payment_intent_data={
                    "setup_future_usage": "off_session",  # This tells Stripe to save the card for future payments
                },
            )
            return JsonResponse({"sessionId": checkout_session["id"]})
        except Exception as e:
            return JsonResponse({"error": str(e)})


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
    # Use `stripe listen --forward-to http://127.0.0.1:8000/payments/webhook` to listen for events
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

        metadata = data["data"]["object"]["metadata"]
        user_id = metadata.get("user_id")
        stack_id = metadata.get("stack_id")

        # Check if the stack already exists
        if Stacks.objects.filter(user=user_id, stack=stack_id).exists():
            return HttpResponse(status=400)

        user = User.objects.get(id=user_id)
        avaiable_stack = AvailableStacks.objects.get(id=stack_id)

        Stacks.objects.create(user=user, stack=avaiable_stack)
        return HttpResponse(status=200)

    return HttpResponse(status=200)


#new branch work################################################################################################

@csrf_exempt
def create_invoice(request):
    if request.method == "POST":
        try:
            # Get data from the request body (e.g., customer_id, amount, description)
            data = json.loads(request.body)
            customer_id = data['customer_id']  # Existing Stripe customer ID
            amount = data['amount']  # Amount to charge in cents (e.g., 5000 for $50.00)
            description = data['description']  # Description of the charge

            # Step 1: Create an invoice item
            stripe.InvoiceItem.create(
                customer=customer_id,
                amount=amount,
                currency="usd",  # You can change the currency if needed
                description=description
            )

            # Step 2: Create the invoice for the customer
            invoice = stripe.Invoice.create(
                customer=customer_id,
                auto_advance=True  # Automatically finalizes and sends the invoice
            )

            # Step 3: Finalize the invoice (send to customer)
            invoice.finalize_invoice()

            return JsonResponse({
                'invoice_id': invoice.id,
                'status': invoice.status
            })

        except stripe.error.StripeError as e:
            return JsonResponse({'error': str(e)}, status=400)

        except Exception as e:
            return JsonResponse({'error': 'An error occurred while creating the invoice.'}, status=400)
