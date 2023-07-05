from flask import Flask, render_template, request, redirect, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import uuid
import os
import openai
import requests

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'tea58/BUCK/MAG'
OPENAI_API_KEY = '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'
socketio = SocketIO(app, async_mode='eventlet')

DB_FILE = 'db.json'


def load_data():
    try:
        with open(DB_FILE, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        return {'menu': [], 'orders': []}


def save_data(data):
    with open(DB_FILE, 'w') as file:
        json.dump(data, file, indent=4)

@socketio.on('update_order_status')
def handle_update_order_status(data):
    # Retrieve the order ID and updated status from the received data
    order_id = data['order_id']
    updated_status = data['status']

    # Update the order status in the data dictionary
    data = load_data()
    orders = data['orders']
    for order in orders:
        if order['id'] == order_id:
            order['status'] = updated_status
            save_data(data)
            break

    # Emit the updated status to the client
    emit('order_status_updated', {'order_id': order_id, 'status': updated_status}, broadcast=True)

def get_chatbot_response(query):
    print(query)
    prompt = f"User: {query}\nChatbot: Hi! How can I assist you today?\nUser: {query}\nChatbot:\n- What are your operation hours?|Our operation hours are from 9 AM to 6 PM.\n- What is the status of my order?|Please provide your order ID, and we will check the status for you.\n- What is your most popular dish?|Our most popular dish is the Spicy Chicken Pasta.\n\nUser:"
    
    payload = {
        'prompt': prompt,
        'max_tokens': 100
    }
    
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        'https://api.openai.com/v1/engines/text-davinci-003/completions',
        data=json.dumps(payload),
        headers=headers
    )
    
    if response.status_code == 200:
        chatbot_response = response.json()['choices'][0]['text'].strip()
        return chatbot_response
    else:
        return "Oops! Something went wrong with the chatbot."




@app.route('/menu', methods=['GET'])
def display_menu():
    data = load_data()
    menu = data['menu']
    return jsonify({"menu":menu})

@app.route('/users', methods=['GET'])
def display_users():
    data = load_data()
    users = data['users']
    return jsonify({"users":users})


@app.route('/add_dish', methods=['POST'])
def add_dish():
    request_data = request.get_json()
    data = load_data()

    dish_id = str(uuid.uuid4())
    new_dish = {
        'id': dish_id,
        'name': request_data['name'],
        'price': request_data['price'],
        'availability': request_data['availability']
    }

    data['menu'].append(new_dish)
    save_data(data)

    return jsonify({"msg" : "New dish has been added!!"})


@app.route('/remove_dish/<id>', methods=['DELETE'])
def remove_dish(id):
    
    data = load_data()

    menu = data['menu']
    for dish in menu:
        if dish['id'] == id:
            menu.remove(dish)
            save_data(data)
            break

    return jsonify({"msg" : "Dish has been removed from menu successfully!!", "menu" : menu})


@app.route('/update_availability', methods=['POST'])
def update_availability():
    request_data = request.get_json()
    data = load_data()

    menu = data['menu']
    for dish in menu:
        if dish['id'] == request_data['id']:
            dish['availability'] = request_data['availability']
            save_data(data)
            break

    return jsonify({"msg" : "Dish status has been updated successfully!!", "menu" : menu})


@app.route('/take_order', methods=['POST'])
def take_order():
    request_data = request.get_json()
    data = load_data()
    menu = data["menu"]
    flag = False
    price = 0
    for dish in menu:
        if request_data["id"] == dish["id"]:
            flag = True
            price = dish['price']
    if flag == True:
     order_id = str(uuid.uuid4())
     new_order = {
        'id': order_id,
        'customer_name': request_data['name'],
        'dishes': request_data['dishes'],
        'price' : price,
        'status': 'Received',
        'dishid' : request_data["disid"],
        'userid' : request_data["userid"]
     }

     data['orders'].append(new_order)
     save_data(data)

     return jsonify({'msg': 'Order taken successfully'})
    else: 
     return jsonify({"msg" : "Ordered dish is not present at this moment"})


@app.route('/update_order', methods=['PATCH'])
def update_order():
    request_data = request.get_json()
    data = load_data()
    flag = False
    orders = data['orders']
    for order in orders:
        if order['id'] == request_data['id']:
            order['status'] = request_data['status']
            flag = True
            save_data(data)
            break
    if flag == True:
        # Emit the updated status to all connected clients
        socketio.emit('order_status_updated', {'order_id': request_data['id'], 'status': request_data['status']})
        return jsonify({'msg': 'Order status updated successfully'})
    else:
        return jsonify({"msg" : 'Order not found!!'})




@app.route('/review_orders', methods=['GET'])
def review_orders():
    data = load_data()
    orders = data['orders']
    return jsonify({'orders': orders})

@app.route('/add_review/<order_id>', methods=['PATCH'])
def add_review(order_id):
    request_data = request.get_json()
    data = load_data()
    orders = data['orders']
    for order in orders:
        if order['id'] == order_id:
            order['rating'] = request_data['rating']
            order['review'] = request_data['review']
            save_data(data)
            return jsonify({'msg': 'Review added successfully'})
    return jsonify({"msg" : 'Order not found!!'})

@app.route('/chatbot', methods=['POST'])
def chatbot():
    request_data = request.get_json()
    user_query = request_data['query']

    # Get the chatbot's response for the user query
    chatbot_response = get_chatbot_response(user_query)

    # Return the response as JSON
    return jsonify({'response': chatbot_response})



if __name__ == '__main__':
    app.run(debug=True)
