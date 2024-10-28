import socket
import cv2
import numpy as np


def start_tcp_server(host='0.0.0.0', port=6969):
    # Create a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the address and port
    server_socket.bind((host, port))

    # Listen for incoming connections
    server_socket.listen(1)
    print(f"Server listening on {host}:{port}")

    # Wait for a client to connect
    client_socket, client_address = server_socket.accept()
    print(f"Connection from {client_address}")

    # Buffer for incoming data
    data_buffer = bytearray()

    try:
        while True:
            # Receive data in chunks
            data = client_socket.recv(4096)
            if not data:
                break  # No more data, client has closed the connection

            # Append received data to buffer
            data_buffer.extend(data)

            # Decode and display video frames
            while len(data_buffer) > 0:
                # Check for start code
                start_code = b'\x00\x00\x00\x01'  # or b'\x00\x00\x01'
                start_index = data_buffer.find(start_code)

                if start_index == -1:
                    break  # No complete NAL unit found yet

                # Find the end of the NAL unit
                start_index += len(start_code)
                end_index = data_buffer.find(start_code, start_index)

                if end_index == -1:
                    nal_unit = data_buffer[start_index:]  # Last NAL unit
                    break  # Wait for more data to get complete NAL unit
                else:
                    nal_unit = data_buffer[start_index:end_index]

                # Process NAL unit: Convert to OpenCV format (if needed)
                frame = decode_nal_to_frame(nal_unit)

                if frame is not None:
                    cv2.imshow('Received Frame', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                # Remove the processed NAL unit from buffer
                data_buffer = data_buffer[end_index:]

    finally:
        # Clean up the connection
        client_socket.close()
        server_socket.close()
        cv2.destroyAllWindows()
        print(f"Connection from {client_address} closed.")


def decode_nal_to_frame(nal_unit):
    # Create a temporary file to store the NAL unit
    with open('temp.h264', 'wb') as f:
        f.write(nal_unit)

    # Use OpenCV to decode the NAL unit
    cap = cv2.VideoCapture('temp.h264')
    ret, frame = cap.read()
    cap.release()

    return frame


if __name__ == "__main__":
    start_tcp_server()
