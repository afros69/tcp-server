import struct
import time

import av

from converter import converter
from h264_unit import H264Unit
from nalu_parser import NALUParser
from server import TCPServer

# Initialize PyAV codec context
codec = av.CodecContext.create('h264', 'r')


def on_data_received(data, count):
    parser.enqueue(data, count)


# Accumulator buffer for NAL units
nal_buffer = bytearray()


def unit_handler(unit: H264Unit, count):
    data_length = None
    if unit.length_data is not None:
        data_length = struct.unpack('>I', unit.length_data)[0]
    print(f"unit: type - {unit.type} [{unit.type_number}], length-data - {data_length} count- {count}")
    frame = converter.convert(unit)
    if frame is not None:
        print("Frame is here!!!")


server = TCPServer(host="0.0.0.0", port=6969)
parser = NALUParser()
parser.h264_unit_handler = unit_handler


server.received_data_handler = on_data_received

if __name__ == '__main__':
    server.start()
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
        print("Server stopped by user.")

