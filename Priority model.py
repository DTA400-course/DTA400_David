import simpy
import random
import numpy as np
import time

# Simulation constants
VOICE_ARRIVAL_RATE = 10  # packets per second (lambda) for voice 0.1 time units     | 0.1 / sek avarage
VOICE_SERVICE_RATE = 50  # packets per second (mu) for voice 0.02 time units        | 0.02 / sek avarage
                                                                                    
VIDEO_ARRIVAL_RATE = 15  # packets per second (lambda) for video 0.06 time units    | 0.06 / sek avarage
VIDEO_SERVICE_RATE = 30  # packets per second (mu) for video 0.03                   | 0.03 / sek avarage

DATA_ARRIVAL_RATE = 5    # packets per second (lambda) for data 0.2 time units      | 0.2 / sek  avarage
DATA_SERVICE_RATE = 20   # packets per second (mu) for data 0.05 time units         | 0.05/ sek avarage

QUEUE_CAPACITY = 40     # shared buffer size
SIM_TIME = 3600        # total simulation time

class PriorityQueue:
    def __init__(self, env, queue_capacity):
        self.env = env
        self.server = simpy.PriorityResource(env, capacity=1)
        self.queue_capacity = queue_capacity

        # Metrics
        self.latencies_voice, self.latencies_video, self.latencies_data = [], [], []
        self.packet_losses_voice, self.packet_losses_video, self.packet_losses_data = 0, 0, 0
        self.total_packets_voice, self.total_packets_video, self.total_packets_data = 0, 0, 0

        # Start processes for each traffic type
        self.env.process(self.packet_arrival("Voice", VOICE_ARRIVAL_RATE, VOICE_SERVICE_RATE, priority=1))
        self.env.process(self.packet_arrival("Video", VIDEO_ARRIVAL_RATE, VIDEO_SERVICE_RATE, priority=2))
        self.env.process(self.packet_arrival("Data", DATA_ARRIVAL_RATE, DATA_SERVICE_RATE, priority=3))

    def packet_arrival(self, packet_type, arrival_rate, service_rate, priority):
        """Handle packet arrivals for different traffic types."""
        while True:
            inter_arrival_time = random.expovariate(arrival_rate)
            yield self.env.timeout(inter_arrival_time)

            # Track total packets per type
            if packet_type == "Voice":
                self.total_packets_voice += 1
            elif packet_type == "Video":
                self.total_packets_video += 1
            else:
                self.total_packets_data += 1

            current_queue_length = self.server.count + len(self.server.queue)
            #print(f"[{self.env.now:.2f} s] {packet_type} Packet arrived with priority {priority}. Queue length: {current_queue_length}")

            if current_queue_length >= self.queue_capacity:
                # Drop packet if queue is full
                if packet_type == "Voice":
                    self.packet_losses_voice += 1
                elif packet_type == "Video":
                    self.packet_losses_video += 1
                else:
                    self.packet_losses_data += 1

               # print(f"[{self.env.now:.2f} s] {packet_type} Packet dropped! Queue full (Length: {current_queue_length}).")
            else:
               # print(f"[{self.env.now:.2f} s] {packet_type} Packet enqueued for service with priority {priority}.")
                self.env.process(self.packet_service(packet_type, service_rate, priority))

    def packet_service(self, packet_type, service_rate, priority):
        """Service each packet in the server."""
        arrival_time = self.env.now
        with self.server.request(priority=priority, preempt=True) as request:
            yield request
           # print(f"[{self.env.now:.2f} s] {packet_type} Packet started service with priority {priority}.")

            # Service the packet
            service_time = random.expovariate(service_rate)
            yield self.env.timeout(service_time)
            latency = self.env.now - arrival_time

            if packet_type == "Voice":
                self.latencies_voice.append(latency)
            elif packet_type == "Video":
                self.latencies_video.append(latency)
            else:
                self.latencies_data.append(latency)

            #print(f"[{self.env.now:.2f} s] {packet_type} Packet completed service. Latency: {latency:.2f} s")

def results(queue):
    # Calculate and display latency, jitter, and packet loss for each type
    traffic_types = {
        "Voice": (queue.latencies_voice, queue.packet_losses_voice, queue.total_packets_voice),
        "Video": (queue.latencies_video, queue.packet_losses_video, queue.total_packets_video),
        "Data": (queue.latencies_data, queue.packet_losses_data, queue.total_packets_data),
    }

    for traffic, (latencies, packet_losses, total_packets) in traffic_types.items():
        avg_latency = np.mean(latencies)

        deviations = [abs(latency - avg_latency) for latency in latencies]
        jitter = np.mean(deviations)
        loss_rate = (packet_losses / total_packets) * 100

        print(f"{traffic} Traffic (M/M/1/K):")
        print(f"  Total packets: {total_packets}")
        print(f"  Packets lost: {packet_losses}")
        print(f"  Average Latency: {avg_latency:.2f} s")
        print(f"  Jitter: {jitter:.2f} s")
        print(f"  Packet Loss Rate: {loss_rate:.2f}%")
        print("-" * 40)

def run_simulation():
    env = simpy.Environment()
    queue = PriorityQueue(env, QUEUE_CAPACITY)

    time.sleep(1),print("--- Simulation Start ---")
    time.sleep(1),print(f"Queue Capacity: {QUEUE_CAPACITY} packets")
    time.sleep(1),print(f"Simulation Time: {SIM_TIME} seconds\n")
    time.sleep(2)

    env.run(until=SIM_TIME)
    print(), print("--- Simulation Results (priority) ---")
    results(queue)

# Run the simulation
run_simulation()
