# Internet Dungeon Server

import socket
import threading
import queue
import math
import random

import pygame

import common
from clientserver import dict_xy
import gemstones
import effects
import monsters
import fireball
import dungeontiles
import message

# This ListenerThread creates a SocketThread per Internet Game Client.
# It listens on the public game Port for new Internet Game CLients.
# The created SocketThread exists only while the Internet Game Client
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
            # Allocate and start a new Thread to communicate with
            # the new Internet Game Client.
            GameServerSocketThread(clientAddress, socket).start()

GameSocketListenerThread().start()


# This queue is used for THREAD-SAFE, one-way communication.
# ALL SocketThreads send requests to the GameServer on this shared Queue,
# but all SocketThreads use their own private queue to recieve the reponse.
shared_request_queue = queue.Queue()


# One SocketThread is created each time a Game client connects
class GameServerSocketThread(threading.Thread):

    def __init__(self, clientAddress, clientsocket):
        threading.Thread.__init__(self)
        self.client_socket = clientsocket
        self.clientAddress = clientAddress

        # This queue is used for THREAD-SAFE, one-way communication
        # from the GameServer back to this thread only.
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

def bump_sprite(sprite, angle, power):
    dx = math.cos(angle) * power
    dy = math.sin(angle) * power
    sprite.scroll_position(dx, dy)


g1 = gemstones.shared.add("GemGreen", dict_xy((100, 100)))
g2 = gemstones.shared.add("GemRed", dict_xy((200, 100)))
m1 = monsters.shared.add("GreenZombie", dict_xy((300, 300)))
m1.set_player(g1)
m2 = monsters.shared.add("GreenZombie", dict_xy((400, 400)))
m2.set_player(g2)
dungeontiles.shared.add("FireballTower", dict_xy((500, 500)))

monster_retarget_trigger = common.frames_per_second / 2
monster_retarget_counter = 0

logins = {}  # Stores usernames for Client Sockets

# This is the main thread.
# Inside the while loop the code never waits for anything,
# Instead it always tries to loop at the required frames_per_second
print("Game Running:")
game_on = True
while game_on:
    # Process all available requests from the GameServerSocketThread queue.
    while shared_request_queue.empty() is not True:
        try:
            # DON'T WAIT on queue, always move on even if the queue is empty
            socket_thread, request = shared_request_queue.get_nowait()
        except(queue.Empty):
            socket_thread = None
            request = None

        if request is not None:
            response = None

            for line in request.splitlines(False):
                data = message.decode_dictionary(line)
                if "request" in data:
                    request_type = data["request"]
                    if request_type == "login":
                        username = data["username"]
                        print("logging in user [{}]".format(username))
                        response = "response:login,username:{}\n".format(
                            username)
                        logins[socket_thread] = username
                    elif request_type == "update":
                        # TODO - add other sprite modules
                        response = gemstones.shared.encode_update()
                        response += effects.shared.encode_update()
                        response += monsters.shared.encode_update()
                        response += fireball.shared.encode_update()
                        response += dungeontiles.shared.encode_update()
                    elif request_type == "bump-monster":
                        sprite_id = int(data["id"])
                        monster = monsters.shared.get(sprite_id)
                        if monster is not None:
                            print("Bumping monster: " + str(monster))
                            angle = random.random() * 2 * math.pi
                            bump_sprite(monster, angle, 10)
                        response = "response:bumped\n"
                    elif request_type == "add-gem":
                        x = int(data["x"])
                        y = int(data["y"])
                        gemtype = data["gemtype"]
                        sprite = gemstones.shared.add(gemtype, dict_xy((x, y)))
                        response = "response:added\n".format(x, y)
                        username = logins[socket_thread]
                        print("[{}] Added gem at {},{}".format(username, x, y))
                    elif request_type == "add-fireball":
                        sprite = fireball.shared.add("FireballRed", data)
                        response = "response:added fireball\n"
                        username = logins[socket_thread]
                        print("[{}] Added fireball".format(username))
                    elif request_type == "delete-gem":
                        sprite_id = int(data["id"])
                        if gemstones.shared.remove(sprite_id):
                            username = logins[socket_thread]
                            print("[{}] deleted id {}".format(
                                username, sprite_id))
                            response = "response:deleted\n"
                        else:
                            response = "response:already_deleted\n"

            if response is None:
                response = "response:unknown-request"  # Default response

                if socket_thread in logins:
                    username = logins[socket_thread]
                    print("Request error from user: [{}]".format(username))
                print(request)
                print(response)

            socket_thread.private_response_queue.put(response)

    # Game logic goes below here...
    gemstones.shared.update_server()
    effects.shared.update_server()
    monsters.shared.update_server()
    fireball.shared.update_server()
    dungeontiles.shared.update_server()

    # Periodically, each monster targets the nearest gem
    monster_retarget_counter += 1
    if monster_retarget_counter >= monster_retarget_trigger:
        monster_retarget_counter = 0
        for monster in monsters.shared.spritegroup:
            if len(gemstones.shared.spritegroup) == 0:
                monster.set_player(None)
                monster.stop()
            else:
                closest_gem = None
                closest_dist2 = None  # Note: compare the distance-squared
                for gem in gemstones.shared.spritegroup:
                    dx = gem.rect.center[0] - monster.rect.center[0]
                    dy = gem.rect.center[1] - monster.rect.center[1]
                    curr_dist2 = dx * dx + dy * dy
                    if closest_dist2 is None or curr_dist2 < closest_dist2:
                        closest_dist2 = curr_dist2
                        closest_gem = gem
            if closest_gem is not None:
                monster.set_player(closest_gem)

    # Gem and monster collisions
    colls = pygame.sprite.groupcollide(gemstones.shared.spritegroup,
                                       monsters.shared.spritegroup,
                                       True, False,
                                       collided=pygame.sprite.collide_circle)
    for sprite in colls:
        data = dict_xy(sprite.rect.center)
        new_effect = effects.shared.add("Vanish", data)

    # Fireball and monster collisions
    colls = pygame.sprite.groupcollide(fireball.shared.spritegroup,
                                       monsters.shared.spritegroup,
                                       False, False,
                                       collided=pygame.sprite.collide_circle)
    for fb in colls:
        fb.done = True
        # Damage each monster
        for monster in colls[fb]:
            monster.hit(5)
            bump_sprite(monster, fb.angle, 10)

    # Remove dead monsters
    for monster in monsters.shared.spritegroup:
        if monster.dead is True:
            monster.kill()

    # Explode completed fireballs
    for fb in fireball.shared.spritegroup:
        if fb.done is True:
            data = dict_xy(fb.get_position())
            effects.shared.add("ExplosionRed", data)
            fb.kill()

    common.clock.tick(common.frames_per_second)