import requests
import json
from pymongo import MongoClient

def invoice(data, token):
    headers ={
        "Authorization": f"Bearer {token}",
        'Content-Type': 'application/json'
    }  
    url = "http://localhost:8000/payments/create-invoice"

    response = requests.post(url, data=data, headers=headers)
    print(response.json())
    
def get_customer_id(user_id, token):
    headers ={
        "Authorization": f"Bearer {token}",
        'Content-Type': 'application/json'
    }  
    url = "http://localhost:8000/payments/get_customer_id"

    user_id = {"user_id": user_id}
    user_id = json.dumps(user_id)

    return requests.post(url, user_id,headers=headers)




def charge_customer():

    token = "HQE9qt5NL8PigIYjvXyoHH5Zcx8AdY"
    headers ={
        "Authorization": f"Bearer {token}"
    }    
    data = requests.get("http://localhost:8000/api/stacks/get_stack_usage_from_db", headers=headers)
    # print("data: ", data.json())

    for stack_id, values in data.json().get('stacks').items():
        user_id, usage = values
        cost = int(round(((usage/1_000_000) * 10)*100, 0))
        customer_id = get_customer_id(user_id=user_id, token=token)
        customer_id = customer_id.json().get("customer_id")

        data = {"customer_id": customer_id, "amount": cost, "description": f"here is your invoice for the database usage totaling {usage}"}

        data = json.dumps(data)

        invoice(data, token)


if __name__ == '__main__':
    charge_customer()