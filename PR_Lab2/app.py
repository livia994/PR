from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, join_room, leave_room, send
import os
import json
from flask_sqlalchemy import SQLAlchemy
import pymysql
import time


app = Flask(__name__) # Creates a flask application instance
app.config['SECRET_KEY'] = 'key123'
socketio = SocketIO(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:rootpassword@db:3306/floralsoul_data'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # To disable Flask-SQLAlchemy modification tracking
db = SQLAlchemy(app)

UPLOAD_FOLDER = './uploads' # defines a variable for the directory path where uploaded files will be stored
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER #stores the upload folder path in the Flask app's config


def wait_for_mysql():
    retries = 5  # Number of retries
    delay = 5  # Delay between retries in seconds
    for _ in range(retries):
        try:
            connection = pymysql.connect(
                host='db',
                user='root',
                password='rootpassword',
                database='floralsoul_data'
            )
            connection.close()  # Close the connection if successful
            print("Connected to MySQL database")
            return True
        except pymysql.MySQLError as e:
            print(f"Waiting for MySQL database: {e}")
            time.sleep(delay)  # Wait before retrying
    return False

# It will wait for the database before running the app
if not wait_for_mysql():
    print("Could not connect to MySQL database after retries.")
    exit(1)  # Exit if we can't connect to the database
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric(10, 2))
    link = db.Column(db.String(500), unique=True)
    category = db.Column(db.String(100))
    size = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Product {self.name}>'

with app.app_context():
    db.create_all()

@app.route('/chat')
def chat():
    return render_template('chat.html')


@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    send(f'{username} has entered the room.', room=room)


@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(f'{username} has left the room.', room=room)


@socketio.on('message')
def handle_message(data):
    room = data['room']
    message = data['message']
    send(message, room=room)

# CREATE - Add a new product
"""{
  "name": "Create Product Name",
  "price": 19.99,
  "category": "Create Category",
  "size": "Large"
}
"""
@app.route('/products', methods=['POST'])
def create_product():
    try:
        data = request.get_json()

        required_fields = ['name', 'price', 'category', 'size']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        new_product = Product(
            name=data['name'],
            price=data['price'],
            category=data['category'],
            size=data['size']
        )

        db.session.add(new_product)
        db.session.commit()

        return jsonify({
            'message': 'Product created successfully',
            'id': new_product.id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# READ - Get all products with pagination & link for pagination: http://localhost:5000/products?limit=4&offset=0
@app.route('/products', methods=['GET'])
def get_products():
    try:
        product_id = request.args.get('id')
        name = request.args.get('name')
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 10))

        if product_id:
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            return jsonify({
                'id': product.id,
                'name': product.name,
                'price': str(product.price),
                'category': product.category,
                'size': product.size,
                'created_at': product.created_at
            })

        query = Product.query
        if name:
            query = query.filter(Product.name.like(f"%{name}%"))
        products = query.offset(offset).limit(limit).all()

        return jsonify([{
            'id': product.id,
            'name': product.name,
            'price': str(product.price),
            'category': product.category,
            'size': product.size,
            'created_at': product.created_at
        } for product in products])

    except Exception as e:
        return jsonify({'error': str(e)}), 500



# UPDATE - Update a product, link to use http://localhost:5000/products?id=2 this is update by id
"""{
  "name": "Updated Product Name",
  "price": 19.99,
  "category": "Updated Category",
  "size": "Large"
}
"""
@app.route('/products', methods=['PUT'])
def update_product():
    try:
        product_id = request.args.get('id')
        if not product_id:
            return jsonify({'error': 'Product ID is required'}), 400

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No update data provided'}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        for key, value in data.items():
            if hasattr(product, key):
                setattr(product, key, value)

        db.session.commit()

        return jsonify({'message': 'Product updated successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# DELETE - Delete a product
@app.route('/products', methods=['DELETE'])
def delete_product():
    try:
        product_id = request.args.get('id')
        if not product_id:
            return jsonify({'error': 'Product ID is required'}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        db.session.delete(product)
        db.session.commit()

        return jsonify({'message': 'Product deleted successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# FILE UPLOAD - Accepts multipart/form-data file uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.json'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename) # file is saved in the folder for upload
        file.save(file_path)

        # Optional Read and parse the JSON file
        with open(file_path, 'r') as f: # opens file in read mode
            file_content = json.load(f) # converts the json file into a python dictionary to be easier to work with

        return jsonify({'message': 'File uploaded successfully', 'content': file_content}), 201
    else:
        return jsonify({'error': 'Only JSON files are allowed'}), 400

if __name__ == '__main__':
    socketio.run(app, port=5000, allow_unsafe_werkzeug=True)
