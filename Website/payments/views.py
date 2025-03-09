from django.conf import settings
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView
from django.http import HttpResponse
from main_site.models import Stacks, User
import json

import stripe

class HomePageView(TemplateView):
    template_name = 'payments-home.html'

class SuccessView(TemplateView):
    template_name = 'payments-success.html'

class CancelledView(TemplateView):
    template_name = 'payments-cancelled.html'

@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)
    
@csrf_exempt
def create_checkout_session(request):
    if request.method == 'GET':
        domain_url = 'http://localhost:8000/'
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
                success_url=domain_url + 'payments/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'payments/cancelled/',
                payment_method_types=['card'],
                mode='payment',
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': 'Basic MERN Stack',
                            },
                            'unit_amount': 200,
                        },
                        'quantity': 1,
                    }
                ]
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})
        
@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        print("Payment was successful.")

        data = json.loads(payload)

        user = data['data']['object']['client_reference_id']
        stack_type = "MEAN"
        variant = "PRO"
        version = "0.0.1"

        print(json.dumps(data, indent=2))
        print(user)

        if not type or not variant or not version:
            return HttpResponse(status=400)

        # Check if the stack already exists
        if Stacks.objects.filter(user=user, type=stack_type, variant=variant, version=version).exists():
            return HttpResponse(status=400)
        

        user_obj = User.objects.get(id=user)
        Stacks.objects.create(user=user_obj, type=stack_type, variant=variant, version=version)
        return HttpResponse(status=200)

    return HttpResponse(status=200)