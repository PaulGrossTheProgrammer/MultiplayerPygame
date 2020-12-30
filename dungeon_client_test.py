# Pygame Internet Client

import socket

from common import server_port

class MessageClientThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        print("MessageClientThread Created:")

    def run(self):
        print("MessageClientThread Started:")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER, server_port))
        client.sendall(bytes(username, 'UTF-8'))
        while True:
            in_data = client.recv(1024)
            print("From Server :", in_data.decode())
            out_data = input("> ")
            client.sendall(bytes(out_data, 'UTF-8'))
            if out_data == 'bye':
                break

        client.close()

SERVER = input("Enter server address: ")
if SERVER == "":
    SERVER = "localhost"
print("Connecting to {}".format(SERVER))

username = input("Your name: ")

