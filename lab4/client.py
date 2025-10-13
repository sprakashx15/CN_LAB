#video streaming UDP


import cv2
import socket
import struct
import numpy as np

LISTEN_IP   = "0.0.0.0"   # listen on all interfaces
LISTEN_PORT = 9999
BUFFER_SIZE = 65535
HEADER_STRUCT = "!IHH"

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_IP, LISTEN_PORT))
    print("Client listening on port", LISTEN_PORT)

    frames = {}  # store partial frames
    print("Press 'q' in the video window to exit.")

    while True:
        packet, addr = sock.recvfrom(BUFFER_SIZE)
        frame_id, pkt_id, total = struct.unpack(HEADER_STRUCT, packet[:8])
        payload = packet[8:]

        if frame_id not in frames:
            frames[frame_id] = [None] * total
        frames[frame_id][pkt_id] = payload

    # If full frame received
        if all(p is not None for p in frames[frame_id]):
            data = b"".join(frames[frame_id])
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is not None:
                cv2.imshow("UDP Stream", frame)

    # clean up old frame
            del frames[frame_id]

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    sock.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
