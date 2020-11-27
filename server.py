# Socket server

import socket

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
# server_address = ('localhost', 56789)
# server_address = ('192.168.61.104', 56789)
server_address = ('', 56789)

print('starting up on %s port %s' % server_address)
sock.bind(server_address)

while True:
    print('\nwaiting to receive message')
    data, address = sock.recvfrom(4096)

    print('received %s bytes from %s' % (len(data), address))
    # print(data)

    if data:
        message = data.decode('utf8')
        echo_message = "ECHO: " + message
        echo_bytes = bytes(echo_message, 'utf8')
        sent = sock.sendto(echo_bytes, address)
        # print('sent %s bytes back to %s' % (sent, address))
        print(message)
        print("echoing...")