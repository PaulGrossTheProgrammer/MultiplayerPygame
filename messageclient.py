import socket

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
# server_address = ('localhost', 5678)
# server_address = ('192.168.61.104', 5678)
server_address = ('192.168.61.1', 5678)

print('connecting to {}'.format(server_address))
sock.connect(server_address)

try:

    # Send data
    message = 'This is the message.  It will be repeated.'
    print('sending "{}"'.format(message))
    message_bytes = bytes(message, 'utf8')

    sock.sendall(message_bytes)

    # Look for the response
    amount_received = 0
    amount_expected = len(message)

    while amount_received < amount_expected:
        data = sock.recv(16)
        amount_received += len(data)
        print('received "{}"'.format(data))

finally:
    print('closing socket')
    sock.close()