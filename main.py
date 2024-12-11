from datetime import datetime

import cv2
import queue
import threading
import time

import numpy as np
#
from builder import frame_data_builder
from frame_decoder import FrameDecoder
from frame_processor import FrameProcessor
from h264_unit import H264Unit
from nalu_parser import NALUParser
from server import TCPServer

# Frame queue for buffering decoded frames
frame_queue = queue.Queue()


def get_fps_info(fps_data):
    fps_data["count"] = fps_data["count"] + 1
    frame_count = fps_data["count"]
    prev = fps_data["start"]
    now = datetime.now()
    seconds_pass = (now - prev).total_seconds()
    fps_data["start"] = now
    fps = round(1 / seconds_pass)
    fps_string = f"FPS: {fps} / FC: {frame_count} {now.strftime("%H:%M:%S")}"
    return fps_string

# Function to handle data reception and processing
def data_receiver():
    server = TCPServer()
    parser = NALUParser()
    frame_processor = FrameProcessor()
    fps_data = {"count": 0, "start": datetime.now()}

    def on_data_received(data, count):
        parser.enqueue(data, count)

    def unit_handler(unit: H264Unit, count):
        decoder = FrameDecoder()
        print(f"unit: type - {unit.type} [{unit.type_number}], length - {unit.byte_length}")
        build_data = frame_data_builder.build(unit)
        if build_data is None:
            return

        # fps_string = get_fps_info(fps_data)
        # print(fps_string)
        # Decode the frame data
        frame = decoder.decode(build_data, 1)
        # frame = frame_processor.nal_units_to_cv2_frame(build_data)
        if frame is not None:
            fps_string = get_fps_info(fps_data)
            print("Frame received and decoded", frame.shape)
            cv2.putText(frame, fps_string, (7, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 255, 0), 3, cv2.LINE_AA)
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
        frame_processor.close()


if __name__ == '__main__':
    data_receiver()
