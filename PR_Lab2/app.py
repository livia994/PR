from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, join_room, leave_room, send
import pymysql
from datetime import datetime
import os
import json

app = Flask(__name__) # Creates a flask application instance
app.config['SECRET_KEY'] = 'key123'
socketio = SocketIO(app)

UPLOAD_FOLDER = './uploads' # defines a variable for the directory path where uploaded files will be stored
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER #stores the upload folder path in the Flask app's config

def create_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='HintalDiez()25',
            database='floralsoul_data',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return None


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
@app.route('/products', methods=['POST'])  # defines a route for https requests
def create_product():
    try:
        connection = create_connection()
        data = request.get_json()

        required_fields = ['name', 'price', 'category', 'size']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        with connection.cursor() as cursor:
            sql = """
                INSERT INTO products (name, price, category, size, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data['name'],
                data['price'],
                data['category'],
                data['size'],
                datetime.now()
            ))
            connection.commit()

            return jsonify({
                'message': 'Product created successfully',
                'id': cursor.lastrowid
            }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection:
            connection.close()

# READ - Get all products with pagination & link for pagination: http://localhost:5000/products?limit=4&offset=0
@app.route('/products', methods=['GET'])
def get_products():
    try:
        connection = create_connection()
        product_id = request.args.get('id')
        name = request.args.get('name')
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 10))

        with connection.cursor() as cursor:
            if product_id:
                cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
                product = cursor.fetchone()
                return jsonify(product) if product else ('Product not found', 404)
            elif name:
                cursor.execute("SELECT * FROM products WHERE name LIKE %s LIMIT %s OFFSET %s", (f"%{name}%", limit, offset))
                products = cursor.fetchall()
                return jsonify(products)
            else:
                cursor.execute("SELECT * FROM products LIMIT %s OFFSET %s", (limit, offset))
                products = cursor.fetchall()
                return jsonify(products)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection:
            connection.close()

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
        connection = create_connection()
        product_id = request.args.get('id')
        if not product_id:
            return jsonify({'error': 'Product ID is required'}), 400

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No update data provided'}), 400

        update_fields = []
        update_values = []
        for key in ['name', 'price', 'category', 'size']:
            if key in data:
                update_fields.append(f"{key} = %s")
                update_values.append(data[key])

        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400

        update_values.append(product_id)

        with connection.cursor() as cursor:
            sql = f"UPDATE products SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(sql, tuple(update_values))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'error': 'Product not found'}), 404

            return jsonify({'message': 'Product updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection:
            connection.close()

# DELETE - Delete a product
@app.route('/products', methods=['DELETE'])
def delete_product():
    try:
        connection = create_connection()
        product_id = request.args.get('id')
        if not product_id:
            return jsonify({'error': 'Product ID is required'}), 400

        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'error': 'Product not found'}), 404

            return jsonify({'message': 'Product deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection:
            connection.close()

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
    app.run(debug=True)
    socketio.run(app, debug=True)

