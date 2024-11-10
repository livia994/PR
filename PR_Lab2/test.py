from flask import Flask, request, jsonify
import socket

app = Flask(__name__)

# Function to send message to the TCP server
def send_to_tcp_server(message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', 12346))  # Connect to the TCP server
        s.sendall(message.encode())
        response = s.recv(1024).decode()  # Get response from the server
    return response

@app.route('/read_from_file', methods=['GET'])
def read_from_file():
    response = send_to_tcp_server("READ")  # Send "READ" command to TCP server
    return jsonify({"file_content": response})

@app.route('/write_to_file', methods=['POST'])
def write_to_file():
    data = request.get_json()  # Get JSON data from request
    content = data.get("content")
    if content:
        response = send_to_tcp_server(f"WRITE {content}")  # Send "WRITE" command to TCP server
        return jsonify({"message": response})
    else:
        return jsonify({"error": "No content provided"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5001)
