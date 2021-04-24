# Dungeon Internet Server

import socket
import threading
import queue
import math
import random

import pygame

import common
from common import calc_distance, calc_angle
import soundeffects
import gemstones
import effects
import monsters
import fireball
import dungeontiles
import clientserver

# This ListenerThread creates a SocketThread per Internet Game Client.
# It listens on the public game Port for new Internet Game CLients.
# The created SocketThread exists only while the Internet Game Client
# needs to play the game, and is closed when the player leaves.
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', common.server_port))

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

class GameSocketListenerThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        print("Internet Socket Server started on: [{}]".format(hostname))
        print("LOCAL IP address = {}".format(local_ip))
        print("Waiting for clients on port {}...".format(common.server_port))
        while True:
            server.listen(1)
            socket, clientAddress = server.accept()
            # Allocate and start a new Thread to communicate with
            # the new Internet Game Client.
            GameServerSocketThread(clientAddress, socket).start()

GameSocketListenerThread().start()

socket_logins = {}  # Stores usernames for Client Sockets

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
        socket_active = True
        try:
            while socket_active:
                # WAIT for requests from the Client socket...
                request = self.client_socket.recv(2048).decode()

                # Put the request on the game queue
                shared_request_queue.put((self, request))

                # WAIT for the response ...
                response = self.private_response_queue.get()

                if response.startswith("response:socket-terminated"):
                    socket_active = False

                self.client_socket.send(bytes(response, 'UTF-8'))

        except Exception:
            # Remove this thread from the socket login dictionary
            socket_logins.pop(self)

        print("Client at ", self.clientAddress, " disconnected...")

#
# Game Server
#

def bump_sprite(sprite, angle, power):
    dx = math.cos(angle) * power
    dy = math.sin(angle) * power
    sprite.scroll_position(dx, dy)


dungeontiles.shared.add("FireballTower").set_position((50, 50))
dungeontiles.shared.add("FireballTower").set_position((750, 50))
dungeontiles.shared.add("FireballTower").set_position((50, 550))
dungeontiles.shared.add("FireballTower").set_position((750, 550))

monster_retarget_trigger = common.frames_per_second / 2
monster_retarget_counter = 0

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
                data = clientserver.decode_dictionary(line)
                if "request" in data:
                    request_type = data["request"]
                    if request_type == "login":
                        username = data["username"]
                        print("logging in user [{}]".format(username))
                        response = "response:login,username:{}\n".format(
                            username)
                        socket_logins[socket_thread] = username
                    elif request_type == "logout":
                        username = socket_logins[socket_thread]
                        print("[{}] logged out".format(username))
                        socket_logins.pop(socket_thread)
                        response = "response:socket-terminated\n"
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
                            soundeffects.add_shared("painhit")
                        response = "response:bumped\n"
                    elif request_type == "gem-drag":
                        sprite_id = int(data["id"])
                        angle = float(data["angle"])
                        gem = gemstones.shared.get(sprite_id)
                        if gem is not None:
                            print("Draging gem: " + str(gem))
                            bump_sprite(gem, angle, 40)
                        response = "response:draggedgem\n"
                    elif request_type == "add-gem":
                        x = int(data["x"])
                        y = int(data["y"])
                        gemtype = data["gemtype"]
                        sprite = gemstones.shared.add(gemtype)
                        sprite.set_position((x, y))
                        response = "response:added-gem\n".format(x, y)
                        username = socket_logins[socket_thread]
                        print("[{}] Added gem at {},{}".format(username, x, y))
                    elif request_type == "add-fireball":
                        sprite = fireball.shared.add("FireballRed", data)
                        soundeffects.add_shared("fireball")
                        response = "response:added-fireball\n"
                        username = socket_logins[socket_thread]
                        print("[{}] Added fireball".format(username))
                    elif request_type == "delete-gem":
                        sprite_id = int(data["id"])
                        if gemstones.shared.remove(sprite_id):
                            username = socket_logins[socket_thread]
                            print("[{}] deleted id {}".format(
                                username, sprite_id))
                            response = "response:deleted-gem\n"
                        else:
                            response = "response:already_deleted\n"

            if response is None:
                response = "response:unknown-request"  # Default response

                if socket_thread in socket_logins:
                    username = socket_logins[socket_thread]
                    print("Request error from user: [{}]".format(username))
                print("[{}]".format(request))
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
                monster.set_target(None)
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
                    monster.set_target(closest_gem)

    # Gem and monster collisions
    coll_gem_monster = pygame.sprite.groupcollide(
        gemstones.shared.spritegroup, monsters.shared.spritegroup,
        True, False, collided=pygame.sprite.collide_circle)
    for gem in coll_gem_monster:
        effects.shared.add("Vanish").set_position(gem.rect.center)
        sound = soundeffects.random_pickup()
        soundeffects.add_shared(sound)

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

    # Explode completed fireballs
    for fb in fireball.shared.spritegroup:
        if fb.done is True:
            effects.shared.add("ExplosionRed").set_position(fb.rect.center)
            fb.kill()
            soundeffects.add_shared("explosion")

            # Damage nearby monsters
            # Look for monsters within explosion range
            expl_range = 200
            for monster in monsters.shared.spritegroup:
                fb_center = fb.rect.center
                m_center = monster.rect.center
                m_distance = calc_distance(fb_center, m_center)
                if m_distance <= expl_range:
                    monster.hit(1)
                    if monster.dead is not True:
                        angle = calc_angle(fb_center, m_center)
                        bump_sprite(monster, angle, 20)

                        soundeffects.add_shared("painhit")
                        effects.shared.add("BloodHit").set_position(
                            monster.rect.center)

    # Remove dead monsters
    for monster in monsters.shared.spritegroup:
        if monster.dead is True:
            monster.kill()
            effects.shared.add("BloodKill").set_position(monster.rect.center)
            soundeffects.add_shared("monsterkill")

    # Replace dead monsters
    if len(monsters.shared.spritegroup) < 6:
        rand_x = random.randrange(110, common.SCREEN_WIDTH - 110)
        rand_y = random.randrange(110, common.SCREEN_HEIGHT - 110)
        pos = (rand_x, rand_y)

        typename = monsters.shared.random_typename()
        m = monsters.shared.add(typename)
        m.set_position(pos)
        effects.shared.add("SparkleYellow").set_position(pos)

    # Replace gems
    if len(gemstones.shared.spritegroup) < 6:
        rand_x = random.randrange(110, common.SCREEN_WIDTH - 110)
        rand_y = random.randrange(110, common.SCREEN_HEIGHT - 110)
        pos = (rand_x, rand_y)

        typename = gemstones.shared.random_typename()
        g = gemstones.shared.add(typename)
        g.set_position(pos)
        effects.shared.add("SparkleWhite").set_position(pos)

    soundeffects.remove_expired()

    common.clock.tick(common.frames_per_second)