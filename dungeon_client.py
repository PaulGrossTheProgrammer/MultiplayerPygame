# Dungeon Internet Client

import socket
import threading
import queue
import math
import time

import pygame

import common
import message
import soundeffects
import gemstones
import effects
import monsters
import dungeontiles
import fireball

# Each queue is used for THREAD-SAFE, one-way communication
request_queue = queue.Queue()  # GameClientThread -> SocketThread
response_queue = queue.Queue()  # GameClientThread <- SocketThread


def reset_game():
    global wait_for_update

    wait_for_update = False

    gemstones.shared.empty()
    effects.shared.empty()
    monsters.shared.empty()
    dungeontiles.shared.empty()
    fireball.shared.empty()

# This thread establishes a socket connection to the Game Server.
class GameClientSocketThread(threading.Thread):
    def __init__(self, server):
        threading.Thread.__init__(self)
        self.server = server
        self.socket_active = True
        self.has_error = False

    def run(self):
        print("GameClientSocketThread Started:")

        while self.socket_active:
            try:
                server_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)
                server_socket.connect((self.server, common.server_port))
                print("Connected to [{}]".format(self.server))

                # Tell the game to clear any error status
                response_queue.put("response:error-clear\n")

                # The first request is always a login
                request = "request:login,username:{}".format(username)
                while self.socket_active:
                    self.has_error = False
                    # Send the request to the server socket
                    server_socket.sendall(bytes(request, 'UTF-8'))

                    # WAIT for a response from the server socket...
                    response = server_socket.recv(8192).decode()

                    # Handle the special case of termination
                    if response.startswith("response:socket-terminated"):
                        self.socket_active = False
                    else:
                        # Send the response to the Game Window
                        response_queue.put(response)

                    # WAIT here for a new request from the Game Client Window
                    if self.socket_active:
                        request = request_queue.get()

            except (ConnectionRefusedError, ConnectionResetError):
                self.has_error = True

                # Reset the game and send the error messsage
                response_queue.put("response:reset-all\n")
                error_text = "Failed to connect to [{}]".format(self.server)
                template = "response:error-set,text:{}\n"
                response_queue.put(template.format(error_text))
                print(error_text)

                if self.socket_active:
                    time.sleep(1)
                    print("retrying connection ...")

            finally:
                if server_socket is not None:
                    server_socket.close()

        print("Socket thread terminated")

    def terminate(self):
        self.socket_active = False


SERVER = input("Enter server address: ")
if SERVER == "":
    SERVER = "localhost"
print("Server set to {}".format(SERVER))

username = input("Your name: ")

client_socket_thread = GameClientSocketThread(SERVER)
client_socket_thread.start()


pygame.init()

pygame.display.set_mode([common.SCREEN_WIDTH, common.SCREEN_HEIGHT])
screen = pygame.display.get_surface()

class StatusLine(pygame.sprite.Sprite):

    font_30 = pygame.font.SysFont(pygame.font.get_default_font(), 30)
    score = 0

    def __init__(self, position):
        super().__init__()
        self.position = position
        self.error = None

    def update(self):
        if self.error is not None:
            text = self.error
        else:
            text = "Name: {}".format(username)

        self.image = self.font_30.render(text, True, common.WHITE)
        self.rect = self.image.get_rect()
        self.rect.center = self.position

    def set_error(self, message):
        self.error = message

    def clear_error(self):
        self.error = None

status_group = pygame.sprite.Group()
status_sprite = StatusLine([250, 20])
status_group.add(status_sprite)

towerselected_group = pygame.sprite.Group()

def draw_arrow(screen, start, end, color, thickness):
    pygame.draw.line(screen, color, start, end, thickness)

    # calculate angle
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    angle = math.atan2(dy, dx)

    head_length = 15
    head_angle = math.pi/6

    # Draw first head line
    angle1 = angle + head_angle
    dx1 = math.cos(angle1) * head_length
    dy1 = math.sin(angle1) * head_length
    end1 = (int(end[0] - dx1), int(end[1] - dy1))
    pygame.draw.line(screen, color, end, end1, thickness)

    # Draw second head line
    angle2 = angle - head_angle
    dx2 = math.cos(angle2) * head_length
    dy2 = math.sin(angle2) * head_length
    end2 = (int(end[0] - dx2), int(end[1] - dy2))
    pygame.draw.line(screen, color, end, end2, thickness)

# Game Client Window - Main Thread

soundeffects.set_global_volume(0.1)

curr_gemtype = "GemGreen"
fireball_start = None
wait_for_update = False
new_requests = []
game_on = True
while game_on:
    #
    # EVENT HANDLING:
    #
    # Process any mouse and keyboard evets
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            print("User closed the window")
            game_on = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                curr_gemtype = "GemGreen"
            if event.key == pygame.K_r:
                curr_gemtype = "GemRed"
            if event.key == pygame.K_p:
                curr_gemtype = "GemPink"
            if event.key == pygame.K_d:
                curr_gemtype = "GemDiamond"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked_gem = gemstones.shared.collide_sprite(event.pos)
            clicked_monster = monsters.shared.collide_sprite(event.pos)
            clicked_tower = dungeontiles.shared.collide_sprite_type(
                event.pos, "FireballTower")

            if clicked_gem is not None:
                template = "request:delete-gem,id:{}\n"
                new_request = template.format(clicked_gem.sprite_id)
                print(new_request)
                new_requests.append(new_request)
            elif clicked_monster is not None:
                template = "request:bump-monster,id:{}\n"
                new_request = template.format(clicked_monster.sprite_id)
                print(new_request)
                new_requests.append(new_request)
            elif clicked_tower is not None:
                fireball_start = clicked_tower.rect.center
                effect = effects.FireCircle()
                effect.set_position(clicked_tower.rect.center)
                towerselected_group.add(effect)
            else:
                template = "request:add-gem,gemtype:{},x:{},y:{}\n"
                new_request = template.format(
                    curr_gemtype, event.pos[0], event.pos[1])
                print(new_request)
                new_requests.append(new_request)
        if (event.type == pygame.MOUSEBUTTONUP and event.button == 1):
            if fireball_start is not None:
                dx = event.pos[0] - fireball_start[0]
                dy = event.pos[1] - fireball_start[1]
                angle = math.atan2(dy, dx)
                template = "request:add-fireball,x:{},y:{},angle:{}\n"
                new_request = template.format(
                    fireball_start[0], fireball_start[1], angle)

                towerselected_group.empty()
                fireball_start = None
                print(new_request)
                new_requests.append(new_request)

    #
    # REQUEST HANDLING:
    #
    # If we are not waiting for an update, and there are
    # no other requests, request an update
    if wait_for_update is False and len(new_requests) == 0:
        new_requests.append("request:update\n")
        wait_for_update = True

    # Send any new requests to the ClientSocketThread queue
    for request in new_requests:
        request_queue.put(request)
    new_requests.clear()

    #
    # RESPONSE HANDLING:
    #

    # Process any available responses from the ClientSocketThread queue
    try:
        # DON'T WAIT on queue, always move on even if the queue is empty
        response = response_queue.get_nowait()
    except(queue.Empty):
        response = None

    if response is not None:
        load_update = False
        id_list = []
        module = None
        sprite_type = None
        module_updates = {}

        for line in response.splitlines(False):
            data = message.decode_dictionary(line)
            if "response" in data:
                response_type = data["response"]
                if response_type == "update":
                    sprite_update = True
                    wait_for_update = False
                    if "module" in data:  # Hack for new class
                        module = data["module"]
                    else:
                        module = data["group"]
                    module_group = []
                    module_updates[module] = module_group
                else:
                    sprite_update = False

                if response_type == "soundeffects":
                    soundeffects.decode_effects(data)

                if response_type == "reset-all":
                    reset_game()
                if response_type == "error-set":
                    text = data["text"]
                    status_sprite.set_error(text)
                if response_type == "error-clear":
                    status_sprite.clear_error()

            elif sprite_update is True:
                module_group.append(data)

        for module, datalines in module_updates.items():
            if module == "gemstones":
                gemstones.shared.decode_update(datalines)
            elif module == "effects":
                effects.shared.decode_update(datalines)
            elif module == "monsters":
                monsters.shared.decode_update(datalines)
            elif module == "fireball":
                fireball.shared.decode_update(datalines)
            elif module == "dungeontiles":
                dungeontiles.shared.decode_update(datalines)

    #
    # ANIMATION HANDLING:
    #

    # Update sprite animation
    gemstones.shared.update()
    effects.shared.update()
    monsters.shared.update()
    fireball.shared.update()
    dungeontiles.shared.update()
    status_group.update()
    towerselected_group.update()

    # Draw game screen
    screen.fill(common.BLACK)

    gemstones.shared.draw(screen)
    dungeontiles.shared.draw(screen)
    monsters.shared.draw(screen)
    fireball.shared.draw(screen)
    effects.shared.draw(screen)
    towerselected_group.draw(screen)
    status_group.draw(screen)

    if fireball_start is not None:
        draw_arrow(screen, fireball_start,
                   pygame.mouse.get_pos(), common.RED, 5)

    pygame.display.flip()

    common.clock.tick(common.frames_per_second)

request_queue.put("request:logout\n")

if client_socket_thread.has_error:
    client_socket_thread.terminate()

pygame.quit()