# Dungeon Internet Client

import threading
import queue
import socket

import pygame

import common
import message
import gemstones
import soundeffects


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

# Game Client Window - Main Thread
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
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click_pos = event.pos
            # Was a gem clicked?
            clicked_id = None
            for sprite in gemstones.spritegroup:
                if sprite.rect.collidepoint(click_pos):
                    clicked_id = sprite.sprite_id

            if clicked_id is not None:
                template = "request:delete,id:{}\n"
                new_request = template.format(clicked_id)
                print(new_request)
                new_requests.append(new_request)
            else:
                template = "request:add,x:{},y:{}\n"
                new_request = template.format(click_pos[0], click_pos[1])
                print(new_request)
                new_requests.append(new_request)
            # wait_for_update is True

    # If we are not wait for an update, and there are
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
                    module = data["module"]
                    module_group = []
                    module_updates[module] = module_group
                else:
                    sprite_update = False

            elif sprite_update is True:
                module_group.append(data)

        for module, datalines in module_updates.items():
            # TODO - process other sprite modules
            if module == "gemstones":
                gemstones.decode_update(datalines)

    # Update sprite animation
    gemstones.update()

    # Draw game screen
    screen.fill(common.BLACK)
    gemstones.draw(screen)

    pygame.display.flip()

    common.clock.tick(common.frames_per_second)

pygame.quit()
quit()