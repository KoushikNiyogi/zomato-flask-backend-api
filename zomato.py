from flask import Flask, render_template, request, redirect, jsonify
from flask_cors import CORS
import json
import uuid

app = Flask(__name__)
CORS(app, origins='*')
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


@app.route('/menu', methods=['GET'])
def display_menu():
    data = load_data()
    menu = data['menu']
    return jsonify({"menu":menu})


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

    return redirect('/menu')


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
        'dishes': request_data['id'],
        'price' : price,
        'status': 'received'
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
        return jsonify({'msg': 'Order status updated successfully'})
    else:
        return jsonify({"msg" : 'Order not found!!'})


@app.route('/review_orders', methods=['GET'])
def review_orders():
    data = load_data()
    orders = data['orders']
    return jsonify({'orders': orders})


if __name__ == '__main__':
    app.run(debug=True)
