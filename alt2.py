import asyncio
import struct
import av  # For H.264 decoding and frame processing
import cv2  # For real-time video display
from collections import deque
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np


# TCP Server
class TCPServer:
    def __init__(self):
        self.listener = None
        self.recieved_data_callback: Optional[Callable[[bytes], None]] = None

    async def start(self, port: int):
        self.listener = await asyncio.start_server(self.handle_connection, '0.0.0.0', port)
        print(f"Listening on port {port}")
        async with self.listener:
            await self.listener.serve_forever()

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        print("New connection established")
        while True:
            data = await reader.read(65000)
            if not data:
                break
            np_data = np.frombuffer(data, np.uint8)

                # Decode the H.264 data using OpenCV
                # Note: Make sure to have proper decoders installed and configured
            frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
            print(frame)

            if self.recieved_data_callback:
                self.recieved_data_callback(data)
        writer.close()
        await writer.wait_closed()

# H.264 NAL Unit
@dataclass
class H264Unit:
    payload: bytes

    @property
    def nalu_type(self):
        return self.payload[0] & 0x1F

    @property
    def data(self) -> bytes:
        if self.nalu_type == 7:  # SPS
            return self.payload
        elif self.nalu_type == 8:  # PPS
            return self.payload
        else:
            length_prefix = struct.pack(">I", len(self.payload))
            return length_prefix + self.payload

# NALU Parser
class NALUParser:
    def __init__(self):
        self.data_stream = bytearray()
        self.search_index = 0
        self.h264_unit_callback: Optional[Callable[[H264Unit], None]] = None

    def enqueue(self, data: bytes):
        self.data_stream.extend(data)
        while self.search_index < len(self.data_stream) - 3:
            if self.data_stream[self.search_index:self.search_index+4] == b'\x00\x00\x00\x01':
                if self.search_index != 0:
                    nalu_data = self.data_stream[:self.search_index]
                    h264_unit = H264Unit(nalu_data)
                    if self.h264_unit_callback:
                        self.h264_unit_callback(h264_unit)
                self.data_stream = self.data_stream[self.search_index+4:]
                self.search_index = 0
            else:
                self.search_index += 1

# H.264 Converter and Real-Time Display
class H264Converter:
    def __init__(self):
        self.sps = None
        self.pps = None
        # self.container = av.open(format="h264", mode="r")  # Dummy container for stream processing
        self.frame_queue = deque(maxlen=10)  # Store frames temporarily for real-time display

    def convert(self, h264_unit: H264Unit):
        if h264_unit.nalu_type == 7:
            self.sps = h264_unit
        elif h264_unit.nalu_type == 8:
            self.pps = h264_unit
        else:
            if not (self.sps and self.pps):
                return  # Skip until SPS and PPS are set
            self.decode_and_display_frame(h264_unit.data)

    def decode_and_display_frame(self, frame_data: bytes):
        # PyAV needs a packet to process video data
        packet = av.Packet(frame_data)
        # Feed the packet to PyAV's internal decode
        for frame in packet.decode():
            print(frame)
            # Convert frame to numpy array for OpenCV
            img = frame.to_ndarray(format="bgr24")
            # Display frame using OpenCV
            cv2.imshow("Real-Time Video", img)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    def close(self):
        cv2.destroyAllWindows()

# Example usage
async def main():
    server = TCPServer()
    parser = NALUParser()
    converter = H264Converter()

    # Define callbacks for the data flow
    server.recieved_data_callback = parser.enqueue
    parser.h264_unit_callback = converter.convert

    try:
        await server.start(6969)
    finally:
        converter.close()

# Run the server
asyncio.run(main())
