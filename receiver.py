import sys
import socket
from packet import Packet


def accept_send_syn(receiver_udp_socket, emulator_addr, emu_recv_port):
    conn_flag = False

    message = receiver_udp_socket.recvfrom(4096)[0]
    ptype, seq_num, length, data = Packet.parse_bytes_data(message)

    if ptype == 3:
        # Received a SYN packet, so send back a SYN packet
        syn_packet = Packet.create_syn()
        receiver_udp_socket.sendto(syn_packet.send_data_as_bytes(), (emulator_addr, emu_recv_port))
        conn_flag = True

    return conn_flag

def main():
    # Parse command line inputs
    if len(sys.argv) != 5:
        print("Incorrect number of arguments provided")
        exit(1)
    else:
        emulator_addr = sys.argv[1]
        emu_recv_port = int(sys.argv[2])
        receiver_port = int(sys.argv[3])
        filename = sys.argv[4]

    # Stage 1 - Connection establishment with sender
    receiver_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver_udp_socket.bind(('', receiver_port))

    conn_state = accept_send_syn(receiver_udp_socket, emulator_addr, emu_recv_port)

    if conn_state:
        # Stage 2 - Data transmission stage

    else:
        print("No connection established with sender")


if __name__ == '__main__':
    main()