import asyncio
import struct
import tempfile
from collections import deque
from dataclasses import dataclass
from typing import Callable, Optional, Deque

import cv2
import numpy as np


# TCP Server equivalent in Python using asyncio
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
            if self.recieved_data_callback:
                print("data", data, "\n")
                self.recieved_data_callback(data)
        writer.close()
        await writer.wait_closed()

# H.264 NAL Unit equivalent in Python
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

# NALU Parser equivalent in Python
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
                    print("enqueue", h264_unit, "\n")
                    if self.h264_unit_callback:
                        self.h264_unit_callback(h264_unit)
                self.data_stream = self.data_stream[self.search_index+4:]
                self.search_index = 0
            else:
                self.search_index += 1

# H.264 Converter equivalent in Python
class H264Converter:
    def __init__(self):
        self.sps = None
        self.pps = None
        self.sample_buffer_callback: Optional[Callable[[bytes], None]] = None

    def convert(self, h264_unit: H264Unit):
        print("in convert", h264_unit, "\n")
        if h264_unit.nalu_type == 7:
            self.sps = h264_unit
        elif h264_unit.nalu_type == 8:
            self.pps = h264_unit
        else:
            if not (self.sps and self.pps):
                return  # Skip until SPS and PPS are set
            sample_buffer = self.create_sample_buffer(h264_unit)
            if sample_buffer and self.sample_buffer_callback:
                self.sample_buffer_callback(sample_buffer)

    def create_sample_buffer(self, h264_unit: H264Unit) -> bytes:
        # Simplified representation, an actual implementation would involve deeper integration
        return h264_unit.data

# Example usage
async def main():
    server = TCPServer()
    parser = NALUParser()
    converter = H264Converter()

    def display_sample(sample_buffer: bytes):
        print("sample_buffer ", sample_buffer, "\n")

    # Define callbacks for the data flow
    server.recieved_data_callback = parser.enqueue
    parser.h264_unit_callback = converter.convert
    converter.sample_buffer_callback = display_sample

    await server.start(6969)

if __name__ == '__main__':
    # Run the server
    asyncio.run(main())
