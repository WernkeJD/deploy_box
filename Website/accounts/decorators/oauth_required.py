from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse
from django.conf import settings
from requests import post
import time


def oauth_required(view_func):
    """Decorator to ensure that the user is authenticated and has a valid access token."""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if the access token is available and valid
        access_token = get_access_token_from_session(request)

        print(f"Access Token: {access_token}")

        if not access_token:
            return redirect(f"{settings.HOST}/accounts/login/?next={request.path}")

        # If the access token is valid, continue with the view
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def get_access_token_from_session(request):
    """Get the access token, refresh it if expired."""
    access_token = request.session.get("access_token")
    refresh_token = request.session.get("refresh_token")
    expires_at = request.session.get("expires_at")

    if not access_token:
        return None

    # Check if the access token is expired
    if time.time() > expires_at:
        # Token expired, refresh it
        new_tokens = refresh_access_token(refresh_token)
        if new_tokens:
            request.session["access_token"] = new_tokens.get("access_token")
            request.session["refresh_token"] = new_tokens.get("refresh_token")
            request.session["expires_at"] = time.time() + new_tokens.get("expires_in")
            return new_tokens.get("access_token")
        else:
            # Failed to refresh token, force user to log in again
            request.session.flush()  # Clear session
            return None

    return access_token


def refresh_access_token(refresh_token):
    """Refresh the access token using the refresh token."""
    # Exchange the refresh token for a new access token
    response = post(
        f"{settings.HOST}/accounts/o/token/",  # Replace with your token endpoint
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.OAUTH2_FRONTEND_SETTINGS["client_id"],
            "client_secret": settings.OAUTH2_FRONTEND_SETTINGS["client_secret"],
        },
    )
    if response.status_code == 200:
        return response.json()
    return None
