# Dungeon Internet Client

import socket
import threading
import queue
import math
import time

import pygame

import common
from common import calc_angle, calc_endpoint, calc_distance
import clientserver
from clientserver import MAX_RESPONSE_BYTES
import soundeffects
import gemstones
import effects
import monsters
import dungeontiles
import fireball
import cursor

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
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.connect((self.server, common.server_port))
                print("Connected to [{}]".format(self.server))

                # Tell the game to clear any error status
                response_queue.put("response:error-clear\n")

                # The first request is always a login
                request = "request:login,username:{}".format(username)
                while self.socket_active:
                    self.has_error = False
                    # Send the request to the server socket
                    server_socket.sendall(bytes(request, "UTF-8"))

                    # WAIT for a response from the server socket...
                    response = server_socket.recv(MAX_RESPONSE_BYTES).decode()

                    # Handle the special case of termination
                    if response.startswith("response:socket-terminated"):
                        self.socket_active = False
                    else:
                        # Send the response to the Game Window
                        # DEBUG:
                        # print(response)
                        # print("Response bytes: {}".format(len(response)))
                        response_queue.put(response)

                    # DEBUG - delay request processing
                    # time.sleep(0.4)

                    # WAIT here for a new request from the Game Client Window
                    if self.socket_active:
                        request = request_queue.get()

            except Exception:
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

pygame.mouse.set_visible(False)


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


def draw_arrow(screen, start, end, color, thickness):
    head_length = 80
    head_angle = math.pi / 6

    # calculate angles
    angle = calc_angle(end, start)
    angle1 = angle + head_angle
    angle2 = angle - head_angle

    # Calculate points
    end1 = calc_endpoint(end, angle1, head_length)
    end2 = calc_endpoint(end, angle2, head_length)
    mid = calc_endpoint(end, angle, head_length * 0.5)

    # Draw the arrow
    pygame.draw.line(screen, color, start, mid, thickness)

    pygame.draw.line(screen, color, end, end1, thickness)
    pygame.draw.line(screen, color, end, end2, thickness)

    pygame.draw.line(screen, color, end1, mid, thickness)
    pygame.draw.line(screen, color, end2, mid, thickness)


status_group = pygame.sprite.Group()
status_sprite = StatusLine([250, 20])
status_group.add(status_sprite)

cursor_group = pygame.sprite.Group()
cursor = cursor.PlayerCursor()
cursor_group.add(cursor)

towerselected_group = pygame.sprite.Group()
tower_locked = False

soundeffects.set_global_volume(0.05)

curr_gemtype = "GemGreen"

fireball_start = None
gemdrag_start = None
gemdrag_id = None

wait_for_update = False
new_requests = []
game_on = True
while game_on:
    #
    # USER EVENT HANDLING:
    #
    # Process any mouse and keyboard events
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

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            clicked_tower = dungeontiles.shared.collide_sprite_type(
                event.pos, "FireballTower")

            towerselected_group.empty()
            if clicked_tower is None:
                tower_locked = False
                fireball_start = None
            else:
                fireball_start = clicked_tower.rect.center
                effect = effects.FireCircle()
                effect.set_position(clicked_tower.rect.center)
                towerselected_group.add(effect)
                tower_locked = True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked_gem = gemstones.shared.collide_sprite(event.pos)
            clicked_monster = monsters.shared.collide_sprite(event.pos)
            clicked_tower = dungeontiles.shared.collide_sprite_type(
                event.pos, "FireballTower")

            if clicked_gem is not None:
                gemdrag_start = clicked_gem.rect.center
                gemdrag_id = clicked_gem.sprite_id
            elif clicked_monster is not None:
                angle = calc_angle(event.pos, clicked_monster.rect.center)
                template = "request:bump-monster,id:{},angle:{}\n"
                new_request = template.format(clicked_monster.sprite_id, angle)
                print(new_request)
                new_requests.append(new_request)
            elif clicked_tower is not None:
                fireball_start = clicked_tower.rect.center
                effect = effects.FireCircle()
                effect.set_position(clicked_tower.rect.center)
                towerselected_group.add(effect)

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if fireball_start is not None:
                angle = calc_angle(fireball_start, event.pos)
                distance = calc_distance(fireball_start, event.pos)
                template = "request:add-fireball,x:{},y:{},angle:{},distance:{}\n"
                new_request = template.format(
                    fireball_start[0], fireball_start[1], angle, distance)
                new_requests.append(new_request)

                if tower_locked is False:
                    towerselected_group.empty()
                    fireball_start = None

            if gemdrag_start is not None:
                angle = calc_angle(gemdrag_start, event.pos)
                template = "request:gem-drag,id:{},angle:{}\n"
                new_request = template.format(gemdrag_id, angle)

                gemdrag_start = None
                gemdrag_id = None
                new_requests.append(new_request)

    #
    # REQUEST HANDLING:
    #

    # If we are not waiting for an update, and there are
    # no other requests, request an update
    if wait_for_update is False and len(new_requests) == 0:
        new_requests.append(clientserver.client_request_all_updates())
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
    except (queue.Empty):
        response = None

    if response is not None:
        # print(response)
        all_lines = response.splitlines(False)

        # Handle command lines in the response
        # And extract the updates
        update_datalines = []
        for line in all_lines:
            data = clientserver.decode_dictionary(line)
            if "response" in data:
                response_type = data["response"]

                if response_type == "reset-all":
                    reset_game()
                elif response_type == "error-set":
                    text = data["text"]
                    status_sprite.set_error(text)
                elif response_type == "error-clear":
                    status_sprite.clear_error()
                elif response_type == "":
                    status_sprite.clear_error()
                else:
                    update_datalines.append(data)
            else:
                update_datalines.append(data)

        # Try to Decode any remaining data as updates
        if len(update_datalines) > 0:
            was_an_update = clientserver.client_decode_all_updates(update_datalines)

            if was_an_update is True:
                wait_for_update = False

    #
    # ANIMATION HANDLING:
    #

    # Update shared sprites
    gemstones.shared.update()
    effects.shared.update()
    monsters.shared.update()
    fireball.shared.update()
    dungeontiles.shared.update()

    # Update local sprites
    status_group.update()
    towerselected_group.update()
    cursor_group.update()

    # Position the cursor at the mouse pointer
    curson_pos = pygame.mouse.get_pos()
    cursor.set_pos(curson_pos)

    # Draw game screen
    screen.fill(common.BLACK)

    gemstones.shared.draw(screen)
    dungeontiles.shared.draw(screen)
    monsters.shared.draw(screen)
    fireball.shared.draw(screen)
    effects.shared.draw(screen)
    towerselected_group.draw(screen)

    status_group.draw(screen)
    cursor_group.draw(screen)

    # Display arrows
    if fireball_start is not None:
        draw_arrow(screen, fireball_start, pygame.mouse.get_pos(), common.RED, 5)

    if gemdrag_start is not None:
        draw_arrow(screen, gemdrag_start, pygame.mouse.get_pos(), common.WHITE, 5)

    '''
    # DEBUG - draw monster's rectangles
    for monster in monsters.shared.spritegroup:
        pygame.draw.rect(screen, common.WHITE, monster.rect, width=1)
    '''

    pygame.display.flip()

    common.clock.tick(common.frames_per_second)

request_queue.put("request:logout\n")

if client_socket_thread.has_error:
    client_socket_thread.terminate()

pygame.quit()
