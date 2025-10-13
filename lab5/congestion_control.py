import matplotlib.pyplot as plt

def simulate_tcp():
    """
    Simulates TCP congestion control behavior including Slow Start,
    Congestion Avoidance, and reaction to packet loss.
    """
    # --- Simulation Parameters ---
    max_rounds = 50
    initial_ssthresh = 16
    packet_loss_rounds = {17, 34}

    #State Variables 
    cwnd = 1  
    ssthresh = initial_ssthresh 
    
    # History for Plotting
    cwnd_history = []
    rounds_history = []

    print("--- Starting TCP Congestion Control Simulation ---")
    print(f"Initial ssthresh: {ssthresh}\n")

    #  Main Simulation Loop 
    for r in range(1, max_rounds + 1):
        # Record the current cwnd for this round
        rounds_history.append(r)
        cwnd_history.append(cwnd)
        
        phase = "Slow Start" if cwnd < ssthresh else "Congestion Avoidance"
        print(f"Round: {r:2} | Phase: {phase:22} | cwnd: {cwnd:3} | ssthresh: {ssthresh:3}", end="")

        # --- Event Handling: Check for Packet Loss or Successful ACK ---
        if r in packet_loss_rounds:
            # 1. Multiplicative Decrease on packet loss (timeout)
            print(" -> PACKET LOSS!")
            ssthresh = cwnd // 2  # Update ssthresh
            cwnd = 1              # Reset cwnd to 1 MSS
        else:
            # 2. Increase cwnd on successful ACK
            print(" -> ACK Received")
            if cwnd < ssthresh:
                # In Slow Start, cwnd doubles (exponential growth)
                cwnd *= 2
            else:
                # In Congestion Avoidance, cwnd increases by 1 (linear growth)
                cwnd += 1

    # --- Plotting the Results ---
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))

    ax.plot(rounds_history, cwnd_history, marker='o', linestyle='-', label='cwnd Growth')
    
    # Mark the packet loss events
    for loss_round in packet_loss_rounds:
        loss_cwnd = cwnd_history[loss_round - 1]
        ax.plot(loss_round, loss_cwnd, 'rx', markersize=12, label=f'Packet Loss at Round {loss_round}')

    ax.set_title('TCP Congestion Control Simulation', fontsize=16)
    ax.set_xlabel('Transmission Round', fontsize=12)
    ax.set_ylabel('Congestion Window Size (cwnd) in MSS', fontsize=12)
    ax.legend()
    ax.set_xticks(range(0, max_rounds + 1, 5))
    ax.set_yticks(range(0, max(cwnd_history) + 5, 5))
    
    # Save the plot to a file
    plt.savefig('cwnd_plot.png')
    print("\n--- Simulation Complete ---")
    print("Plot saved as cwnd_plot.png")

    # Display the plot
    plt.show()


if __name__ == '__main__':
    simulate_tcp()