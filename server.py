import socket
import threading


class TCPServer:

    def __init__(self, host='0.0.0.0', port=6969):
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_listening = False
        self.received_data_handler = None  # Function to handle incoming data

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.is_listening = True
        print(f"Listening for connections on {self.host}:{self.port}")

        # Start accepting connections in a separate thread
        threading.Thread(target=self.accept_connections, daemon=True).start()

    def accept_connections(self):
        while self.is_listening:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection accepted from {addr}")
            # Start a new thread to handle each client connection
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

    def handle_client(self, client_socket):
        count = 0
        while True:
            count += 1
            try:
                data = client_socket.recv(65000)
                if not data:
                    break
                # with open("an_data.txt", 'a') as file:
                #     file.write(str(data))
                if self.received_data_handler:
                    self.received_data_handler(data, count)
            except ConnectionResetError:
                break
        client_socket.close()
        print("Connection closed")

    def stop(self):
        self.is_listening = False
        if self.server_socket:
            self.server_socket.close()
            print("Server stopped")
