import socket
import struct

import av
import cv2
import numpy as np

from h264_unit import H264Unit

# H.264 start code (used to indicate NAL units)
NALU_START_CODE = b'\x00\x00\x00\x01'


def replace_length_with_start_code(nalu_data):
    """Replace the 4-byte length information at the beginning of a NAL unit with a start code."""
    return NALU_START_CODE + nalu_data[4:]


def extract_sps_pps(frame_data):
    """
    Extract SPS and PPS NAL units from an i-frame.
    Frame data should be a single i-frame sample buffer.
    Returns the SPS and PPS NALUs as byte arrays.
    """
    sps = pps = None
    offset = 0
    while offset < len(frame_data):
        nalu_len = struct.unpack('>I', frame_data[offset:offset + 4])[0]  # 4-byte length prefix
        nalu_data = frame_data[offset + 4:offset + 4 + nalu_len]

        # NALU type is the first byte's last 5 bits (type = byte & 0x1F)
        nalu_type = nalu_data[0] & 0x1F

        # SPS NALU type is 7, PPS NALU type is 8
        if nalu_type == 7:
            sps = replace_length_with_start_code(nalu_data)
        elif nalu_type == 8:
            pps = replace_length_with_start_code(nalu_data)

        offset += 4 + nalu_len

    return sps, pps


def process_frame(frame_data, is_key_frame):
    """
    Process a video frame. If it's a key frame (i-frame), add SPS and PPS data at the start.
    """
    # If keyframe, extract SPS/PPS and prepend to frame data
    if is_key_frame:
        sps, pps = extract_sps_pps(frame_data)
        if sps and pps:
            # Prepend SPS and PPS NAL units to the frame data with start codes
            processed_data = sps + pps + replace_length_with_start_code(frame_data)
        else:
            processed_data = replace_length_with_start_code(frame_data)
    else:
        # For p-frames and other types, just replace the length with start code
        processed_data = replace_length_with_start_code(frame_data)

    return processed_data


def run_tcp_server(host='0.0.0.0', port=6969):
    """Sets up a TCP server to receive and process H.264 video data."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"Server is listening on {host}:{port}")
    count = 0
    while True:
        conn, addr = server_socket.accept()
        print(f"Connected by {addr}")

        try:
            # Loop to receive and process incoming frames
            while count < 20:
                count += 1
                # Read 4 bytes to get the frame length
                length_prefix = conn.recv(4)
                print(length_prefix)
                if not length_prefix:
                    print("Connection closed by client.")
                    break

                frame_length = struct.unpack('>I', length_prefix)[0]

                # Receive the entire frame based on the length prefix
                frame_data = conn.recv(frame_length)
                if not frame_data:
                    print("Incomplete frame data received.")
                    break

                unit = H264Unit(frame_data)
                data_length = None
                if unit.length_data is not None:
                    data_length = struct.unpack('>I', unit.length_data)[0]

                print(f"frame_length: {frame_length}")
                print(f"Processed frame (key-frame: {unit.type == 'vcl'}), length: {data_length} bytes, type: {unit.type}")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            conn.close()
            print(f"Connection with {addr} closed.")


# Run the server
run_tcp_server()