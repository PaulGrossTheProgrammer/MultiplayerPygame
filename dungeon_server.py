# Internet Message Server

import socket
import threading
import time

server_port = 56789

# Each queue is used for THREAD-SAFE one-way communication
request_queue = []  # Append from SocketThread, pop at GameServerThread
response_queue = []  # Append from GameServerThread, pop at SocketThread

# One of these Threads is created per Game client for socket comms
class GameServerSocketThread(threading.Thread):

    def __init__(self, clientAddress, clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        print("New connection added: ", clientAddress)

    def run(self):
        thread_id = threading.get_ident()
        print("Connection from : ", clientAddress)
        while True:
            data = self.csocket.recv(2048)
            request = data.decode()

            # Put the request on the game queue
            request_queue.append([thread_id, request])

            # Wait for the response
            # FIXME - use a lock wait() to avoid busy waiting
            response = None
            while response is None:
                while len(response_queue) == 0:
                    time.sleep(0.001)

                # Search the queue and remove only this user's response
                # FIXME - use an sequencial index to remove
                for curr_id, curr_response in response_queue:
                    if curr_id == thread_id:
                        response = curr_response
                        response_queue.remove([curr_id, curr_response])
                        break

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

socketuser_dict = {}

class GameServerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        print("Game Server Started:")
        while True:
            # Process Client requests
            if len(request_queue) > 0:
                # FIXME: multiline requests don't work
                thread_id, request = request_queue.pop(0)
                username = socketuser_dict.get(thread_id, "UNKNOWN")
                if request.startswith("UPDATE") is False:
                    print("Game Server Request from user [{}]: {}".format(
                          username, request))

                line = request

                key_dict = {}
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

                response = "OK"  # Default response

                login_request = key_dict.get("LOGIN")
                if login_request is not None:
                    username = login_request["username"]
                    print("logging in user [{}]".format(username))
                    response = "LOGIN success:1,dummy:0".format(username)
                    socketuser_dict[thread_id] = username

                update_request = key_dict.get("UPDATE")
                if update_request is not None:
                    x, y = get_gem_pos()
                    response = "UPDATE x:{},y:{}".format(x, y)

                click_request = key_dict.get("CLICK")
                if click_request is not None:
                    x = click_request["x"]
                    y = click_request["y"]
                    update_gem_pos(x, y)
                    response = "UPDATE x:{},y:{}".format(x, y)
                    print("[{}] moved gem to {},{}".format(username, x, y))

                response_queue.append([thread_id, response])

            # FIXME - use fps. Maybe pygame clock.tick()?
            time.sleep(0.034)

messagethread = GameServerThread()
messagethread.start()

print("Socket Server started")
print("Waiting for Game client to log in from the Internet ...")
while True:
    server.listen(2)
    client_sock, clientAddress = server.accept()
    new_client_thread = GameServerSocketThread(clientAddress, client_sock)
    new_client_thread.start()