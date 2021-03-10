Computer networks project implementing a UDP-based ping client that communicates
with the provided ping server. The functionality emulates ICMP echo requests and
replies (which are performed over raw IP sockets - see RFC 792) via UDP messages.
At a high level, the ping client sends byte-encoded ping request messages (which
include a calculated checksum) to the ping server the given "count" times.
The ping server responds with an echo reply which is received, decoded, and
verified by the client. Informational messages are printed during the message
exchange as well as relevant statistics. Additionally, my implementation 
spawns multiple threads to more efficiently send and receive the ping
messages.

To run:

1) Open project directory in terminal

2) The ping server can be run with command: ```java -jar pingserver.jar --port=<port> [--loss_rate=<rate>] [--bit_error_rate=<rate>] [--avg_delay=<delay>]```
    - loss_rate, bit_error_rate, and avg_delay are optional parameters to
    simulate packet loss, bit errors and average transmission delay if 
      server is run locally

3) Run ping client via command: ```python3 ping_client.py <server_ip> 
       <server_port> <count> <period> <timeout>```
       
    Example: ```python3 ping_client.py 128.135.164.173 8025 15 3000 4000```
   - In order to function, client should correctly point to server ip and port 
   - Note that period and timeout are in milliseconds
   
