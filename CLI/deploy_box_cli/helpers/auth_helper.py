import http.server
import socketserver
import threading
import urllib.parse
import webbrowser
import requests
import time
import keyring
import pkce
import random
import string
from .decorators import singleton


@singleton
class AuthHelper:
    """Handles OAuth 2.0 PKCE authentication flow, including token storage and retrieval."""

    API_URL = "https://deploy-box.onrender.com"
    # API_URL = "http://127.0.0.1:8000"
    AUTHORIZATION_URL = f"{API_URL}/accounts/o/authorize/"
    TOKEN_URL = f"{API_URL}/accounts/o/token/"
    CLIENT_ID = "QQZwAMHo6G7kJPzI9A4OJxtIkhR5gc8rsEF9Vsgk"
    REDIRECT_URI = "http://127.0.0.1:8080/callback"
    SERVICE_NAME = "oauth-cli"

    def __init__(self):
        # Generate PKCE code verifier and challenge
        self.CODE_VERIFIER = pkce.generate_code_verifier(128)
        self.CODE_CHALLENGE = pkce.get_code_challenge(self.CODE_VERIFIER)

        # Generate state for CSRF protection
        self.state = "".join(random.choices(string.ascii_letters + string.digits, k=10))

        self.access_token = None
        self.refresh_token = None
        self.login_complete = False
        self.httpd = None

        self.load_tokens()

    def start_callback_server(self):
        """Starts a local web server to handle the OAuth callback."""
        handler = lambda *args, **kwargs: OAuthHandler(
            self, *args, **kwargs
        )  # Pass `self` to handler
        with socketserver.TCPServer(("localhost", 8080), handler) as self.httpd:
            self.httpd.RequestHandlerClass.log_message = lambda *args, **kwargs: None
            self.httpd.serve_forever()

    def login(self):
        """Authenticate using OAuth 2.0 PKCE."""
        if self.login_complete:
            print("Already logged in!")
            return

        threading.Thread(target=self.start_callback_server, daemon=True).start()

        print("Opening browser for authentication...")
        auth_url = (
            f"{self.AUTHORIZATION_URL}?response_type=code&client_id={self.CLIENT_ID}"
            f"&redirect_uri={self.REDIRECT_URI}&code_challenge={self.CODE_CHALLENGE}"
            f"&code_challenge_method=S256&state={self.state}"
        )
        webbrowser.open(auth_url)

        while not self.login_complete:
            time.sleep(1)

        print("Login complete!")

    def load_tokens(self):
        """Load tokens from the system keychain."""
        self.access_token = keyring.get_password(self.SERVICE_NAME, "access_token")
        self.refresh_token = keyring.get_password(self.SERVICE_NAME, "refresh_token")
        self.login_complete = self.access_token is not None

    def logout(self):
        """Clear stored tokens."""
        self.access_token = None
        self.refresh_token = None
        self.login_complete = False
        keyring.delete_password(self.SERVICE_NAME, "access_token")
        keyring.delete_password(self.SERVICE_NAME, "refresh_token")
        print("Logged out successfully!")

    def refresh_access_token(self):
        # TODO: Fix this

        """Refresh the access token using the refresh token."""
        if not self.refresh_token:
            print("No refresh token found. Please log in again.")
            return

        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.CLIENT_ID,
        }

        response = requests.post(self.TOKEN_URL, data=token_data)
        tokens = response.json()

        if "access_token" in tokens:
            self.access_token = tokens["access_token"]
            self.save_tokens()
            print("Access token refreshed successfully!")
        else:
            print("\nError refreshing access token:", tokens)

    def request_api(
        self, method, endpoint, json=None, data=None, files=None, stream=False
    ):
        """Make an authenticated request to the API."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.request(
            method,
            f"{self.API_URL}/api/{endpoint}",
            headers=headers,
            json=json,
            data=data,
            files=files,
            stream=stream,
        )

        if response.status_code == 401:
            print("Access token expired. Refreshing token...")
            self.refresh_access_token()
            headers["Authorization"] = f"Bearer {self.access_token}"
            response = requests.request(
                method,
                f"{self.API_URL}/api/{endpoint}",
                headers=headers,
                json=json,
                data=data,
                files=files,
                stream=stream,
            )

        return response

    def save_tokens(self):
        """Securely store tokens in the system keychain."""
        keyring.set_password(self.SERVICE_NAME, "access_token", self.access_token)
        keyring.set_password(self.SERVICE_NAME, "refresh_token", self.refresh_token)


class OAuthHandler(http.server.SimpleHTTPRequestHandler):
    """Handles OAuth 2.0 callback."""

    def __init__(self, auth_helper: AuthHelper, *args, **kwargs):
        self.auth_helper = auth_helper
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handles the redirect from the OAuth provider."""
        parsed_path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_path.query)

        if "code" in params:
            auth_code = params["code"][0]

            token_data = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": self.auth_helper.REDIRECT_URI,
                "client_id": self.auth_helper.CLIENT_ID,
                "code_verifier": self.auth_helper.CODE_VERIFIER,
            }

            response = requests.post(self.auth_helper.TOKEN_URL, data=token_data)
            tokens = response.json()

            if "access_token" in tokens:
                self.auth_helper.access_token = tokens["access_token"]
                self.auth_helper.refresh_token = tokens.get("refresh_token")
                self.auth_helper.save_tokens()
                self.auth_helper.login_complete = True
            else:
                print("\nError getting access token:", tokens)

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Authentication Successful!</h1><p>You can close this tab.</p></body></html>"
            )

            threading.Thread(target=self.auth_helper.httpd.shutdown).start()

        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Error: No code received</h1></body></html>"
            )
