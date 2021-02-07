# Dungeon Internet Client

import threading
import queue
import socket
import math

import pygame

import common
import message
import gemstones
import effects
import monsters
import dungeontiles
import fireball

# Each queue is used for THREAD-SAFE, one-way communication
request_queue = queue.Queue()  # GameClientThread -> SocketThread
response_queue = queue.Queue()  # GameClientThread <- SocketThread

# This thread establishes a socket connection to the Game Server.
class GameClientSocketThread(threading.Thread):
    def __init__(self, server):
        threading.Thread.__init__(self)
        self.server = server

    def run(self):
        print("GameClientSocketThread Started:")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((self.server, common.server_port))

        # The first request is always a login
        request = "request:login,username:{}".format(username)
        while True:
            # Send the request to the server socket
            server_socket.sendall(bytes(request, 'UTF-8'))

            # WAIT for a response from the server socket...
            response = server_socket.recv(8192).decode()

            # Send the response to the Game Window
            response_queue.put(response)

            # WAIT here for a new request from the Game Client Window
            request = request_queue.get()

        server_socket.close()

SERVER = input("Enter server address: ")
if SERVER == "":
    SERVER = "localhost"
print("Connecting to {}".format(SERVER))

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
        self.update_image()

    def update_image(self):
        text = "Name: {}".format(username)
        self.image = self.font_30.render(text, True, common.WHITE)
        self.rect = self.image.get_rect()
        self.rect.center = self.position


status_group = pygame.sprite.Group()
status_sprite = StatusLine([150, 20])
status_group.add(status_sprite)


# Game Client Window - Main Thread
curr_gemtype = "GemGreen"
fireball_start = None
wait_for_update = False
new_requests = []
game_on = True
while game_on:
    # Check for mouse and keyboard events
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
            # Was a gem clicked?
            clicked_gem = gemstones.shared.collide_sprite(event.pos)
            clicked_monster = monsters.shared.collide_sprite(event.pos)
            tower = dungeontiles.shared.collide_sprite_type(
                event.pos, "FireballTower")

            if clicked_gem is not None:
                template = "request:delete-gem,id:{}\n"
                new_request = template.format(clicked_gem.sprite_id)
                print(new_request)
                new_requests.append(new_request)
            elif tower is not None:
                fireball_start = tower.rect.center
            elif clicked_monster is not None:
                template = "request:bump-monster,id:{}\n"
                new_request = template.format(clicked_monster.sprite_id)
                print(new_request)
                new_requests.append(new_request)
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
                fireball_start = None
                print(new_request)
                new_requests.append(new_request)

    # If we are not waiting for an update, and there are
    # no other requests, request an update
    if wait_for_update is False and len(new_requests) == 0:
        new_requests.append("request:update\n")
        wait_for_update = True

    # Send any new requests to the ClientSocketThread queue
    for request in new_requests:
        request_queue.put(request)
    new_requests.clear()

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

            elif sprite_update is True:
                module_group.append(data)

        for module, datalines in module_updates.items():
            # TODO - process other sprite modules
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

    # Update sprite animation
    gemstones.shared.update()
    effects.shared.update()
    monsters.shared.update()
    fireball.shared.update()
    dungeontiles.shared.update()
    status_group.update()

    # Draw game screen
    screen.fill(common.BLACK)

    gemstones.shared.draw(screen)
    effects.shared.draw(screen)
    dungeontiles.shared.draw(screen)
    monsters.shared.draw(screen)
    fireball.shared.draw(screen)
    status_group.draw(screen)

    if fireball_start is not None:
        pygame.draw.line(screen, common.RED,
                         fireball_start, pygame.mouse.get_pos(), 2)

    pygame.display.flip()

    common.clock.tick(common.frames_per_second)

pygame.quit()
quit()