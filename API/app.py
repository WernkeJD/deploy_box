import os
import requests
import subprocess
from flask import Flask, redirect, request, session, url_for

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Use a secure secret key

# GitHub OAuth credentials
CLIENT_ID = "Ov23lilI02RZEMGj4xAX"
CLIENT_SECRET = "143eeca2aed576e63ca87ff9435bcfbb2be0790c"
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


@app.route("/")
def home():
    return "Welcome to Deploy Box! <a href='/auth/github'>Login with GitHub</a>"


@app.route("/auth/github")
def github_login():
    """Redirects users to GitHub OAuth page."""
    return redirect(f"{GITHUB_AUTH_URL}?client_id={CLIENT_ID}&scope=repo")


@app.route("/auth/github/callback")
def github_callback():
    """Handles GitHub OAuth callback and fetches user info."""
    code = request.args.get("code")
    if not code:
        return "Authorization failed", 400

    # Exchange code for access token
    token_response = requests.post(
        GITHUB_TOKEN_URL,
        headers={"Accept": "application/json"},
        data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "code": code},
    )
    token_json = token_response.json()
    access_token = token_json.get("access_token")

    if not access_token:
        return "Failed to retrieve access token", 400

    # Fetch user info from GitHub API
    user_response = requests.get(
        GITHUB_USER_URL, headers={"Authorization": f"token {access_token}"}
    )
    user_data = user_response.json()

    # Store token securely (session for now)
    session["github_token"] = access_token
    session["github_user"] = user_data

    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    """Displays user info after successful login."""
    if "github_user" not in session:
        return redirect(url_for("home"))

    user = session["github_user"]
    return f"Welcome, {user['login']}! <a href='/logout'>Logout</a>"


@app.route("/logout")
def logout():
    """Clears session data."""
    session.clear()
    return redirect(url_for("home"))


GITHUB_REPOS_URL = "https://api.github.com/user/repos"


@app.route("/repos")
def list_repos():
    """Fetch and display user repositories with a deploy button."""
    if "github_token" not in session:
        return redirect(url_for("home"))

    access_token = session["github_token"]

    repo_response = requests.get(
        GITHUB_REPOS_URL,
        headers={"Authorization": f"token {access_token}"},
        params={"per_page": 100},
    )

    if repo_response.status_code != 200:
        return "Failed to fetch repositories", 400

    repos = repo_response.json()

    # Display repositories with deploy buttons
    repo_list = "<h2>Your GitHub Repositories:</h2><ul>"
    for repo in repos:
        repo_list += f"""
            <li>
                <a href="{repo["html_url"]}">{repo["name"]}</a>
                <form action="/clone_repo" method="post" style="display:inline;">
                    <input type="hidden" name="repo_url" value="{repo["clone_url"]}">
                    <input type="hidden" name="repo_name" value="{repo["name"]}">
                    <button type="submit">Deploy</button>
                </form>
            </li>
        """
    repo_list += "</ul>"

    return repo_list


def clone_repo(repo_url, repo_name):
    """Clones the given GitHub repository to the server."""
    repo_path = os.path.join("deployed_repos", repo_name)

    if os.path.exists(repo_path):
        return f"Repository {repo_name} already exists."

    os.makedirs("deployed_repos", exist_ok=True)

    # Get GitHub token from session (you should store this securely)
    access_token = session.get("github_token")

    if not access_token:
        return "Missing GitHub access token. Please authenticate again.", 401

    # Convert repo URL to use token authentication
    repo_url_with_auth = repo_url.replace(
        "https://github.com", f"https://{access_token}:x-oauth-basic@github.com"
    )

    try:
        subprocess.run(["git", "clone", repo_url_with_auth, repo_path], check=True)
        return f"Repository {repo_name} cloned successfully!"
    except subprocess.CalledProcessError as e:
        return f"Failed to clone repository: {str(e)}"


@app.route("/clone_repo", methods=["POST"])
def clone_user_repo():
    """Clones a user-selected repo."""
    if "github_token" not in session:
        return redirect(url_for("home"))

    repo_url = request.form.get("repo_url")
    repo_name = request.form.get("repo_name")

    if not repo_url or not repo_name:
        return "Invalid request", 400

    result = clone_repo(repo_url, repo_name)
    return result


if __name__ == "__main__":
    app.run(debug=True)
