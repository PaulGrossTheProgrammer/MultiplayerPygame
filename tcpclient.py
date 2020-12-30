# TCP Client to webserver

import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2.5)

server_address = ('www.httpbin.org', 80)

sock.connect(server_address)

request_header = 'GET /ip HTTP/1.0\r\nHost: www.httpbin.org\r\n\r\n'
sock.send(bytes(request_header, 'utf8'))

response = ''
while True:
    recv = sock.recv(1024)
    if not recv:
        break
    response += recv.decode('utf8')

print(response)
sock.close()