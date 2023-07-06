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
    prompt = f"User: {query}\nChatbot: Hi! How can I assist you today?\nUser: {query}\nChatbot:\n- How can I place an order for food?|To place an order for food, you can browse our menu and select the items you'd like to order. Then, proceed to the checkout and provide the necessary details to complete the order.\n- What are the available options for ordering food?|We offer various options for ordering food, including online ordering through our website or mobile app, as well as phone-in orders.\n- Is there a delivery service for food orders?|Yes, we provide delivery service for food orders. Simply provide your delivery address during the ordering process, and our delivery team will ensure your food is delivered to your doorstep.\n- How long does it take to receive the food after placing an order?|The delivery time can vary depending on factors such as distance and order volume. However, we strive to deliver orders as quickly as possible, usually within 30-45 minutes.\n- What is the process for making changes to my food order?|If you need to make changes to your food order, please contact our customer support team as soon as possible. They will assist you with the necessary modifications.\n- Are there any special instructions or requirements for ordering food?|If you have any special instructions or specific requirements for your food order, such as dietary restrictions or allergen concerns, please mention them while placing your order. We'll do our best to accommodate your needs.\n- Can I customize my food order with specific preferences or dietary restrictions?|Certainly! We offer customization options for our food orders. You can specify your preferences and dietary restrictions during the ordering process, and we'll prepare your food accordingly.\n- What payment methods are accepted for food orders?|We accept various payment methods, including credit cards, debit cards, and online payment platforms like PayPal. Cash on delivery is also available in certain areas.\n- Is there a minimum order requirement for delivery?|Yes, we have a minimum order requirement for delivery. The specific minimum order amount may vary based on your location. Please check the details during the ordering process.\n- How can I track the status of my food order?|Once you've placed your order, you'll receive an order confirmation with a tracking number. You can use this tracking number to monitor the status of your order through our website or mobile app.\n\nUser:"
    
    payload = {
        'prompt': prompt,
        'max_tokens': 100,
        'model': 'gpt-3.5-turbo-0301'
    }
    
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        'https://api.openai.com/v1/engines/davinci-codex/completions',
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
        'dishid' : request_data["id"],
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

@app.route('/reviews/<id>', methods=['PATCH'])
def add_reviews(id):
    data = load_data()
    menu = data['menu']
    request_data = request.get_json()
    flag = False
    for dish in menu:
        if dish['id'] == id:
          if 'review' in dish and 'rating' in dish:
                dish['review'].append(request.json['review'])
                dish['rating'].append(int(request.json['rating']))
          else:
                dish['review'] = [request_data['review']]
                dish['rating'] = [int(request_data['rating'])]
          flag =True
          save_data(data)
          break
    if flag == True:    
        return jsonify({"msg" : "Review has been added"}), 200
    else:
        return jsonify({'msg': 'Invalid review or rating'}), 400

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
