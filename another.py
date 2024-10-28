import socket
import cv2
import numpy as np
import struct

# Constants
HOST = '0.0.0.0'  # Listen on all available interfaces
PORT = 6969  # The port you specified
BUFFER_SIZE = 65536  # Buffer size for incoming data

def main():
    # Create a TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)

    print(f'Server listening on {HOST}:{PORT}...')

    # Accept a connection from the client
    conn, addr = server_socket.accept()
    print(f'Connection established with {addr}')

    try:
        while True:
            # Read metadata (e.g., frame size) first, assuming it's sent before the actual video data
            metadata = conn.recv(8)  # Assuming the first 8 bytes are metadata (e.g., frame width and height)
            if not metadata:
                break

            # Unpack the metadata
            frame_size = struct.unpack('!I', metadata[:4])[0]  # First 4 bytes might be frame size
            frame_data = conn.recv(frame_size)  # Receive the actual frame data

            if not frame_data:
                break

            # Convert received data into a NumPy array and decode
            np_data = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
            print(frame)

            # if frame is not None:
            #     cv2.imshow('Received Frame', frame)  # Display the received frame
            #
            # # Check for 'q' key to exit
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break

    except Exception as e:
        print(f'Error: {e}')
    finally:
        conn.close()
        server_socket.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
