# Internet Dungeon Server

import socket
import threading
import queue

# import pygame
import gemstones

import common

# This queue is used for THREAD-SAFE, one-way communication
# All SocketThreads send requests to the GameServer on this Queue
request_queue = queue.Queue()  # SocketThread -> GameServerThread

# One SocketThread is created each time a Game client connects
class GameServerSocketThread(threading.Thread):

    def __init__(self, clientAddress, clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        self.clientAddress = clientAddress

        # This queue is used for THREAD-SAFE, one-way communication
        # from the GameServer to this thread
        self.response_queue = queue.Queue()  # SocketThread <- GameServerThread
        print("New socket connection from: {}".format(clientAddress))

    def run(self):
        while True:
            # WAIT for requests from the Client socket...
            data = self.csocket.recv(2048)
            request = data.decode()

            # Put the request on the game queue
            request_queue.put([self, request])

            # WAIT for the response ...
            response = self.response_queue.get()

            self.csocket.send(bytes(response, 'UTF-8'))

        print("Client at ", self.clientAddress, " disconnected...")


# This ListenerThread creates a SocketThread for each client

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('', common.server_port))

class GameSocketListenerThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        print("Socket Server started:")
        print("Waiting for clients on port {}...".format(common.server_port))
        while True:
            server.listen(1)
            socket, clientAddress = server.accept()
            new_client_thread = GameServerSocketThread(clientAddress, socket)
            new_client_thread.start()

GameSocketListenerThread().start()

# Game Server

def sprite_response(sprite_type):
    response = "reponsetype:spriteupdate,type:{}\n".format(sprite_type)
    template = "id:{},x:{},y:{}\n"
    for sprite in gemstones.spritegroup:
        sprite_id = sprite.sprite_id
        curr_sprite_type = sprite.typename
        if curr_sprite_type == sprite_type:
            x, y = sprite.get_position()
            response += template.format(sprite_id, x, y)
    return response


gemstones.add_gem("gemstones.GemGreen", [100, 100])

logins = {}  # Stores usernames for Client Sockets

print("Game Running:")
game_on = True
while game_on:
    # Process Client requests
    try:
        # Don't wait on queue, just get any available request
        socket_thread, request = request_queue.get_nowait()
    except(queue.Empty):
        socket_thread = None
        request = None

    if request is not None:
        # FIXME: multiline requests don't work
        username = logins.get(socket_thread, "UNKNOWN")
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
            response = "LOGIN success:1,dummy:0\n".format(username)
            logins[socket_thread] = username

        update_request = key_dict.get("UPDATE")
        if update_request is not None:
            # TODO - handle different sprite types
            # TODO - move response code into gemstones module
            response = sprite_response("gemstones.GemGreen")

        delete_request = key_dict.get("DELETE")
        if delete_request is not None:
            sprite_id = int(delete_request["id"])
            if gemstones.remove_gem(sprite_id):
                response = "DELETED id:{}\n".format(sprite_id)
            else:
                response = "NONE id:{}\n".format(sprite_id)

        click_request = key_dict.get("CLICK")
        if click_request is not None:
            # sprite_id = int(click_request["id"])
            # sprite_type = click_request["type"]
            x = int(click_request["x"])
            y = int(click_request["y"])
            sprite = gemstones.add_gem("gemstones.GemGreen", [x, y])

            if sprite is not None:
                response = "ADDED x:{},y:{}\n".format(x, y)
                print("[{}] Added gem at {},{}".format(username, x, y))

        socket_thread.response_queue.put(response)

    common.clock.tick(common.frames_per_second)