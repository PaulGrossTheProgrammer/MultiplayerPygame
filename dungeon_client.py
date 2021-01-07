# Dungeon Internet Client

import threading
import queue
# import datetime
import socket

import pygame

import common
import message
import gemstones


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
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((self.server, common.server_port))
        request = "LOGIN username:{}".format(username)
        while True:
            # Send the request to the server socket
            client.sendall(bytes(request, 'UTF-8'))

            # WAIT for a response from the server socket...
            response = client.recv(8192).decode()

            # Send the response to the Game Window
            response_queue.put(response)

            # WAIT here for a new request from the Game Client Window
            request = request_queue.get()

        client.close()

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

message_font_30 = pygame.font.SysFont(pygame.font.get_default_font(), 30)

def draw(screen, image, position=None):
    rect = image.get_rect()
    if position is None:
        rect.center = [screen.get_width()/2, screen.get_height()/2]

    screen.blit(image, rect)

def drawtext(screen, text, size=None, color=None, position=None):
    global message_font_30

    if size is None:
        font = message_font_30
    else:
        font = pygame.font.SysFont(pygame.font.get_default_font(), size)

    if color is None:
        color = common.WHITE

    image = font.render(text, True, color)

    draw(screen, image, position)

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
                template = "DELETE id:{}\n"
                new_request = template.format(clicked_id)
                print(new_request)
                new_requests.append(new_request)
            else:
                template = "CLICK x:{},y:{}\n"
                new_request = template.format(click_pos[0], click_pos[1])
                print(new_request)
                new_requests.append(new_request)
            # current_request = True
            wait_for_update is True

    # If we are not wait for an update, and there are
    # no other requests, request an update
    if wait_for_update is False and len(new_requests) == 0:
        new_requests.append("UPDATE id:1,test:2\n")
        wait_for_update = True

    # Send any new requests to the ClientSocketThread queue
    for request in new_requests:
        request_queue.put(request)
    new_requests.clear()

    # Process any responses from the ClientSocketThread queue
    try:
        # Don't wait on queue, just get any available response
        response = response_queue.get_nowait()
    except(queue.Empty):
        response = None

    if response is not None:
        print(response)
        is_update = False
        id_list = []
        sprite_type = None

        for line in response.splitlines(False):
            data = message.decode_dictionary(line)
            if "reponsetype" in data:
                if data["reponsetype"] == "spriteupdate":
                    is_update = True
                    wait_for_update = False
                    sprite_type = data["type"]
            elif is_update is True:
                sprite_id = int(data["id"])
                x = int(data["x"])
                y = int(data["y"])
                id_list.append(sprite_id)

                sprite = gemstones.get_gem(sprite_id)
                if sprite is None:
                    gemstones.add_gem(sprite_type, [x, y], sprite_id)
                else:
                    sprite.set_position([x, y])

        if is_update is True:
            # Remove any gems not included in the update
            for sprite in gemstones.spritegroup:
                curr_id = sprite.sprite_id
                if curr_id not in id_list:
                    gemstones.remove_gem(curr_id)

    # Update sprites
    gemstones.spritegroup.update()

    # Draw game screen
    screen.fill(common.BLACK)
    gemstones.spritegroup.draw(screen)

    pygame.display.flip()

    common.clock.tick(common.frames_per_second)

pygame.quit()
quit()