from flask import Flask
from routes import api
import os

app = Flask(__name__)
app.register_blueprint(api)

def setup():
    # Authenticate with GCP
    os.system("gcloud auth configure-docker us-central1-docker.pkg.dev")


if __name__ == '__main__':
    setup()
    app.run(debug=True, host='0.0.0.0', port=5000)
