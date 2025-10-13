#UDP Video Streaming Server

import cv2
import socket
import struct
import math
import time

# Settings
DEST_IP   = "127.0.0.1"   # client IP
DEST_PORT = 9999          # client port
VIDEO_SRC = 0            # 0 = webcam, or "video.mp4" for file
PAYLOAD   = 1400          # bytes per UDP packet (safe size)
JPEG_QUALITY = 60        # lower = smaller size

# Header format: frame_id (int), packet_id (short), total_packets (short)
HEADER_STRUCT = "!IHH"

def main():
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dest = (DEST_IP, DEST_PORT)

    # Open video (0 = webcam)
    cap = cv2.VideoCapture(VIDEO_SRC)
    if not cap.isOpened():
        print("Error: cannot open video source")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0: fps = 25
    frame_interval = 1 / fps

    frame_id = 0
    print("Server started, streaming to", dest)

    while True:
        start = time.time()
        ret, frame = cap.read()
        if not ret:
            print("Video ended or camera error.")
            break

        # Encode as JPEG
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
        ok, encimg = cv2.imencode(".jpg", frame, encode_param)
        if not ok:
            continue
        data = encimg.tobytes()

        # Split into chunks
        chunk_size = PAYLOAD - struct.calcsize(HEADER_STRUCT)
        total_packets = math.ceil(len(data) / chunk_size)

        for pkt_id in range(total_packets):
            start_byte = pkt_id * chunk_size
            end_byte   = start_byte + chunk_size
            chunk = data[start_byte:end_byte]
            header = struct.pack(HEADER_STRUCT, frame_id, pkt_id, total_packets)
            sock.sendto(header + chunk, dest)

        frame_id += 1

        # keep fps stable
        elapsed = time.time() - start
        if elapsed < frame_interval:
            time.sleep(frame_interval - elapsed)

    cap.release()
    sock.close()

if __name__ == "__main__":
    main()
