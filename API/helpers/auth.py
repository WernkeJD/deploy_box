from flask import Flask, jsonify, request
from functools import wraps
import requests

DJANGO_API_URL = "http://127.0.0.1:8000/api/validate-token/"

def require_authentication(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if token is None:
            return jsonify({"error": "Missing token"}), 401
        
        # Check if token starts with 'Bearer ' and extract the token part
        if not token.startswith('Bearer '):
            return jsonify({"error": "Invalid token format"}), 401
        
        
        # Make a request to the Django API to validate the token
        response = requests.get(DJANGO_API_URL, headers={'Authorization': token})
        
        # If the response is not 200 (OK), deny access
        if response.status_code != 200:
            return jsonify({"error": "Unauthorized"}), 403
        
        return f(*args, **kwargs)
    return decorated_function