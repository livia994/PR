import socket
import threading

# Shared resource (file) and synchronization mechanism
file_path = "shared_file.txt"
write_lock = threading.Lock()  # Lock to ensure write completion before read

# Function to handle read requests
def handle_read(conn, addr):
    with write_lock:  # Ensure no writes are ongoing while reading
        with open(file_path, 'r') as file:
            data = file.read()
        conn.sendall(data.encode())  # Send data back to the client

# Function to handle write requests
def handle_write(conn, addr, data):
    with write_lock:  # Ensure no reads occur during write
        with open(file_path, 'a') as file:
            file.write(data + '\n')
        conn.sendall(b'Write operation successful')

# Function to handle each client connection
def handle_client(conn, addr):
    print(f"Connected by {addr}")
    try:
        while True:
            # Receive the command from the client
            message = conn.recv(1024).decode()

            if message.startswith("READ"):
                handle_read(conn, addr)
            elif message.startswith("WRITE"):
                data = message.split(" ", 1)[1]
                handle_write(conn, addr, data)
            else:
                conn.sendall(b"Invalid command")
    except:
        pass
    finally:
        conn.close()

# Create a TCP/IP socket and listen for connections
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 12347))  # Use port 12345 (you can change it)
server.listen(5)

print("TCP server listening on port 12347")

# Accept client connections
while True:
    conn, addr = server.accept()
    threading.Thread(target=handle_client, args=(conn, addr)).start()
