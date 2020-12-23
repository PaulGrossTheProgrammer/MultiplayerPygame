# Socket server


import socket
port = 56789

server_address = ('', port)

name = input("Enter owner: ")

print('starting up on {}'.format(server_address))
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(server_address)

while True:
    print(name + ' is waiting to receive message on port ' + str(port))
    data, address = sock.recvfrom(4096)
    print('Received {} bytes from {}'.format(len(data), address))

    if data:
        message = data.decode('utf8')
        print(message)
        print("echoing...")
        echo_message = name + " is ECHOING: " + message
        echo_bytes = bytes(echo_message, 'utf8')
        sent = sock.sendto(echo_bytes, address)