import random
import time

def go_back_n(tf, n, p):
    """
    Simulates the Go-Back-N protocol with individual acknowledgments.
    
    tf: Total number of frames to send.
    n: Window size.
    p: Probability of frame loss.
    """
    b = 0  # Window base
    s = 0  # Next sequence number to send

    print(f"Total frames: {tf}, Window Size: {n}, Loss Probability: {p}\n")

    while b < tf:
        print(f"Current Window: [{b}, {min(b + n - 1, tf - 1)}]")

        # --- Sender sends all frames in the window ---
        frames_to_send = range(s, min(b + n, tf))
        for i in frames_to_send:
            print(f"  Sending Frame {i}...")
            s += 1
            time.sleep(0.5)

        # --- Simulate receiver's response for each frame sent ---
        acked_successfully = True
        for i in range(b, s):
            time.sleep(0.5)
            # Check if this frame or its ACK is lost
            if random.random() < p:
                print(f" Frame {i} or its ACK lost. Timeout!")
                print(f"-> GOING BACK TO {b}. Retransmitting window.\n")
                s = b  # Go-Back-N: Reset sender to the last confirmed base
                acked_successfully = False
                break
            else:
                # Successfully received ACK for frame i
                print(f" ACK {i + 1} received.")
        
        if acked_successfully:
            # If all frames in the batch were acked, slide the window base
            b = s
            print("-> Window slides successfully.\n")

    print("All frames transmitted successfully.")


if __name__ == '__main__':
    total_frames = 8
    window_size = 3
    loss_prob = 0.20 # Lower probability to see successful sliding
    
    go_back_n(total_frames, window_size, loss_prob)