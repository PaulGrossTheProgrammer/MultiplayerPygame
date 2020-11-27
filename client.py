# Socket client

import socket

# server_address = ('localhost', 10000)
# server_address = ('192.168.61.104', 56789)
server_address = ('192.168.61.1', 56789)

# message = 'This is the message.  It will be repeated.'
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

            # Send data
            # print('sending "%s"' % message)
            sent = sock.sendto(message_bytes, server_address)

            # Receive response
            print('waiting for server response...')
            data, server = sock.recvfrom(4096)
            message = data.decode('utf8')
            print('response "%s"' % message)

        finally:
            # print('closing socket')
            sock.close()