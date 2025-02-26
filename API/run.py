from flask import Flask, jsonify, request
from mongoDBUtils import deploy_mongodb

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({'message': 'Welcome to the API!'})

@app.route('/api/deployMERNStack', methods=['POST'])
def deploy_mern_stack():
    data = request.get_json()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)