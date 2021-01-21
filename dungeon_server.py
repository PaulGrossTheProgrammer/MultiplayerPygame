# Internet Dungeon Server

import socket
import threading
import queue

import gemstones
import message
import common

# This ListenerThread creates a SocketThread per Internet Game Client.
# It listens on the public game Port for new Internet Game CLients.
# The created SocketThread exists while the Internet Game Client
# needs to play the game, and is closed when the player leaves.
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('', common.server_port))

class GameSocketListenerThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        print("Internet Socket Server started:")
        print("Waiting for clients on port {}...".format(common.server_port))
        while True:
            server.listen(1)
            socket, clientAddress = server.accept()
            # Allocate and start new Thread to communicate with
            # the new Internet Game Client.
            GameServerSocketThread(clientAddress, socket).start()

GameSocketListenerThread().start()


# This queue is used for THREAD-SAFE, one-way communication
# ALL SocketThreads send requests to the GameServer on this shared Queue,
# but all SocketThreads use their own private queue to recieve the reponse
shared_request_queue = queue.Queue()


# One SocketThread is created each time a Game client connects
class GameServerSocketThread(threading.Thread):

    def __init__(self, clientAddress, clientsocket):
        threading.Thread.__init__(self)
        self.client_socket = clientsocket
        self.clientAddress = clientAddress

        # This queue is used for THREAD-SAFE, one-way communication
        # from the GameServer back to this thread only
        self.private_response_queue = queue.Queue()
        print("New socket connection from: {}".format(clientAddress))

    def run(self):
        while True:
            # WAIT for requests from the Client socket...
            request = self.client_socket.recv(2048).decode()

            # Put the request on the game queue
            shared_request_queue.put([self, request])

            # WAIT for the response ...
            response = self.private_response_queue.get()

            self.client_socket.send(bytes(response, 'UTF-8'))

        print("Client at ", self.clientAddress, " disconnected...")


# Game Server

gemstones.add_gem("GemGreen", [100, 100])
gemstones.add_gem("GemRed", [200, 100])

logins = {}  # Stores usernames for Client Sockets

# This is the main thread.
# Inside the while loop the code never waits for anything,
# Instead it always tries to loop at the required frames_per_second
print("Game Running:")
game_on = True
while game_on:
    # Process any available requests from the GameServerSocketThread queue
    try:
        # DON'T WAIT on queue, always move on even if the queue is empty
        socket_thread, request = shared_request_queue.get_nowait()
    except(queue.Empty):
        socket_thread = None
        request = None

    if request is not None:
        response = "response:none"  # Default response

        for line in request.splitlines(False):
            data = message.decode_dictionary(line)
            if "request" in data:
                request_type = data["request"]
                if request_type == "login":
                    username = data["username"]
                    print("logging in user [{}]".format(username))
                    response = "response:login,username:{}\n".format(username)
                    logins[socket_thread] = username
                elif request_type == "update":
                    # TODO - add other sprite modules
                    response = gemstones.encode_update()
                elif request_type == "add":
                    x = int(data["x"])
                    y = int(data["y"])
                    sprite = gemstones.add_gem("GemGreen", [x, y])
                    response = "response:added\n".format(x, y)
                    username = logins[socket_thread]
                    print("[{}] Added gem at {},{}".format(username, x, y))
                elif request_type == "delete":
                    sprite_id = int(data["id"])
                    if gemstones.remove_gem(sprite_id):
                        username = logins[socket_thread]
                        print("[{}] deleted id {}".format(username, sprite_id))
                        response = "response:deleted\n"
                    else:
                        response = "response:already_deleted\n"

        socket_thread.private_response_queue.put(response)

    # Game logic goes below here...

    common.clock.tick(common.frames_per_second)