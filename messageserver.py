import socket

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
# server_address = ('localhost', 5678)
# server_address = ('192.168.61.104', 5678)
server_address = ('', 5678)

print('starting up on %s port {}'.format(server_address))
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection
    print('waiting for a connection...')
    connection, client_address = sock.accept()

    try:
        print('connection from {}'.format(client_address))

        # Receive the data in small chunks and retransmit it
        while True:
            data = connection.recv(16)
            print('received {}'.format(data))
            if data:
                print('sending data back to the client')
                connection.sendall(data)
            else:
                print('no more data from {}'.format(client_address))
                break

    finally:
        connection.close()