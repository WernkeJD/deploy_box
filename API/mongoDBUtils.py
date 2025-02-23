import dotenv
import os
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
dotenv.load_dotenv()

MONGODB_TOKEN = os.environ.get("MONGODB_TOKEN")
MONGODB_ORG_ID = os.environ.get("MONGODB_ORG_ID")
MONGODB_CLIENT_ID = os.environ.get("MONGODB_CLIENT_ID")
MONGODB_CLIENT_SECRET = os.environ.get("MONGODB_CLIENT_SECRET")

def get_mongodb_token():
    global MONGODB_TOKEN

    if MONGODB_TOKEN:
        return MONGODB_TOKEN

    url = "https://cloud.mongodb.com/api/oauth/token"
    payload = {
        "grant_type": "client_credentials"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    auth = (MONGODB_CLIENT_ID, MONGODB_CLIENT_SECRET)
    response = requests.post(url, data=payload, headers=headers, auth=auth)
    response.raise_for_status()
    MONGODB_TOKEN = response.json().get("access_token")
    print(MONGODB_TOKEN)
    return MONGODB_TOKEN


def request_helper(url, method="GET", data=None):
    global MONGODB_TOKEN

    while True:
        headers = {
            "Authorization": f"Bearer {MONGODB_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.atlas.2023-01-01+json"
        }
            
        try:
            response = None
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)

            if response.status_code == 401:
                MONGODB_TOKEN = None
                get_mongodb_token()
                continue


            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            return err
        except Exception as e:
            return e


def deploy_mongodb(projectName: str):
    cluster_already_exists_flag = False

    try:
        # Get the project id
        project_id = None
        response = request_helper("https://cloud.mongodb.com/api/atlas/v2/groups", "GET")
        projects = response.get("results", [])
        for project in projects:
            if project.get("name") == projectName:
                if project.get("clusterCount") > 0:
                    print("Cluster already exists")
                    cluster_already_exists_flag = True
                project_id = project.get("id")
                break
            
        if not project_id:
            response = request_helper("https://cloud.mongodb.com/api/atlas/v2/groups", "POST", {"name": projectName, "orgId": MONGODB_ORG_ID})
            project_id = response.get("id")

 
        # Check if the cluster already exists
        # response = request_helper(f"https://cloud.mongodb.com/api/atlas/v2/groups/{project_id}/clusters", "GET")

        # If the cluster already exists, return the cluster details


        if not cluster_already_exists_flag:
            # Create a new cluster
            # Set up the Selenium WebDriver
            chrome_options = Options()
            # chrome_options.add_argument("--headless")  # Headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            # Automatically download and set up the ChromeDriver
            driver = webdriver.Chrome(options=chrome_options)
            actions = ActionChains(driver)
            wait = WebDriverWait(driver, 10)

            # Navigate to MongoDB website
            # driver.get(f"https://cloud.mongodb.com/v2/{project_id}#/clusters/starterTemplates")
            driver.get("https://account.mongodb.com/account/login")

            time.sleep(2)

            # Find the email input field and enter the email
            email_input = driver.find_element(By.ID, "username")
            email_input.send_keys(os.environ.get("MONGODB_EMAIL"))

            next_button = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[1]/form/footer/button/div[2]")
            next_button.click()

            time.sleep(2)

            # Find the password input field and enter the password
            password_input = driver.find_element(By.ID, "lg-passwordinput-1")
            password_input.send_keys(os.environ.get("MONGODB_PASSWORD"))
            password_input.send_keys(u'\ue007')

            attempts = 5

            while attempts > 0:
                time.sleep(5)
                attempts -= 1

                password_input = driver.find_element(By.ID, "lg-passwordinput-1")
                if not password_input:
                    continue

                password_input.send_keys(u'\ue007')

            #     login_button = driver.find_elements(By.XPATH, "/html/body/div[1]/div/div[1]/form/footer/button/div[2]")
            #     if login_button and login_button[0].text == "Login":
            #         login_button[0].click()
            #         time.sleep(4)

            # Wait for the page to load completely
            time.sleep(7)

            reset_button = driver.find_elements(By.CSS_SELECTOR, '[data-testid="reset-button"]')
            if reset_button and reset_button[0].text == "Reset":
                reset_button[0].click()
                time.sleep(6)

            # Select tier
            tier_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="template-cards-m0"]')))
            tier_button.click()

            time.sleep(2)

            # Deselect Preloaded sample data
            sample_data_button = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div/div/div/div[3]/main/div[1]/div/div/div[2]/div[4]/div[2]/div/div[2]/div[1]/label/span')))
            sample_data_button.click()

            # Choose a cloud provider
            cloud_provider_button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div/div[3]/main/div[1]/div/div/div[2]/div[4]/div[1]/div[1]/div[2]/div/label[2]/div')
            cloud_provider_button.click()

            # Deploy the cluster
            deploy_button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div/div[3]/main/div[1]/footer/div/div/button[2]/div[2]')
            if deploy_button.text == "Create Deployment":
                deploy_button.click()
            else:
                print("Error deploying cluster")

            # Close the browser after actions are complete
            time.sleep(5)
            driver.quit()

        # Create database user
        databaseRole = "databaseUserRole"
        response = request_helper(f"https://cloud.mongodb.com/api/atlas/v2/groups/{project_id}/customDBRoles/databaseUserRole", "GET")

        if not isinstance(response, requests.exceptions.HTTPError):
            print("Database user role already exists")
            databaseRole = response.get("results")[0]
        else:

            response = request_helper(f"https://cloud.mongodb.com/api/atlas/v2/groups/{project_id}/customDBRoles/roles", "POST", {
        "actions": [
            {
                "action": "FIND",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "INSERT",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "REMOVE",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "UPDATE",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "BYPASS_DOCUMENT_VALIDATION",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "CREATE_COLLECTION",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "CREATE_INDEX",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "DROP_COLLECTION",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "CHANGE_STREAM",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "COLL_MOD",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "COMPACT",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "CONVERT_TO_CAPPED",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "DROP_INDEX",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "RE_INDEX",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "COLL_STATS",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "DB_HASH",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "LIST_INDEXES",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            },
            {
                "action": "VALIDATE",
                "resources": [
                    {
                        "collection": "Cluster0",
                        "db": "testingProject"
                    }
                ]
            }
        ],
        "inheritedRoles": [],
        "roleName": "databaseUserRole"
    })
            
            print(response)

        # Create a database user
        response = request_helper(f"https://cloud.mongodb.com/api/atlas/v2/groups/{project_id}/databaseUsers", "POST", {
            "databaseName": "Cluster0",
            "password": "password",
            "roles": [
                {
                    "databaseName": "Cluster0",
                    "roleName": "databaseUserRole"
                }
            ],
            "username": "admin"
        })

    except KeyboardInterrupt:
        driver.quit()

if __name__ == '__main__':
    print(deploy_mongodb())
    