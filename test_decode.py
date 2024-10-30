import cv2

from an_data import test_byte_array
from builder import frame_data_builder
from frame_decoder import FrameDecoder
from h264_unit import H264Unit
from nalu_parser import NALUParser


def test():
    decoder = FrameDecoder()

    def test_unit_handler(unit: H264Unit, count):
        print(f"unit: type - {unit.type} [{unit.type_number}], length - {unit.byte_length}")
        build_data = frame_data_builder.build(unit)
        if build_data is None:
            return

        for i in [4]:
            frame = decoder.decode(build_data, i)
            if frame is not None:
                print("Frame is here!!!")
                cv2.imwrite(f"frames/frame{i}.png", frame)
            else:
                print("Frame is not here (")

    parser = NALUParser()
    parser.h264_unit_handler = test_unit_handler
    parser.enqueue(test_byte_array, 1)


if __name__ == '__main__':
    test()