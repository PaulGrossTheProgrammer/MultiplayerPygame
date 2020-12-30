# Pygame Internet Client
import threading
import time
import socket

import pygame

import gemstones

from common import server_port

class MessageClientThread(threading.Thread):
    def __init__(self, server, username, messages_server, messages_client):
        threading.Thread.__init__(self)
        print("MessageClientThread Created:")

        self.server = server
        self.messages_server = messages_server

    def run(self):
        print("MessageClientThread Started:")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((self.server, server_port))
        login_message = "LOGIN username:{}".format(username)
        client.sendall(bytes(login_message, 'UTF-8'))
        while True:
            in_data = client.recv(1024)
            server_message = in_data.decode()
            if server_message != "UPDATE":
                self.messages_server.append(server_message)

            if len(messages_client) > 0:
                out_data = messages_client.pop()
                print("Client request [{}]".format(out_data))
            else:
                # TODO - build a proper update request
                out_data = "UPDATE id:1,test:2"

            client.sendall(bytes(out_data, 'UTF-8'))
            if out_data == 'bye':
                break

            time.sleep(0.1)

        client.close()

SERVER = input("Enter server address: ")
if SERVER == "":
    SERVER = "localhost"
print("Connecting to {}".format(SERVER))

username = input("Your name: ")

messages_server = []
messages_client = []

messagethread = MessageClientThread(
    SERVER, username, messages_server, messages_client)
messagethread.start()

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

latest_message = None

gem_group = pygame.sprite.Group()
gem_group.add(gemstones.GemGreen([100, 100]))

game_on = True
while game_on:
    # Check for mouse and keyboard events
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            print("User closed the window")
            game_on = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x_click = event.pos[0]
            y_click = event.pos[1]
            messages_client.append("CLICK x:{},y:{}".format(x_click, y_click))

    gem_group.update()

    screen.fill(BLACK)
    gem_group.draw(screen)

    if len(messages_server) > 0:
        latest_message = messages_server.pop()

        key_dict = {}
        space_index = latest_message.find(" ")
        # print("space_index={}".format(space_index))
        key = latest_message[0:space_index]
        # print("key={}".format(key))
        values = latest_message[space_index + 1:]
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
            x = int(update_response["x"])
            y = int(update_response["y"])
            print("x:{},y:{}".format(x, y))

            gem = gem_group.sprites()[0]
            if gem is not None:
                gem.set_position([x, y])

    if latest_message is not None:
        drawtext(screen, latest_message)

    pygame.display.flip()

    clock.tick(frames_per_second)

pygame.quit()
quit()