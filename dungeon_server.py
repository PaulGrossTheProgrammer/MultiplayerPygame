# Internet Dungeon Server

import socket
import threading
import queue
import math
import random

import pygame

import common
import soundeffects
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


gemstones.shared.add("GemGreen").set_position((100, 100))
gemstones.shared.add("GemRed").set_position((200, 100))

dungeontiles.shared.add("FireballTower").set_position((50, 50))
dungeontiles.shared.add("FireballTower").set_position((750, 50))
dungeontiles.shared.add("FireballTower").set_position((50, 550))
dungeontiles.shared.add("FireballTower").set_position((750, 550))

monster_retarget_trigger = common.frames_per_second / 2
monster_retarget_counter = 0

logins = {}  # Stores usernames for Client Sockets

# This is the main thread.
# Inside the while loop the code never waits for anything,
# Instead it always tries to loop at the required frames_per_second
print("Game Running:")
game_on = True
while game_on:
    #
    # REQUEST-RESPONSE HANDLING:
    #
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
                        response = gemstones.shared.encode_update()
                        response += effects.shared.encode_update()
                        response += monsters.shared.encode_update()
                        response += fireball.shared.encode_update()
                        response += dungeontiles.shared.encode_update()

                        response += soundeffects.encode_effects(socket_thread)
                    elif request_type == "bump-monster":
                        sprite_id = int(data["id"])
                        monster = monsters.shared.get(sprite_id)
                        if monster is not None:
                            print("Bumping monster: " + str(monster))
                            angle = random.random() * 2 * math.pi
                            bump_sprite(monster, angle, 10)
                            monster.hit(1)
                            effects.shared.add("BloodHit").set_position(
                                monster.rect.center)
                        response = "response:bumped\n"
                    elif request_type == "add-gem":
                        x = int(data["x"])
                        y = int(data["y"])
                        gemtype = data["gemtype"]
                        sprite = gemstones.shared.add(gemtype)
                        sprite.set_position((x, y))
                        response = "response:added-gem\n".format(x, y)
                        username = logins[socket_thread]
                        print("[{}] Added gem at {},{}".format(username, x, y))
                    elif request_type == "add-fireball":
                        sprite = fireball.shared.add("FireballRed", data)
                        response = "response:added-fireball\n"
                        username = logins[socket_thread]
                        print("[{}] Added fireball".format(username))
                    elif request_type == "delete-gem":
                        sprite_id = int(data["id"])
                        if gemstones.shared.remove(sprite_id):
                            username = logins[socket_thread]
                            print("[{}] deleted id {}".format(
                                username, sprite_id))
                            response = "response:deleted-gem\n"
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

    #
    # GAME LOGIC:
    #
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
            if len(gemstones.shared.spritegroup) == 0:  # No gems
                monster.set_player(None)
                monster.stop()
            else:  # Target nearest gem
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
    coll_gem_monster = pygame.sprite.groupcollide(
        gemstones.shared.spritegroup, monsters.shared.spritegroup,
        True, False, collided=pygame.sprite.collide_circle)
    for sprite in coll_gem_monster:
        effects.shared.add("Vanish").set_position(sprite.rect.center)

    # Fireball and monster collisions
    coll_fb_monster = pygame.sprite.groupcollide(
        fireball.shared.spritegroup,
        monsters.shared.spritegroup, False, False,
        collided=pygame.sprite.collide_circle)
    for fb in coll_fb_monster:
        fb.done = True
        # Damage each monster
        for monster in coll_fb_monster[fb]:
            monster.hit(5)
            if monster.dead is not True:
                bump_sprite(monster, fb.angle, 20)
                effects.shared.add("BloodHit").set_position(
                    monster.rect.center)

    # Remove dead monsters
    for monster in monsters.shared.spritegroup:
        if monster.dead is True:
            monster.kill()
            effects.shared.add("BloodKill").set_position(monster.rect.center)

    # Explode completed fireballs
    for fb in fireball.shared.spritegroup:
        if fb.done is True:
            effects.shared.add("ExplosionRed").set_position(fb.rect.center)
            fb.kill()
            soundeffects.add_shared("explosion")

    # Replace dead monsters
    if len(monsters.shared.spritegroup) < 2:
        rand_x = random.randrange(150, common.SCREEN_WIDTH - 150)
        rand_y = random.randrange(150, common.SCREEN_HEIGHT - 150)
        pos = (rand_x, rand_y)

        typename = monsters.shared.random_typename()
        m = monsters.shared.add(typename)
        m.set_position(pos)
        effects.shared.add("SparkleYellow").set_position(pos)

    soundeffects.remove_expired()

    common.clock.tick(common.frames_per_second)