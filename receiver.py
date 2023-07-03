import socket
import sys
from packet import Packet

# Global variables
SEQ_MODULO = 32

def log_arrival(seqnum):
    with open("arrival.log", "a") as file:
        file.write(f"{seqnum}\n")

def accept_send_syn(receiver_udp_socket, emulator_addr, emu_recv_port):
    conn_flag = False

    message = receiver_udp_socket.recvfrom(2048)[0]
    ptype, seq_num, length, data = Packet(message).decode()

    if ptype == 3:
        # Received a SYN packet, so send back a SYN packet
        log_arrival('SYN')
        syn_packet = Packet(3, 0, 0, "")
        receiver_udp_socket.sendto(syn_packet.encode(), (emulator_addr, emu_recv_port))
        conn_flag = True

    return conn_flag

def log_seq(seqnum):
    with open("arrival.log", "a") as file:
        file.write(f"{seqnum}\n")


def receive_data(receiver_udp_socket, filename, emulator_addr, emu_recv_port):
    exp_seqnum = 0
    buffer = {}  # key: seqnum, value: packet data

    while True:
        packet = receiver_udp_socket.recvfrom(2048)[0]
        ptype, seqnum, length, data = Packet(packet).decode()

        if ptype == 3:  # Received a SYN packet for re-request from sender after initial SYN packet from receiver got lost
            conn_state = accept_send_syn(receiver_udp_socket, emulator_addr, emu_recv_port)
            if conn_state:
                continue

        log_seq(seqnum)

        if seqnum == exp_seqnum:  # handle valid packet
            if ptype == 1:  # data packet
                with open(filename, "a") as f:
                    f.write(data)
                    exp_seqnum = (exp_seqnum+1) % SEQ_MODULO

                    # Check buffer for the following packets
                    while exp_seqnum in buffer:
                        f.write(buffer[exp_seqnum])
                        buffer.pop(exp_seqnum)
                        exp_seqnum = (exp_seqnum+1) % SEQ_MODULO

                # send ACK for the last packet that we wrote into the output file
                ack_packet = Packet(0, (exp_seqnum - 1) % SEQ_MODULO, 0, "")
                receiver_udp_socket.sendto(ack_packet.encode(), (emulator_addr, emu_recv_port))

            elif ptype == 2:  # EOT packet received
                # Send EOT packet back to sender and close connection
                eot_packet = Packet(2, exp_seqnum, 0, "")
                receiver_udp_socket.sendto(eot_packet.encode(), (emulator_addr, emu_recv_port))
                print("EOT Received. Closing connection with sender")
                receiver_udp_socket.close()
                break

        else:  # handle out-of-order packets
            # buffer window size is max of N
            if len(buffer) <= 10:
                # check if received seqnum is within the next 10 seqnums, then buffer it
                if seqnum > exp_seqnum and seqnum <= (exp_seqnum - 10) % SEQ_MODULO:
                    buffer[seqnum] = data

                if seqnum - 1 in buffer:
                    buffer.pop(seqnum-1)

            # ACK the most recently received valid data packet
            ack_packet = Packet(0, (exp_seqnum - 1) % SEQ_MODULO, 0, "")
            receiver_udp_socket.sendto(ack_packet.encode(), (emulator_addr, emu_recv_port))


def main():

    # Reset log files
    f = open("arrival.log", "w")
    f.close()

    # Parse command line inputs
    if len(sys.argv) != 5:
        print("Incorrect number of arguments provided")
        exit(1)
    else:
        emulator_addr = sys.argv[1]
        emu_recv_port = int(sys.argv[2])
        receiver_port = int(sys.argv[3])
        filename = sys.argv[4]

    # Reset output file that will contain data received
    f = open(filename, "w")
    f.close()

    # Stage 1 - Connection establishment with sender
    receiver_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver_udp_socket.bind(('', receiver_port))

    conn_state = accept_send_syn(receiver_udp_socket, emulator_addr, emu_recv_port)

    if conn_state:
        # Next stage - Data transmission and termination stage
        receive_data(receiver_udp_socket, filename, emulator_addr, emu_recv_port)


if __name__ == '__main__':
    main()