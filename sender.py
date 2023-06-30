import sys
import math
import time
import threading
from packet import Packet
import socket

# Global Variables
MAX_DATA_SIZE = Packet.MAX_DATA_LENGTH  # 500
SEQ_MODULO = Packet.SEQ_NUM_MODULO  # 32
MAX_WINDOW_SIZE = 10
N = 1  # initial window size
MAX_SEQ_NUM = 31
TIMEOUT = 0  # initial value (in seconds)

last_unacked_seqnum = 0
next_seq_num = 0
last_acked_seq_num = 0
eot_state = False
start_time = 0

lock = threading.Lock()  # lock for critical sections

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
    global eot_state

    syn_packet = Packet.create_syn()
    conn_flag = False

    while True:
        sender_udp_sock.sendto(syn_packet.send_data_as_bytes(), (emulator_addr, emulator_rcv_port))
        time.sleep(3)

        try:
            message = sender_udp_sock.recvfrom(2048)[0]
            ptype, seq_num, length, data = Packet.parse_bytes_data(message)

            if ptype == 3:
                conn_flag = True
                eot_state = True
                break

        except BlockingIOError:
            pass

    return conn_flag


def send_packets_to_receiver(packets_all, num_of_packets, sender_udp_sock, emulator_addr, emulator_rcv_port):
    global start_time, last_unacked_seqnum, next_seq_num, N

    # start checking for ACKs in a separate thread #
    receive_ack_thread = threading.Thread(target=receive_ack, args=(sender_udp_sock,))
    receive_ack_thread.start()

    lock.acquire()
    start_time = time.time()
    lock.release()

    local_n = 0  # local loop counter to control the number of packets sent in a window is equal to N
    np = 0  # local variable to check if all packets are sent

    lock.acquire()
    local_last_ack = last_acked_seq_num
    lock.release()

    while not eot_state:  # connection between sender and receiver has not been terminated with EOT yet
        if time.time() - start_time < TIMEOUT:
            if N <= MAX_WINDOW_SIZE:
                while local_n < N and np < num_of_packets:  # window is full when this condition fails or all packets have been sent
                    sender_udp_sock.sendto(packets_all[next_seq_num].send_data_as_bytes(), (emulator_addr, emulator_rcv_port))
                    np += 1
                    last_unacked_seqnum = next_seq_num
                    next_seq_num += 1
                    local_n += 1

                lock.acquire()
                if local_last_ack < last_acked_seq_num:  # checks if window has space to transmit
                    local_n = local_n - (last_acked_seq_num - local_last_ack)
                lock.release()

                if next_seq_num == SEQ_MODULO:
                    next_seq_num = 0

                if np == num_of_packets:  # all packets have been sent
                    # check if all ACKs have been received or not
                    # if yes, move to connection termination stage
                    # todo


        else:  # timeout has occurred
            # resend un-ACKed packet only and reset timer
            sender_udp_sock.sendto(packets_all[last_unacked_seqnum].send_data_as_bytes(), (emulator_addr, emulator_rcv_port))
            lock.acquire()
            start_time = time.time()
            lock.release()


def receive_ack(sender_udp_sock):
    global eot_state, last_acked_seq_num, start_time, N

    while not eot_state:  # connection between sender and rcvr has not been terminated with EOT yet
        message = sender_udp_sock.recvfrom(2048)[0]
        ptype, seq_num, length, data = Packet.parse_bytes_data(message)

        if ptype == 2:  # EOT packet received
            lock.acquire()
            eot_state = True  # this variable value is used in send packet function
            lock.release()
            break

        elif ptype == 0:  # ACK packet received
            if seq_num > last_acked_seq_num:  # new ACK packet
                last_acked_seq_num = seq_num

                lock.acquire()
                N = 10 if N == 10 else N + 1  # window size capped at 10
                lock.release()

                if last_acked_seq_num < last_unacked_seqnum:  # there are some previously transmitted but unacked packets
                    lock.acquire()
                    start_time = time.time()
                    lock.release()

                elif last_acked_seq_num == last_unacked_seqnum:  # no outstanding packets
                    lock.acquire()
                    start_time = 0
                    lock.release()

            elif seq_num < last_acked_seq_num: # ACK for some previous out-of-order packet received

            elif seq_num == last_acked_seq_num:  # duplicate ACK









def main():
    global TIMEOUT

    # Check if input format is correct or not
    if len(sys.argv) != 6:
        print("Incorrect number of arguments provided")
        exit(1)
    else:
        emulator_addr = sys.argv[1]
        emulator_rcv_port = int(sys.argv[2])
        sender_rcv_port = int(sys.argv[3])
        TIMEOUT = float(sys.argv[4]) * 0.001  # input in milliseconds, convert to seconds
        filename = sys.argv[5]

    # Stage 1 - Connection establishment - Send a SYN packet to receiver
    sender_udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender_udp_sock.bind(('', sender_rcv_port))

    conn_state = start_connection(sender_udp_sock, emulator_addr, emulator_rcv_port)

    if conn_state:
        # Stage 2 - data transfer
        # Convert file to packets
        packets_all, num_of_packets = file_to_packets(filename)
        send_packets_to_receiver(packets_all, num_of_packets, sender_udp_sock, emulator_addr, emulator_rcv_port)

    else:
        print("No connection established with receiver")


if __name__ == '__main__':
    main()