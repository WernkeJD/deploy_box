from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from .models import UserProfile
from django.conf import settings
from django.http import JsonResponse
from requests import post
import os
import base64
import hashlib
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
import time
from .decorators.oauth_required import oauth_required
from payments.views import create_stripe_user


@oauth_required
def protected_view(request):
    return HttpResponse(f"Welcome {request.user.username}!")


def generate_pkce_pair():
    """Generates a PKCE code_verifier and code_challenge."""
    code_verifier = (
        base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode("utf-8")
    )

    sha256_hash = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(sha256_hash).rstrip(b"=").decode("utf-8")

    return code_verifier, code_challenge


# Authentication
def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            birthdate = form.cleaned_data["birthdate"]

            # Create a stripe customer
            stripe_customer_id = create_stripe_user(user)

            UserProfile.objects.create(
                user=user, birthdate=birthdate, stripe_customer_id=stripe_customer_id
            )

            return redirect("/accounts/login")
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts-signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Generate a PKCE pair
            code_verifier, code_challenge = generate_pkce_pair()

            # Store the code verifier in the session
            request.session["code_verifier"] = code_verifier

            # Redirect to the OAuth2 authorization page after login
            client_id = settings.OAUTH2_FRONTEND_SETTINGS["client_id"]
            redirect_uri = settings.OAUTH2_FRONTEND_SETTINGS["redirect_uri"]

            oauth_url = (
                reverse("accounts:oauth2_provider:authorize")
                + f"?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&code_challenge={code_challenge}&code_challenge_method=S256"
            )

            return redirect(oauth_url)
        else:
            # Handle failed login (return an error, show a message, etc.)
            return HttpResponse("Invalid credentials", status=401)

    return render(request, "accounts-login.html")


import logging

logger = logging.getLogger(__name__)


@login_required
def oauth2_callback(request):
    code = request.GET.get("code")
    code_verifier = request.session.get("code_verifier")

    if not code or not code_verifier:
        logger.error("Missing code or code_verifier.")
        return redirect("accounts:login")  # Redirect to login if anything is missing

    # Prepare data for token exchange
    token_url = (
        f"{settings.HOST}/accounts/o/token/"  # Ensure this is the correct token URL
    )
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.OAUTH2_FRONTEND_SETTINGS["redirect_uri"],
        "client_id": settings.OAUTH2_FRONTEND_SETTINGS["client_id"],
        "code_verifier": code_verifier,
    }

    try:
        # Exchange the authorization code for an access token
        response = post(token_url, data=data)

        if response.status_code != 200:
            logger.error(f"Error exchanging code for token: {response.text}")
            return JsonResponse(
                {"error": "Failed to exchange code for token"}, status=400
            )

        # Get the access token from the response
        response_data = response.json()
        access_token = response_data.get("access_token")

        if access_token:
            # Store the access token securely in the session
            request.session["access_token"] = access_token
            request.session["expires_at"] = (
                response_data.get("expires_in") + time.time()
            )

            # Optionally, you can store the refresh_token for refreshing the access token later
            refresh_token = response_data.get("refresh_token")
            if refresh_token:
                request.session["refresh_token"] = refresh_token

            return redirect("/")  # Redirect to the home page after successful login
        else:
            logger.error("No access token returned in the response.")
            return JsonResponse({"error": "No access token returned"}, status=400)

    except Exception as e:
        logger.error(f"Error occurred during token exchange: {str(e)}")
        return JsonResponse({"error": "Error during token exchange"}, status=500)
