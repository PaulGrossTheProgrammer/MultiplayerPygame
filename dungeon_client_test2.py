# Pygame Internet Client
import threading
# import datetime
import socket

import pygame

import gemstones

from common import server_port

# Each queue is used for THREAD-SAFE, one-way communication
request_queue = []  # Append from Game window, pop(0) at Network Thread
response_queue = []  # Append from Network Thread, pop(0) at Game window
# TODO: Lookup threading condition for a better name than 'cv'
cv = threading.Condition()

# This thread establishes a socket connection to the Game Server.
class GameClientSocketThread(threading.Thread):
    def __init__(self, server):
        threading.Thread.__init__(self)
        self.server = server

    def run(self):
        print("GameClientSocketThread Started:")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((self.server, server_port))
        request = "LOGIN username:{}".format(username)
        while True:
            # Send the request to the server socket
            client.sendall(bytes(request, 'UTF-8'))

            # Wait for a response from the server socket...
            response = client.recv(1024).decode()

            # Send the response to the Game Window
            response_queue.append(response)

            # Wait here for a new request from the Game Client Window
            with cv:
                while len(request_queue) == 0:
                    cv.wait()
                request = request_queue.pop(0)
                if request.startswith("UPDATE"):
                    # Clear other UPDATE requests
                    for item in request_queue:
                        if item.startswith("UPDATE"):
                            request_queue.remove(item)

        client.close()

SERVER = input("Enter server address: ")
if SERVER == "":
    SERVER = "localhost"
print("Connecting to {}".format(SERVER))

username = input("Your name: ")

client_socket_thread = GameClientSocketThread(SERVER)
client_socket_thread.start()

pygame.init()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
screen = pygame.display.get_surface()

frames_per_second = 30
clock = pygame.time.Clock()

message_font_50 = pygame.font.SysFont(pygame.font.get_default_font(), 50)

def draw(screen, image, position=None):
    rect = image.get_rect()
    if position is None:
        rect.center = [screen.get_width()/2, screen.get_height()/2]

    screen.blit(image, rect)

def drawtext(screen, text, size=None, color=None, position=None):
    global message_font_50

    if size is None:
        font = message_font_50
    else:
        font = pygame.font.SysFont(pygame.font.get_default_font(), size)

    if color is None:
        color = WHITE

    image = font.render(text, True, color)

    draw(screen, image, position)

# latest_message = None

gem_group = pygame.sprite.Group()
gem_group.add(gemstones.GemGreen([100, 100]))

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
            x = event.pos[0]
            y = event.pos[1]
            new_request = "CLICK x:{},y:{}".format(x, y)
            print(new_request)
            new_requests.append(new_request)
            # current_request = True
            wait_for_update is True

    if wait_for_update is False:
        new_requests.append("UPDATE id:1,test:2")
        wait_for_update = True

    # Send any new requests to the ClientSocketThread queue
    if len(new_requests) > 0:
        with cv:
            request_queue.extend(new_requests)
            cv.notify_all()

        # print("New requests Queued")
        new_requests.clear()

    # Process any responses from the ClientSocketThread queue
    if len(response_queue) > 0:
        response = response_queue.pop(0)

        key_dict = {}
        space_index = response.find(" ")
        # print("space_index={}".format(space_index))
        key = response[0:space_index]
        # print("key={}".format(key))
        values = response[space_index + 1:]
        # print("values={}".format(values))
        value_pairs = values.split(",")
        # print("value_pairs={}".format(value_pairs))
        values_dict = {}
        for pair in value_pairs:
            pair_list = pair.split(":")
            values_dict[pair_list[0]] = pair_list[1]
        # print("values_dict={}".format(values_dict))
        key_dict[key] = values_dict

        update_response = key_dict.get("UPDATE")
        if update_response is not None:
            wait_for_update = False
            x = int(update_response["x"])
            y = int(update_response["y"])

            gem = gem_group.sprites()[0]
            if gem is not None:
                gem.set_position([x, y])

    # Update sprites
    gem_group.update()

    # Draw game screen
    screen.fill(BLACK)
    gem_group.draw(screen)

    # if response is not None:
    #     drawtext(screen, response)

    pygame.display.flip()

    clock.tick(frames_per_second)

pygame.quit()
quit()