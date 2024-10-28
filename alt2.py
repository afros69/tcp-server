import av
import cv2


def alt2_decode(frame_data: bytes):
    packet = av.Packet(frame_data)
    for frame in packet.decode():
        img = frame.to_ndarray(format="bgr24")
        cv2.imwrite("alt2.png", img)
