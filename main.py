import cv2
import queue
import threading
import time

import numpy as np
#
from builder import frame_data_builder
from frame_decoder import FrameDecoder
from h264_unit import H264Unit
from nalu_parser import NALUParser
from server import TCPServer

# Frame queue for buffering decoded frames
frame_queue = queue.Queue()


# Function to handle data reception and processing
def data_receiver():
    server = TCPServer()
    parser = NALUParser()

    def on_data_received(data, count):
        parser.enqueue(data, count)

    def unit_handler(unit: H264Unit, count):
        decoder = FrameDecoder()
        print(f"unit: type - {unit.type} [{unit.type_number}], length - {unit.byte_length}")
        build_data = frame_data_builder.build(unit)
        if build_data is None:
            return

        # Decode the frame data
        frame = decoder.decode(build_data, 1)
        if frame is not None:
            print("Frame received and decoded", frame.shape)
            cv2.imshow("MyWindow", frame)

            key = cv2.waitKey(1)
            if key & 0xFF == ord('q'):
                return

    server.received_data_handler = on_data_received
    parser.h264_unit_handler = unit_handler
    server.start()

    try:
        while True:
            time.sleep(1)  # Keep the thread alive
    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        print("Stopped by user.")
    except Exception as e:
        print(f"Error in data receiver: {e}")
    finally:
        server.stop()


if __name__ == '__main__':
    data_receiver()
