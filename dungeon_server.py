# Internet Message Server

import socket
import threading
import time

server_port = 56789

class MessageServerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        print("MessageServer Created:")

    def run(self):
        print("MessageServer Started:")
        while True:
            # print("Message loop ...")
            time.sleep(1)

messagethread = MessageServerThread()
messagethread.start()

class ClientThread(threading.Thread):

    def __init__(self, clientAddress, clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        print("New connection added: ", clientAddress)

    def run(self):
        print("Connection from : ", clientAddress)
        # self.csocket.send(bytes("Hi, This is from Server..",'utf-8'))
        msg = ''
        username = None
        while True:
            data = self.csocket.recv(2048)
            msg = data.decode()
            if msg == 'bye':
                break

            key_dict = {}
            # FIXME: line in msg doesn't work
            line = msg
            # Split the key from the values at the first space
            space_index = line.find(" ")
            key = line[0:space_index]
            values = line[space_index + 1:]
            value_pairs = values.split(",")
            values_dict = {}
            for pair in value_pairs:
                pair_list = pair.split(":")
                values_dict[pair_list[0]] = pair_list[1]

            key_dict[key] = values_dict

            response = "NONE"

            login_request = key_dict.get("LOGIN")
            if login_request is not None:
                username = login_request["username"]
                print("logging in user [{}]".format(username))
                response = "Logged in [{}]".format(username)

            update_request = key_dict.get("UPDATE")
            if update_request is not None:
                x, y = get_gem_pos()
                response = "UPDATE x:{},y:{}".format(x, y)

            click_request = key_dict.get("CLICK")
            if click_request is not None:
                x = click_request["x"]
                y = click_request["y"]
                update_gem_pos(x, y)
                response = "CLICKED {},{}".format(x, y)

            self.csocket.send(bytes(response, 'UTF-8'))
        print("Client at ", clientAddress, " disconnected...")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('', server_port))

gem_x = 100
gem_y = 100

def update_gem_pos(x, y):
    global gem_x, gem_y

    gem_x = x
    gem_y = y

def get_gem_pos():
    global gem_x, gem_y

    return [gem_x, gem_y]


print("Internet Server started")
print("Waiting for Internet client requests ...")
while True:
    server.listen(2)
    client_sock, clientAddress = server.accept()
    new_client_thread = ClientThread(clientAddress, client_sock)
    new_client_thread.start()