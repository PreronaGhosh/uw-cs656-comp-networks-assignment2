import sys
import math
import time
from packet import Packet
import socket

# Global Variables
MAX_DATA_SIZE = Packet.MAX_DATA_LENGTH
MAX_WINDOW_SIZE = 10

curr_seq_num = 0
next_seq_num = 0
timer = 0
timeout_state = False


# Global variables for logs
log_seq_num = []
log_ack = []

def file_to_packets(filename):
    file = open(filename, 'r')
    data = file.read()
    packets_all = []

    num_of_packets = math.ceil(len(data) / MAX_DATA_SIZE) + 1  # Add 1 for EOT packet

    # Add content of text file as data to every packet
    for i in range(num_of_packets - 1):
        start_index = i * MAX_DATA_SIZE
        end_index = min((i + 1) * MAX_DATA_SIZE, len(data))
        packet_data = data[start_index:end_index]
        packets_all.append(Packet.create_packet(i, len(packet_data), str(packet_data)))

    # Add an EOT packet
    packets_all.append(Packet.create_eot(num_of_packets - 1))

    return packets_all, num_of_packets


def start_connection(sender_udp_sock, emulator_addr, emulator_rcv_port):
    syn_packet = Packet.create_syn()
    conn_flag = False

    while True:
        sender_udp_sock.sendto(syn_packet.send_data_as_bytes(), (emulator_addr, emulator_rcv_port))
        time.sleep(3)

        message = sender_udp_sock.recvfrom(1024)[0]
        ptype, seq_num, length, data = Packet.parse_bytes_data(message)
        if ptype == 3:
            conn_flag = True
            break

    return conn_flag


def send_packets_to_receiver(packets_all, sender_udp_sock, emulator_addr, emulator_rcv_port):
    n = 1  # initial window size

    if n <= MAX_WINDOW_SIZE:





def main():

    # Check if input format is correct or not
    if len(sys.argv) != 6:
        print("Incorrect number of arguments provided")
        exit(1)
    else:
        emulator_addr = sys.argv[1]
        emulator_rcv_port = int(sys.argv[2])
        sender_rcv_port = int(sys.argv[3])
        timeout = int(sys.argv[4])  # in milliseconds
        filename = sys.argv[5]

    # Stage 1 - Connection establishment - Send a SYN packet to receiver
    sender_udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender_udp_sock.bind(('', sender_rcv_port))

    conn_state = start_connection(sender_udp_sock, emulator_addr, emulator_rcv_port)

    if conn_state:
        # Stage 2 - data transfer
        # Convert file to packets
        packets_all, num_of_packets = file_to_packets(filename)


    else:
        print("No connection established with receiver")



if __name__ == '__main__':
    main()