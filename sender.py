import socket
import sys
from datetime import datetime
import time
import math
from packet import Packet

# Global variables
TIMEOUT = 0
MAX_DATA_SIZE = 500
SEQ_MODULO = 32

N = 1  # initial window size
timer = None
num_unacked_packets = 0
next_seqnum = 0


def file_to_packets(filename):
    file = open(filename, 'rb')
    data = file.read()
    packets_all = []  # list of all packets created from the data

    num_of_packets = math.ceil(len(data) / MAX_DATA_SIZE) + 1  # Add 1 for EOT packet
    print(num_of_packets, flush=True)

    # Add content of text file as data to every packet
    for i in range(num_of_packets - 1):
        start_index = i * MAX_DATA_SIZE
        end_index = min((i + 1) * MAX_DATA_SIZE, len(data))
        packet_data = data[start_index:end_index]
        packets_all.append(Packet(1, (i % SEQ_MODULO), len(packet_data), packet_data.decode()))

    # Add an EOT packet
    packets_all.append(Packet(2, (num_of_packets-1) % SEQ_MODULO, 0, ""))
    print(len(packets_all), flush=True)

    return packets_all, num_of_packets


def write_log_files(log_type, seqnum, t):
    if log_type == 'seqnum':
        with open("seqnum.log", "a") as file:
            file.write(f"t={t} {seqnum}\n")

    if log_type == 'N':
        with open("N.log", "a") as file:
            file.write(f"t={t} {seqnum}\n")

    if log_type == 'ack':
        with open("ack.log", "a") as file:
            file.write(f"t={t} {seqnum}\n")


def start_connection(sender_udp_sock, emulator_addr, emulator_rcv_port):
    print("inside start_connection()", flush=True)
    conn_flag = False
    sender_udp_sock.settimeout(3)

    while True:
        print("here2", flush=True)
        packet = Packet(3, 0, 0, "")
        sender_udp_sock.sendto(packet.encode(), (emulator_addr, emulator_rcv_port))
        write_log_files('seqnum', 'SYN', -1)
        time.sleep(3)

        try:
            print("here3", flush=True)
            message = sender_udp_sock.recvfrom(2048)[0]
            print(message)
            ptype, seq_num, length, data = Packet(message).decode()
            print(seq_num)
            if ptype == 3:
                conn_flag = True
                break

        except socket.timeout:
            continue

        except BlockingIOError:
            pass

    return conn_flag


def reset_files():
    f1 = open("N.log", "w")
    f2 = open("seqnum.log", "w")
    f3 = open("ack.log", "w")
    f1.close()
    f2.close()
    f3.close()


def is_between(a,b,c):
    if a < b:
        if a <= c and c < b:
            return True
        else:
            return False
    else:
        if b < c and c <= a:
            return False
        else:
            return True


def send_receive_packets(packets_all, num_of_packets, sender_udp_sock, emulator_addr, emulator_rcv_port):
    global timer, num_unacked_packets, next_seqnum, N

    timestamp = 0
    write_log_files('N', N, 0)

    print("Ready to send packets", flush=True)
    curr_packet = 0  # holds position of the packet in packets_all list

    while True:
        if curr_packet == num_of_packets - 1:  # EOT packet
            if num_unacked_packets == 0:
                print("Data completely transferred. Sending EOT to close connection.")

                while True:
                    sender_udp_sock.sendto(packets_all[num_of_packets-1].encode(), (emulator_addr, emulator_rcv_port))
                    timestamp += 1
                    write_log_files('seqnum', 'EOT', timestamp)
                    time.sleep(3)

                    try:
                        rcvd_eot_packet = sender_udp_sock.recvfrom(2048)[0]
                        ptype, eot_seqnum, length, data = Packet(rcvd_eot_packet).decode()

                        if ptype == 2:
                            timestamp += 1
                            write_log_files('ack', 'EOT', timestamp)
                            sender_udp_sock.close()
                            break
                        else:
                            continue

                    except BlockingIOError:
                        continue
                print("Received EOT, closing connection", flush=True)
                break

        elif num_unacked_packets < N:

            if num_unacked_packets == 0:
                timer = datetime.now()   # first packet of a new window

            print("num_unacked_packets: ", num_unacked_packets, flush=True)
            sender_udp_sock.sendto(packets_all[curr_packet].encode(), (emulator_addr, emulator_rcv_port))

            timestamp += 1
            write_log_files('seqnum', curr_packet % SEQ_MODULO, timestamp)

            curr_packet += 1
            num_unacked_packets += 1
            next_seqnum = curr_packet % SEQ_MODULO

        # if timeout has occurred
        if timer and (datetime.now() - timer).microseconds > TIMEOUT * 1000:
            print("Timeout has occurred", flush=True)
            N = 1

            timestamp += 1
            write_log_files('N', N, timestamp)

            # retransmit the packet that caused retransmission
            sender_udp_sock.sendto(packets_all[curr_packet - num_unacked_packets].encode(), (emulator_addr, emulator_rcv_port))
            print("retrans pack pos is:", curr_packet - num_unacked_packets, flush=True)
            timer = datetime.now()

        # Check if ACK packet has been received - non blocking code
        rcvd_ack_packet = None
        timestamp += 1

        try:
            rcvd_ack_packet = sender_udp_sock.recvfrom(2048)[0]
        except BlockingIOError:
            pass

        if rcvd_ack_packet is None:
            continue

        ptype, ack_seqnum, length, data = Packet(rcvd_ack_packet).decode()

        if ptype == 0:  # ACK received
            write_log_files('ack', ack_seqnum, timestamp)

            # check if it's a new ACK
            if is_between(ack_seqnum % SEQ_MODULO, (next_seqnum - num_unacked_packets) % SEQ_MODULO, next_seqnum % SEQ_MODULO):
                num_acked_packets = 1 + ack_seqnum - (next_seqnum - num_unacked_packets) % 32  # count num packets we can consider ACKed now

                if num_acked_packets <= num_unacked_packets:
                    num_unacked_packets -= num_acked_packets  # update spare room in window
                    print("num of unacked packets:", num_unacked_packets, flush=True)

                if N == 10:  # window size capped at 10
                    N = 10
                else:
                    N += 1
                    write_log_files('N', N, timestamp)

                if num_unacked_packets > 0:
                    print("Timer reset as num_unacked > 0", flush=True)
                    timer = datetime.now()
                elif num_unacked_packets < 0 and curr_packet <= num_of_packets -1:
                    print("Timer stopped", flush=True)
                    timer = None

    # timestamp += 1
    # sender_udp_sock.settimeout(None)
    # rcvd_eot_packet = sender_udp_sock.recvfrom(2048)[0]
    # ptype, eot_seqnum, length, data = Packet(rcvd_eot_packet).decode()
    # if ptype == 2:
    #     write_log_files('ack', 'EOT', timestamp)
    #     sender_udp_sock.close()


def main():
    global TIMEOUT

    # Reset log files
    reset_files()

    # Check if input format is correct or not
    if len(sys.argv) != 6:
        print("Incorrect number of arguments provided")
        exit(1)
    else:
        emulator_addr = sys.argv[1]
        emulator_rcv_port = int(sys.argv[2])
        sender_rcv_port = int(sys.argv[3])
        TIMEOUT = int(sys.argv[4])  # milliseconds
        filename = sys.argv[5]

    print(f"Timeout: {TIMEOUT}")
    # Stage 1 - Connection establishment - Send a SYN packet to receiver
    sender_udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender_udp_sock.bind(('', sender_rcv_port))

    conn_state = start_connection(sender_udp_sock, emulator_addr, emulator_rcv_port)

    if conn_state:
        print("Connection established")
        # Stage 2 - data transfer
        # Convert file to packets
        packets_all, num_of_packets = file_to_packets(filename)
        print("Created all packets", flush=True)

        sender_udp_sock.settimeout(0)

        send_receive_packets(packets_all, num_of_packets, sender_udp_sock, emulator_addr, emulator_rcv_port)

    else:
        print("No connection established with receiver")


if __name__ == '__main__':
    main()