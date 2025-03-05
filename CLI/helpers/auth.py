import cmd
import requests
import webbrowser
import pkce
import random
import string
import time
import keyring
import http.server
import socketserver
import threading
import urllib.parse

# OAuth server details
API_URL = "http://127.0.0.1:8000"
AUTHORIZATION_URL = f"{API_URL}/o/authorize/"
TOKEN_URL = f"{API_URL}/o/token/"
CLIENT_ID = "G6d1r65SOzEUKp9iKZYQnwgvTOMHj90NGVrJmZ8X"
REDIRECT_URI = "http://localhost:8080/callback"
SERVICE_NAME = "oauth-cli"

# Generate PKCE Code Verifier and Challenge
CODE_VERIFIER = pkce.generate_code_verifier(128)
CODE_CHALLENGE = pkce.get_code_challenge(CODE_VERIFIER)

# Store state for CSRF protection
state = "".join(random.choices(string.ascii_letters + string.digits, k=10))

access_token = None
refresh_token = None
login_complete = False

class OAuthHandler(http.server.SimpleHTTPRequestHandler):
    """Handles OAuth 2.0 callback."""
    
    def do_GET(self):
        global access_token, refresh_token, login_complete

        # Parse the URL to get the authorization code
        parsed_path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_path.query)

        if "code" in params:
            auth_code = params["code"][0]

            # Exchange code for access token
            token_data = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": REDIRECT_URI,
                "client_id": CLIENT_ID,
                "code_verifier": CODE_VERIFIER,
            }

            response = requests.post(TOKEN_URL, data=token_data)
            tokens = response.json()

            if "access_token" in tokens:
                access_token = tokens["access_token"]
                refresh_token = tokens.get("refresh_token")
                self.__save_tokens(access_token, refresh_token)
                login_complete = True
            else:
                print("\nError getting access token:", tokens)

            # Send response to browser
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authentication Successful!</h1><p>You can close this tab.</p></body></html>")

            # Stop the server after handling one request
            threading.Thread(target=httpd.shutdown).start()

        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Error: No code received</h1></body></html>")

    def __save_tokens(self, access_token, refresh_token):
        """Securely store tokens in the system keychain."""
        keyring.set_password(SERVICE_NAME, "access_token", access_token)
        keyring.set_password(SERVICE_NAME, "refresh_token", refresh_token)
        

def start_callback_server():
    """Starts a local web server to handle the OAuth callback."""
    global httpd
    with socketserver.TCPServer(("localhost", 8080), OAuthHandler) as httpd:
        # Suppress server logs
        httpd.RequestHandlerClass.log_message = lambda *args, **kwargs: None
        httpd.serve_forever()

def login():
    """Authenticate using OAuth 2.0 PKCE."""
    global login_complete
    if login_complete:
        print("Already logged in!")
        return
    
    threading.Thread(target=start_callback_server, daemon=True).start()

    print("Opening browser for authentication...")

    auth_url = (
        f"{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&code_challenge={CODE_CHALLENGE}"
        f"&code_challenge_method=S256&state={state}"
    )
    webbrowser.open(auth_url)

    # Block CLI until login is complete
    while not login_complete:
        time.sleep(1)  # Wait until login is complete

    print("Login complete!")

def load_tokens():
    """Load tokens from the system keychain."""
    global access_token, refresh_token, login_complete
    access_token = keyring.get_password(SERVICE_NAME, "access_token")
    refresh_token = keyring.get_password(SERVICE_NAME, "refresh_token")
    login_complete = access_token is not None
    

def logout():
    """Clear stored tokens."""
    global access_token, refresh_token, login_complete
    access_token = None
    refresh_token = None
    login_complete = False
    keyring.delete_password(SERVICE_NAME, "access_token")
    keyring.delete_password(SERVICE_NAME, "refresh_token")
    print("Logged out successfully!")
