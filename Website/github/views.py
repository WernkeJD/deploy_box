import os
import requests
import subprocess
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from django.urls import reverse
from django.contrib.sessions.models import Session
import hmac
import hashlib
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Webhooks, Tokens
import secrets
from api.models import Stacks

GITHUB_SECRET = "your_webhook_secret"
# GitHub OAuth credentials
CLIENT_ID = settings.GITHUB_CLIENT_ID
CLIENT_SECRET = settings.GITHUB_CLIENT_SECRET
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_REPOS_URL = "https://api.github.com/user/repos"


def home(request):
    return HttpResponse(
        "Welcome to Deploy Box! <a href='/github/auth'>Login with GitHub</a>"
    )


def github_login(request):
    """Redirects users to GitHub OAuth page."""
    return redirect(f"{GITHUB_AUTH_URL}?client_id={CLIENT_ID}&scope=repo")


def github_callback(request):
    """Handles GitHub OAuth callback and fetches user info."""
    code = request.GET.get("code")
    if not code:
        return HttpResponse("Authorization failed", status=400)

    # Exchange code for access token
    token_response = requests.post(
        GITHUB_TOKEN_URL,
        headers={"Accept": "application/json"},
        data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "code": code},
    )
    token_json = token_response.json()
    access_token = token_json.get("access_token")

    if not access_token:
        return HttpResponse("Failed to retrieve access token", status=400)

    # Fetch user info from GitHub API
    user_response = requests.get(
        GITHUB_USER_URL, headers={"Authorization": f"token {access_token}"}
    )
    user_data = user_response.json()

    if "id" not in user_data:
        return HttpResponse("Failed to retrieve user info", status=400)

    # Store token securely in database
    github_token, created = Tokens.objects.get_or_create(user=request.user)
    github_token.set_token(access_token)
    github_token.save()

    # Store user info in session
    request.session["github_user"] = user_data
    request.session.modified = True

    return redirect(reverse("github:list_repos"))


def dashboard(request):
    """Displays user info after successful login."""
    if "github_user" not in request.session:
        return redirect(reverse("github:home"))

    user = request.session["github_user"]
    return HttpResponse(f"Welcome, {user['login']}! <a href='/logout'>Logout</a>")


def logout(request):
    """Clears session data."""
    request.session.clear()
    return redirect(reverse("github:home"))


def list_repos(request):
    """Fetch and display user repositories with a deploy button."""
    user = request.user

    # Retrieve GitHub token securely
    try:
        github_token = Tokens.objects.get(user=user).get_token()
    except Tokens.DoesNotExist:
        return JsonResponse({"error": "GitHub token not found"}, status=403)

    repo_response = requests.get(
        GITHUB_REPOS_URL,
        headers={"Authorization": f"token {github_token}"},
        params={"per_page": 100},
    )

    if repo_response.status_code != 200:
        return HttpResponse("Failed to fetch repositories", status=400)

    repos = repo_response.json()

    # Display repositories with deploy buttons
    repo_list = "<h2>Your GitHub Repositories:</h2><ul>"
    for repo in repos:
        repo_list += f"""
            <li>
                <a href="{repo['html_url']}">{repo['name']}</a>
                <form action="{settings.HOST}/github/webhooks/create" method="post" style="display:inline;">
                    <input type="hidden" name="stack-id" value="{ 8 }">
                    <input type="hidden" name="repo-url" value="{repo['clone_url']}">
                    <input type="hidden" name="repo-name" value="{repo['name']}">
                    <button type="submit">Deploy</button>
                </form>
            </li>
        """
    repo_list += "</ul>"

    return HttpResponse(repo_list)


import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Webhooks

GITHUB_API_BASE = "https://api.github.com"


@csrf_exempt
def create_github_webhook(request):
    """Create and store a GitHub webhook for a user's repository."""
    user = request.user
    repo_name = request.POST.get("repo-name")

    if not repo_name:
        return JsonResponse({"error": "Repository name is required"}, status=400)

    stack_id = request.POST.get("stack-id")

    if not stack_id:
        return JsonResponse({"error": "Stack ID is required"}, status=400)

    # Check if the stack exists
    stack = Stacks.objects.filter(id=stack_id).first()
    if not stack:
        return JsonResponse({"error": "Stack not found"}, status=404)

    # Retrieve GitHub token securely
    try:
        print(user)
        github_token = Tokens.objects.get(user=user).get_token()
    except Tokens.DoesNotExist:
        return JsonResponse({"error": "GitHub token not found"}, status=403)

    # Generate a secure secret for webhook
    # webhook_secret = secrets.token_hex(32)

    # Webhook URL pointing to your backend
    webhook_url = f"{settings.HOST}/github/webhooks/{user.id}"

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    payload = {
        "name": "web",
        "active": True,
        "events": ["push"],  # Add more events if needed
        "config": {
            "url": webhook_url,
            "content_type": "json",
            "secret": GITHUB_SECRET,
        },
    }

    print(f"{GITHUB_API_BASE}/repos/{user.username}/{repo_name}/hooks")
    print(payload)
    print(headers)

    # Check if webhook already exists in the database
    if Webhooks.objects.filter(
        user=user, repository=f"{user.username}/{repo_name}"
    ).exists():
        return JsonResponse({"error": "Webhook already exists"}, status=400)

    # Check if webhook already exists on GitHub
    response = requests.get(
        f"{GITHUB_API_BASE}/repos/{user.username}/{repo_name}/hooks",
        headers=headers,
    )

    for hook in response.json():
        if hook["config"]["url"] == webhook_url:
            webhook = Webhooks.objects.create(
                user=user,
                stack=stack,
                repository=f"{user.username}/{repo_name}",
                webhook_id=hook["id"],
                url=hook["config"]["url"],
                secret=GITHUB_SECRET,  # Store secret securely
            )
            return JsonResponse(
                {"message": "Webhook created", "webhook_id": webhook.webhook_id},
                status=201,
            )

    # Create webhook on GitHub
    response = requests.post(
        f"{GITHUB_API_BASE}/repos/{user.username}/{repo_name}/hooks",
        json=payload,
        headers=headers,
    )

    if response.status_code == 201:
        data = response.json()
        # Store webhook details in database
        webhook = Webhooks.objects.create(
            user=user,
            stack=stack,
            repository=f"{user.username}/{repo_name}",
            webhook_id=data["id"],
            url=data["config"]["url"],
            secret=GITHUB_SECRET,  # Store secret securely
        )
        return JsonResponse(
            {"message": "Webhook created", "webhook_id": webhook.webhook_id}, status=201
        )
    else:
        return JsonResponse({"error": response.json()}, status=response.status_code)


def delete_github_webhook(request):
    """Delete a GitHub webhook for a user's repository"""
    user = request.user
    repo = request.POST.get("repository")

    try:
        webhook = Webhooks.objects.get(user=user, repository=repo)
    except Webhooks.DoesNotExist:
        return JsonResponse({"error": "Webhook not found"}, status=404)

    headers = {
        "Authorization": f"token {user.github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    response = requests.delete(
        f"{GITHUB_API_BASE}/repos/{repo}/hooks/{webhook.webhook_id}", headers=headers
    )

    if response.status_code == 204:
        webhook.delete()
        return JsonResponse({"message": "Webhook deleted"}, status=200)
    else:
        return JsonResponse({"error": response.json()}, status=response.status_code)


def list_github_webhooks(request):
    """List all GitHub webhooks for the authenticated user"""
    webhooks = Webhooks.objects.filter(user=request.user)
    data = [
        {"repository": wh.repository, "webhook_id": wh.webhook_id} for wh in webhooks
    ]
    return JsonResponse({"webhooks": data}, status=200)


import hmac
import hashlib
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import WebhookEvents, Webhooks
from django.contrib.auth.models import User

ALLOWED_EVENTS = {"push", "pull_request", "issues"}  # Specify allowed event types

from google.cloud.devtools import cloudbuild_v1
from google.oauth2 import service_account


def sample_submit_and_approve_build(stack_id, github_repo, github_token, layer:str):
    try:
        # Create a client with credentials
        credentials = service_account.Credentials.from_service_account_file(settings.GCP_KEY_PATH)
        client = cloudbuild_v1.CloudBuildClient(credentials=credentials)

        # Replace with your project ID
        project_id = "deploy-box"
        github_url = (
            f"https://{github_token}:x-oauth-basic@github.com/{github_repo}.git"
        )
        github_repo_name = github_repo.split("/")[-1]
        print(github_url)
        print(github_repo_name)

        layer = layer.lower()
        image_name = f"us-central1-docker.pkg.dev/deploy-box/deploy-box-repository/{layer}-{stack_id}".lower()

        # Define the Cloud Build steps similar to the YAML configuration
        build_steps = [
            cloudbuild_v1.BuildStep(
                name="gcr.io/cloud-builders/git", args=["clone", github_url]
            ),
            cloudbuild_v1.BuildStep(
                name="gcr.io/cloud-builders/docker",
                entrypoint="bash",
                args=[
                    "-c",
                    f"docker build -t {image_name} ./{github_repo_name}/{layer}",
                ],
            ),
            cloudbuild_v1.BuildStep(
                name="gcr.io/cloud-builders/docker",
                args=[
                    "push",
                    image_name,
                ],
            ),
            cloudbuild_v1.BuildStep(
                name="gcr.io/google.com/cloudsdktool/cloud-sdk",
                entrypoint="bash",
                args=[
                    "-c",
                    f"""
                    gcloud run deploy {layer}-{stack_id} \
                        --image={image_name} \
                        --region=us-central1 \
                        --platform=managed \
                        --allow-unauthenticated
                """,
                ],
            ),
            cloudbuild_v1.BuildStep(
                name="gcr.io/google.com/cloudsdktool/cloud-sdk",
                entrypoint="bash",
                args=[
                    "-c",
                    f"""
                    service_full_name="projects/deploy-box/locations/us-central1/services/{layer}-{stack_id}"
                    gcloud run services add-iam-policy-binding {layer}-{stack_id} \
                        --region=us-central1 \
                        --member="allUsers" \
                        --role="roles/run.invoker"
                """,
                ],
            ),
        ]

        # Define the build configuration (timeout, source location, and steps)
        build = cloudbuild_v1.Build(steps=build_steps, timeout="600s")

        # Create the build request
        build_request = cloudbuild_v1.CreateBuildRequest(
            project_id=project_id, build=build
        )

        # Submit the build
        print("Submitting build...")
        operation = client.create_build(build_request)

        # Wait for the build to finish and catch any errors
        print("Waiting for build to complete...")
        response = operation.result()
        print(f"Build submitted: {response.status}")
        print(f"Build ID: {response.id}")
        print(f"Build name: {response.name}")

        if response.status != cloudbuild_v1.Build.Status.SUCCESS:
            print("Build failed. Checking logs...")
            # Optionally, fetch more logs or information on why the build failed
            print(
                f"Build log URL: https://console.cloud.google.com/cloud-build/builds/{response.id}?project={project_id}"
            )

    except Exception as e:
        print(f"An error occurred: {e}")


@csrf_exempt
def github_webhook(request, webhook_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    # Validate GitHub signature
    signature = request.headers.get("X-Hub-Signature-256")
    body = request.body

    computed_signature = (
        "sha256=" + hmac.new(GITHUB_SECRET.encode(), body, hashlib.sha256).hexdigest()
    )
    if not hmac.compare_digest(signature, computed_signature):
        return JsonResponse({"error": "Invalid signature"}, status=403)

    # Parse webhook payload
    payload = json.loads(body)
    event_type = request.headers.get("X-GitHub-Event")
    webhook_id = request.headers.get("X-GitHub-Hook-ID")
    repository = payload.get("repository", {}).get("full_name", "unknown/repo")

    # Ignore events that aren't in the allowed list
    if event_type not in ALLOWED_EVENTS:
        return JsonResponse(
            {"message": f"Ignored event type: {event_type}"}, status=200
        )

    # Find user based on webhook repository
    webhook = Webhooks.objects.filter(webhook_id=webhook_id).first()
    print("repository", repository)
    print("webhook", webhook)
    user = webhook.user if webhook else None

    # Store event in the database
    # webhook_event = WebhookEvents.objects.create(
    #     user=user, stack=webhook.stack, event_type=event_type, payload=payload
    # )

    github_token = Tokens.objects.get(user=user).get_token()

    # TODO: Handle different repository types
    if repository == "WernkeJD/deploy_box":
        # Handle the specific repository
        print("Handling WernkeJD/deploy_box repository")

        threading.Thread(
            target=sample_submit_and_approve_build,
            args=(webhook.stack.id, webhook.repository, github_token, "Website"),
        ).start()

    else:

        threading.Thread(
            target=sample_submit_and_approve_build,
            args=(webhook.stack.id, webhook.repository, github_token, "backend"),
        ).start()

        threading.Thread(
            target=sample_submit_and_approve_build,
            args=(webhook.stack.id, webhook.repository, github_token, "frontend"),
        ).start()



    return JsonResponse({"status": "success", "event_type": event_type}, status=200)


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import WebhookEvents
import threading


@login_required
def list_github_webhook_events(request):
    """Retrieve all webhook events for the authenticated user"""
    events = WebhookEvents.objects.filter(user=request.user).order_by("-received_at")
    data = [
        {
            "event_type": event.event_type,
            "repository": event.repository,
            "received_at": event.received_at.isoformat(),
            "payload": event.payload,
        }
        for event in events
    ]
    return JsonResponse({"events": data}, status=200)
