# Socket client

import socket

from datetime import datetime

port = 56789

server_ip = input("Enter Server IP: ")

server_address = (server_ip, port)

inSession = True
while inSession:
    message = input("Enter message: ")
    if len(message) == 0:
        inSession = False
    else:
        message_bytes = bytes(message, 'utf8')

        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.5)
        try:
            start_time = datetime.now()
            sent = sock.sendto(message_bytes, server_address)
            print("Client socket: {}". format(sock.getsockname()))

            data, server = sock.recvfrom(4096)
            trip_ms = (datetime.now().microsecond -
                       start_time.microsecond)/1000

            message = data.decode('utf8')
            print('response {} in {} ms'.format(message, trip_ms))

        finally:
            sock.close()