# Socket client

import socket

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
        try:
            sent = sock.sendto(message_bytes, server_address)

            data, server = sock.recvfrom(4096)
            message = data.decode('utf8')
            print('response "%s"' % message)

        finally:
            # print('closing socket')
            sock.close()