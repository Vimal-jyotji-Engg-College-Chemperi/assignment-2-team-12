import threading
import queue
import time
import random

# ----------------------------
# Take User Input
# ----------------------------
while True:
    try:
        NUM_PROCESSES = int(input("Enter number of processes: "))
        if NUM_PROCESSES < 2:
            print("Please enter at least 2 processes.")
            continue
        break
    except ValueError:
        print("Invalid input! Please enter a valid integer.")

# ----------------------------
# Shared Distributed File (Simulated)
# ----------------------------
distributed_file = []
file_lock = threading.Lock()  # Only for printing safely


# ----------------------------
# Message Structure
# ----------------------------
class Message:
    def __init__(self, msg_type, timestamp, sender):
        self.msg_type = msg_type
        self.timestamp = timestamp
        self.sender = sender


# ----------------------------
# Process Class
# ----------------------------
class Process(threading.Thread):
    def __init__(self, pid, processes):
        super().__init__()
        self.pid = pid
        self.clock = 0
        self.request_queue = []
        self.reply_count = 0
        self.processes = processes
        self.inbox = queue.Queue()
        self.requesting_cs = False

    # Lamport Clock Update Rule
    def update_clock(self, received_timestamp=None):
        if received_timestamp is None:
            self.clock += 1
        else:
            self.clock = max(self.clock, received_timestamp) + 1

    # Broadcast message
    def broadcast(self, msg_type):
        self.update_clock()
        msg = Message(msg_type, self.clock, self.pid)
        for p in self.processes:
            if p.pid != self.pid:
                p.inbox.put(msg)

    # Handle incoming messages
    def handle_message(self, msg):
        self.update_clock(msg.timestamp)

        if msg.msg_type == "REQUEST":
            self.request_queue.append((msg.timestamp, msg.sender))
            self.request_queue.sort()

            reply = Message("REPLY", self.clock, self.pid)
            self.processes[msg.sender].inbox.put(reply)

        elif msg.msg_type == "REPLY":
            self.reply_count += 1

        elif msg.msg_type == "RELEASE":
            self.request_queue = [
                req for req in self.request_queue if req[1] != msg.sender
            ]

    # Request Critical Section
    def request_cs(self):
        self.requesting_cs = True
        self.update_clock()
        self.request_timestamp = self.clock

        print(f"Process {self.pid} requesting CS at time {self.clock}")

        self.request_queue.append((self.request_timestamp, self.pid))
        self.request_queue.sort()

        self.reply_count = 0
        self.broadcast("REQUEST")

        while not self.can_enter_cs():
            self.process_incoming()

        self.enter_cs()

    def can_enter_cs(self):
        return (
            self.reply_count == NUM_PROCESSES - 1
            and self.request_queue[0][1] == self.pid
        )

    # Enter Critical Section
    def enter_cs(self):
        print(f"Process {self.pid} ENTERING CS at time {self.clock}")
        self.write_to_file()
        time.sleep(random.uniform(1, 2))
        self.release_cs()

    # Simulated File Write
    def write_to_file(self):
        with file_lock:
            entry = f"Written by Process {self.pid} at time {self.clock}"
            distributed_file.append(entry)
            print(f"FILE UPDATE: {entry}")

    # Release CS
    def release_cs(self):
        self.update_clock()
        print(f"Process {self.pid} RELEASING CS at time {self.clock}")

        self.request_queue.pop(0)
        self.broadcast("RELEASE")
        self.requesting_cs = False

    # Process incoming messages
    def process_incoming(self):
        while not self.inbox.empty():
            msg = self.inbox.get()
            self.handle_message(msg)
        time.sleep(0.1)

    # Thread execution
    def run(self):
        time.sleep(random.uniform(0.5, 2))
        self.request_cs()


# ----------------------------
# Create Processes
# ----------------------------
processes = []
for i in range(NUM_PROCESSES):
    processes.append(Process(i, []))

for p in processes:
    p.processes = processes

# Start Processes
for p in processes:
    p.start()

# Wait for Completion
for p in processes:
    p.join()

# Final File Output
print("\nFinal Distributed File Content:")
for line in distributed_file:
    print(line)
