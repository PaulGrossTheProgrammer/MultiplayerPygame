# Dungeon Internet Server

import socket
import threading
import queue
import math
import random

import pygame

import common
from common import calc_distance, calc_angle, calc_endpoint
import soundeffects
import gemstones
import effects
import monsters
import fireball
import dungeontiles
# import level
import clientserver
from clientserver import data_xy

# This ListenerThread creates a SocketThread per Internet Game Client.
# It listens on the public game Port for new Internet Game CLients.
# The created SocketThread exists only while the Internet Game Client
# needs to play the game, and is closed when the player leaves.
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("", common.server_port))

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

                self.client_socket.send(bytes(response, "UTF-8"))

        except Exception:
            # Remove this thread from the socket login dictionary
            socket_logins.pop(self)

        print("Client at ", self.clientAddress, " disconnected...")


#
# Game Server
#

# Set the shared sprites into server mode
# All delta mode groups
gemstones.shared.set_as_server(enable_delta=True, delta_timeout_s=2)
dungeontiles.shared.set_as_server(enable_delta=True)

# All remaining groups
monsters.shared.set_as_server()
effects.shared.set_as_server()
fireball.shared.set_as_server()

def check_monster_shielded(fireball, monster, expl_range):
    line_of_explosion = (fireball.rect.center, monster.rect.center)

    # Monsters are shielded by other monsters.
    # NOTE: Don't allow a monster to shield itself.
    # NOTE: Overlaping monsters cannot shield each other.
    for test_monster in monsters.shared.spritegroup:
        # Monster doesn't shield itself
        if test_monster is not monster:
            # Overlapping monsters can't shield
            if not test_monster.rect.collidepoint(
                monster.rect.center
            ):
                if test_monster.rect.clipline(line_of_explosion):
                    return True

    all_walls = dungeontiles.shared.typegroup("WallTile")
    # Eliminate all walls outside explosion range
    near_walls = []
    for test_wall in all_walls:
        if (
            abs(test_wall.rect.center[0] - fb.rect.center[0]) < expl_range
            and
            abs(test_wall.rect.center[1] - fb.rect.center[1]) < expl_range
        ):
            near_walls.append(test_wall)

    for tile in near_walls:
        if tile.rect.clipline(line_of_explosion):
            return True

    return False

def shift_sprite(sprite, angle, distance):
    start_pos = sprite.rect.center
    new_pos = calc_endpoint(start_pos, angle, distance)
    clientserver.set_position(sprite, new_pos)

# mapname = "map01.txt"
# mapname = "map_amelie.txt"
# level.start_level(mapname)

print("Map size: {} tiles".format(len(dungeontiles.shared.spritegroup)))

dungeontiles.shared.add("FireballTower", data_xy((50, 50)))
dungeontiles.shared.add("FireballTower", data_xy((750, 50)))
dungeontiles.shared.add("FireballTower", data_xy((50, 550)))
dungeontiles.shared.add("FireballTower", data_xy((750, 550)))

dungeontiles.shared.add("WallTile", data_xy((350, 300)))

# Monster actions are recacluated periodically
monster_action_counter = 0
monster_action_trigger = common.frames_per_second / 2

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
        except (queue.Empty):
            socket_thread = None
            request = None

        if request is not None:
            response = None
            # print(request)

            for line in request.splitlines(False):
                data = clientserver.decode_dictionary(line)

                if "request" in data:
                    request_type = data["request"]
                    if request_type == "login":
                        username = data["username"]
                        print("logging in user [{}]".format(username))
                        response = "response:login-success,username:{}\n".format(
                            username)
                        socket_logins[socket_thread] = username

                    elif request_type == "logout":
                        username = socket_logins[socket_thread]
                        print("[{}] logged out".format(username))
                        socket_logins.pop(socket_thread)
                        response = "response:socket-terminated\n"

                    elif request_type == "update":
                        response = clientserver.server_encode_all_responses(
                            data, socket_thread)

                    elif request_type == "bump-monster":
                        sprite_id = int(data["id"])
                        angle = float(data["angle"])
                        monster = monsters.shared.get(sprite_id)
                        if monster is not None:
                            print("Bumping monster: " + str(monster))
                            shift_sprite(monster, angle, 10)
                            soundeffects.add_shared("painhit")
                        response = "response:bumped-monster\n"

                    elif request_type == "gem-drag":
                        sprite_id = int(data["id"])
                        angle = float(data["angle"])
                        gem = gemstones.shared.get(sprite_id)
                        if gem is not None:
                            print("Dragging gem: " + str(gem))
                            shift_sprite(gem, angle, 40)
                        response = "response:dragged-gem\n"

                    elif request_type == "add-fireball":
                        sprite = fireball.shared.add("FireballRed", data)
                        soundeffects.add_shared("fireball")
                        response = "response:added-fireball\n"

            if response is None:
                response = "response:unknown-request"  # Default response

                if socket_thread in socket_logins:
                    username = socket_logins[socket_thread]
                    print("Request error from user: [{}]".format(username))
                print("[{}]".format(request))

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
    monster_action_counter += 1
    if monster_action_counter >= monster_action_trigger:
        monster_action_counter = 0
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
        False, False, collided=pygame.sprite.collide_circle)
    for gem in coll_gem_monster:
        gemstones.shared.remove(gem)
        effects.shared.add("Vanish", gem.get_data())

        sound = soundeffects.random_pickup()
        soundeffects.add_shared(sound)

    # Fireball and monster collisions
    coll_fb_monster = pygame.sprite.groupcollide(
        fireball.shared.spritegroup, monsters.shared.spritegroup,
        False, False, collided=pygame.sprite.collide_circle)
    for fb in coll_fb_monster:
        fb.done = True
        # Damage each monster hit
        for monster in coll_fb_monster[fb]:
            monster.hit(5)

    # Fireball and wall collisions
    coll_fb_walls = pygame.sprite.groupcollide(
        fireball.shared.spritegroup, dungeontiles.shared.typegroup("WallTile"),
        False, False, collided=pygame.sprite.collide_circle)
    for fb in coll_fb_walls:
        fb.done = True

    # Explode completed fireballs
    for fb in fireball.shared.spritegroup:
        if fb.done is True:
            soundeffects.add_shared("explosion")
            effects.shared.add("ExplosionRed", fb.get_data())
            fb.kill()

            # Damage unshielded monsters within explosion range
            expl_range = 200

            for curr_monster in monsters.shared.spritegroup:
                monster_dist = calc_distance(fb.rect.center, curr_monster.rect.center)
                print(curr_monster)
                print("monster distance = " + str(monster_dist))

                if monster_dist < expl_range:
                    monster_shielded = check_monster_shielded(fb, curr_monster,
                                                              expl_range)

                    if monster_shielded is False:
                        # Reduce damage with distance
                        dist_ratio = monster_dist/expl_range  # Calc the ratio 0 to 1
                        dist_inv_ratio = 1 - dist_ratio  # Convert to 1 to 0

                        max_damage = 4
                        damage_float = max_damage * dist_inv_ratio  # multiply by max
                        damage = math.ceil(damage_float)  # Round up to integer
                        print("monster damage = " + str(damage))
                        curr_monster.hit(damage)

                        # Reduce bump with distance
                        if monster.dead is not True:
                            angle = calc_angle(fb.rect.center, curr_monster.rect.center)

                            max_bump = 20
                            bump = math.ceil(max_bump * dist_inv_ratio)
                            shift_sprite(curr_monster, angle, bump)

                            effects.shared.add("BloodHit", curr_monster.get_data())
                            soundeffects.add_shared("painhit")

    # Remove dead monsters
    for monster in monsters.shared.spritegroup:
        if monster.dead is True:
            monster.kill()
            effects.shared.add("BloodKill", monster.get_data())
            soundeffects.add_shared("monsterkill")

    # Replace dead monsters
    if len(monsters.shared.spritegroup) < 2:
        rand_x = random.randrange(110, common.SCREEN_WIDTH - 110)
        rand_y = random.randrange(110, common.SCREEN_HEIGHT - 110)
        pos = {"x": rand_x, "y": rand_y}

        typename = monsters.shared.random_typename()
        monsters.shared.add(typename, pos)
        effects.shared.add("SparkleYellow", pos)

    # Replace gems
    if len(gemstones.shared.spritegroup) < 0:
        rand_x = random.randrange(110, common.SCREEN_WIDTH - 110)
        rand_y = random.randrange(110, common.SCREEN_HEIGHT - 110)
        pos = {"x": rand_x, "y": rand_y}

        typename = gemstones.shared.random_typename()
        gemstones.shared.add(typename, pos)

        effects.shared.add("SparkleWhite", pos)

    soundeffects.remove_expired()

    common.clock.tick(common.frames_per_second)
