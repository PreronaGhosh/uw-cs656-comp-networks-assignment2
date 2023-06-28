class Packet:
    MAX_DATA_LENGTH = 500
    SEQ_NUM_MODULO = 32

    def __init__(self, ptype, seq_num, length, data):
        if len(data) > self.MAX_DATA_LENGTH:
            print("Data is too large, max data should be 500")

        self.ptype = ptype
        self.seq_num = seq_num % self.SEQ_NUM_MODULO
        self.length = length
        self.data = data

    @staticmethod
    def create_packet(seq_num, length, data):
        return Packet(1, seq_num, length, data)

    @staticmethod
    def create_ack(seq_num):
        return Packet(0, seq_num, 0, "")

    @staticmethod
    def create_eot(seq_num):
        return Packet(2, seq_num, 0, "")

    @staticmethod
    def create_syn():
        return Packet(3, 0, 0, "")

    def send_data_as_bytes(self):
        obj = bytearray()
        obj.extend(self.ptype.to_bytes(length=4, byteorder="big"))
        obj.extend(self.seq_num.to_bytes(length=4, byteorder="big"))
        obj.extend(self.length.to_bytes(length=4, byteorder="big"))
        obj.extend(self.data.encode())
        return obj

    @staticmethod
    def parse_bytes_data(udp_data):
        ptype = int.from_bytes(udp_data[0:4], byteorder="big")
        seq_num = int.from_bytes(udp_data[4:8], byteorder="big")
        length = int.from_bytes(udp_data[8:12], byteorder="big")

        if ptype == 1:
            data = udp_data[12:12+length].decode()
            return ptype, seq_num, length, data

        elif ptype == 0 or ptype == 2 or ptype == 3:
            return ptype, seq_num, 0, ""
