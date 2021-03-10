import sys
import socket
import time
import threading
import os
import random


class PingClient:
    """Class encapsulating ping client functionality"""

    def __init__(self, server_ip, server_port, count, period, timeout):
        self.server_ip = server_ip
        self.server_port = int(server_port)
        self.count = int(count)
        self.period = int(period) / 1000  # milliseconds
        self.timeout = int(timeout) / 1000  # milliseconds
        self.total_start = 0
        self.total_end = 0
        self.request_count = 0
        self.reply_count = 0
        self.rtt_list = []
        self.thread_list = []

    def build_message(self, seq_num):
        """Build a binary message according to project's ICMP message format:
        type - 1 byte,
        code - 1 byte,
        checksum - 2 bytes,
        identifier - 2 bytes,
        seqno - 2 bytes,
        timestamp - 6 bytes.

        Inputs: integer (seq_num)
        Outputs: binary object (new_packet)
        """

        # construct message items
        msg_type = 8  # 8 for echo request per ICMP message format
        identifier = (os.getpid() % 65536).to_bytes(2, byteorder='big')
        checksum = (0).to_bytes(2, byteorder='big')
        seq_num = seq_num.to_bytes(2, byteorder='big')
        timestamp = int(time.time() * 1000).to_bytes(6, byteorder='big')

        # construct initial message with checksum set to 0
        msg = bytearray()
        msg.insert(0, msg_type)
        msg.insert(1, 0)
        msg.extend(checksum)
        msg.extend(identifier)
        msg.extend(seq_num)
        msg.extend(timestamp)

        # calculate checksum with initial message
        checksum = self.calculate_checksum(msg)
        checksum = self.bit_flip(checksum).to_bytes(2, byteorder='big')

        # create final message inserting checksum calculated
        final_msg = bytearray()
        final_msg.insert(0, msg_type)
        final_msg.insert(1, 0)
        final_msg.extend(checksum)
        final_msg.extend(identifier)
        final_msg.extend(seq_num)
        final_msg.extend(timestamp)

        return final_msg

    def calculate_checksum(self, message):
        """Calculates one's complement sum of given message.
        Inputs: bytes object (message)
        Outputs: integer
        **Note: Referenced stack overflow for implementation of this calculation**
        Source: https://stackoverflow.com/questions/3949726/calculate-ip-checksum-
        in-python
        """
        s = 0
        for i in range(0, len(message)-1, 2):
            w = (message[i]) + (message[i + 1] << 8) << 8
            s = ((w + s) & 0xffff) + ((w + s) >> 16)
        return s

    def bit_flip(self, checksum):
        """Flips checksum bits.
        Inputs: integer (checksum)
        Outputs: integer
        """
        return 0xffff - checksum

    def summary_statistics(self):
        """Method which captures the summary statistics for a series of pings
        sent to the server and outputs string to be printed.
        No inputs.
        Outputs: string
        """
        display_str = f'--- {self.server_ip} ping statistics ---\n'

        transmitted = str(self.request_count)
        received = str(self.reply_count)
        loss = str(round((1 - self.reply_count / self.request_count) * 100))
        total_time = str(round(self.total_end - self.total_start))

        display_str += f'{transmitted} transmitted, {received} received, ' \
                       f'{loss}% loss, time {total_time} ms\n'
        if self.reply_count:
            rtt_min = str(min(self.rtt_list))
            rtt_avg = str(round(sum(self.rtt_list) / len(self.rtt_list)))
            rtt_max = str(max(self.rtt_list))
            display_str += f'rtt min/avg/max = {rtt_min}/{rtt_avg}/{rtt_max} '\
                           f'ms'
        else:
            display_str += 'rtt min/avg/max = 0/0/0 ms'

        return display_str

    def send_ping(self, seq_num):
        """Main method of ping client. Sends ping request to client and
        captures ping reply from server. Prints details relating to current
        message request/reply.
        Inputs: integer (seq_num)
        No Outputs.
        """
        # Create a client socket, bind to random port, and set timeout of sock
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        rand_port = random.randint(1024, 65535)
        host = socket.gethostbyname(socket.gethostname())
        client_sock.bind((host, rand_port))
        client_sock.settimeout(self.timeout)

        # If first request, print relevant message
        if seq_num == 1:
            print(f'PING {self.server_ip}')
        # Try - send ping request to server
        try:
            # build request message
            request_msg = self.build_message(seq_num)

            # Mark start time for calculating request message rtt (ms)
            start_time = time.time() * 1000
            # Send echo request message to server and receive any reply
            client_sock.sendto(request_msg, (self.server_ip, self.server_port))
            data, address = client_sock.recvfrom(2048)
            # Mark end time for calculating rtt (ms)
            end_time = time.time() * 1000

            # Add rtt to list of rtts
            rtt = int(end_time - start_time)
            self.rtt_list.append(rtt)
            # Increment request count since transmitted another message
            self.request_count += 1

            # Calculate checksum from server
            server_checksum = self.calculate_checksum(data)
            # Grab sequence number from reply message
            server_seq_num = int.from_bytes(data[6:8], byteorder='big')

            # If checksum from server reply is invalid, print error message
            # (invalid if sum of headers not = 65535 (all 1's in binary))
            if server_checksum != 65535:
                print(f'WARNING: checksum verification failure for echo reply '
                      f'seqno={str(server_seq_num)}')
            # Otherwise print PONG
            else:
                print(f'PONG {self.server_ip}: seq={str(server_seq_num)} '
                      f'time={rtt} ms')
                # Successfully received a reply
                self.reply_count += 1
            client_sock.close()

        # If have timeout exception, count as dropped
        except socket.timeout:
            self.request_count += 1
            client_sock.close()

    def run(self):
        """"""
        # Mark start time for total transmission of ping requests
        self.total_start = time.time() * 1000

        # Initiate sequence number
        seq_num = 1

        # Spawn and start first thread (send immediately before waiting period
        # time)
        thread = threading.Thread(target=self.send_ping, args=[seq_num])
        thread.start()
        # Add thread to list of threads
        self.thread_list.append(thread)

        seq_num += 1

        # Loop through remaining count and create threading timer objects with
        # interval of period given. Add to thread list and increment sequence
        # number every time
        for i in range(self.count - 1):
            thread = threading.Timer(interval=self.period,
                                     function=self.send_ping, args=[seq_num])
            thread.start()
            self.thread_list.append(thread)
            seq_num += 1

        # Join threads once all have been started
        if len(self.thread_list) == self.count:
            for thread in self.thread_list:
                thread.join()

        # Once finished, print out summary statistics
        self.total_end = time.time() * 1000
        print(self.summary_statistics())


if __name__ == "__main__":
    # Capture command line args
    server_ip = sys.argv[1]
    server_port = sys.argv[2]
    count = sys.argv[3]
    period = sys.argv[4]
    timeout = sys.argv[5]

    # Instantiate and run ping client based on parameters given
    ping_client = PingClient(server_ip, server_port, count, period, timeout)
    ping_client.run()
