import dotenv
import os
import requests
import time
import uuid
import hashlib
from pymongo import MongoClient

dotenv.load_dotenv()

MONGODB_TOKEN = os.environ.get("MONGODB_TOKEN")
MONGODB_ORG_ID = os.environ.get("MONGODB_ORG_ID")
MONGODB_PROJECT_ID = os.environ.get("MONGODB_PROJECT_ID")
MONGODB_CLIENT_ID = os.environ.get("MONGODB_CLIENT_ID")
MONGODB_CLIENT_SECRET = os.environ.get("MONGODB_CLIENT_SECRET")
MONGODB_CONNECTION_STRING = os.environ.get("MONGODB_CONNECTION_STRING")

client = MongoClient(MONGODB_CONNECTION_STRING)


def get_mongodb_token():
    global MONGODB_TOKEN

    if MONGODB_TOKEN:
        return MONGODB_TOKEN

    url = "https://cloud.mongodb.com/api/oauth/token"
    payload = {"grant_type": "client_credentials"}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    auth = (MONGODB_CLIENT_ID, MONGODB_CLIENT_SECRET)
    response = requests.post(url, data=payload, headers=headers, auth=auth)
    response.raise_for_status()
    MONGODB_TOKEN = response.json().get("access_token")
    print(f"MONGODB_TOKEN={MONGODB_TOKEN}")
    return MONGODB_TOKEN


def request_helper(url, method="GET", data=None):
    global MONGODB_TOKEN

    url = f"https://cloud.mongodb.com/api/atlas/v2{url}"

    while True:
        headers = {
            "Authorization": f"Bearer {MONGODB_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.atlas.2023-01-01+json",
        }

        response = None
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data)

        if response.status_code == 401:
            MONGODB_TOKEN = None
            get_mongodb_token()
            continue

        elif response.ok:
            return response.json()

        return response


def deploy_mongodb(deployment_id: str):
    database_name = f"db-{deployment_id}"
    username = f"deployBoxUser-{deployment_id}"
    password = hashlib.sha256(str(time.time()).encode()).hexdigest()[:12]

    db = client[database_name]

    # Get the database stats
    stats = db.command("dbstats")

    # Print the stats
    print(stats.get("storageSize"))

    # Check if user already exists
    response = request_helper(
        f"/groups/{MONGODB_PROJECT_ID}/databaseUsers/admin/{username}", "GET"
    )

    if isinstance(response, requests.models.Response):
        if response.status_code != 404:
            raise response

        # Create a new database user
        user_data = {
            "groupId": MONGODB_PROJECT_ID,
            "databaseName": "admin",
            "username": username,
            "password": password,
            "roles": [{"databaseName": database_name, "roleName": "readWrite"}],
            "scopes": [{"name": "cluster0", "type": "CLUSTER"}],
        }

        response = request_helper(
            f"/groups/{MONGODB_PROJECT_ID}/databaseUsers", "POST", user_data
        )

        print(response)

    connection_string = f"mongodb+srv://{username}:{password}@cluster0.yjaoi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

    return connection_string


if __name__ == "__main__":
    print(deploy_mongodb("1741647285"))
    # print(deploy_mongodb(str(int(time.time()))))
