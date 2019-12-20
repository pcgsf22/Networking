import sys
import socket
import packet_tools
import pygame
import queue
import threading
import random
import time
import config

WHITE = 255, 255, 255
BLACK = 0, 0, 0
RED = 255, 0, 0
GREEN = 0, 255, 0
BLUE = 0, 0, 255
ORANGE = 255, 165, 0

UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3

bufsize = 1024


clock = pygame.time.Clock()


class ClientAgent:
    def __init__(self, s, status, ID, name, player_side):
        self.prev_keys = {}
        self.socket = s
        self.ID = ID
        self.name = name
        self.status = 0
        self.listener_queue = queue.Queue()
        self.bufsize = 1024
        self.rows, self.cols = 32, 32
        self.snake_size = 20
        self.surface = pygame.display.set_mode(
            (self.cols * self.snake_size, self.rows * self.snake_size))
        pygame.display.set_caption('Snake Game')
        self.snake_color = [None] * 2
        self.snake_color[0] = GREEN
        self.snake_color[1] = ORANGE
        if player_side == 2:
            self.snake_color[0], self.snake_color[1] = self.snake_color[1], self.snake_color[0]
        self.current_seq = 0
        self.is_quit = False

    def _draw_rect(self, pos, color):
        x, y = pos
        pygame.draw.rect(self.surface, color,
                         (x*self.snake_size+1, y*self.snake_size+1, self.snake_size-2, self.snake_size-2))

    def move(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_quit = True
                pygame.quit()
                return

        keys = pygame.key.get_pressed()
        message = None
        if keys[pygame.K_RIGHT]:
            message = RIGHT
        if keys[pygame.K_LEFT]:
            message = LEFT
        if keys[pygame.K_UP]:
            message = UP
        if keys[pygame.K_DOWN]:
            message = DOWN
        if message is not None:
            msg = packet_tools.pack(3, self.ID.encode(
                "UTF-8"), self.name.encode("UTF-8"), message)
            self.socket.sendto(msg, (host_ip, host_port))

    def listener(self):
        try:
            message = self.socket.recvfrom(self.bufsize)
            self.listener_queue.put_nowait(message)
        except socket.timeout as e:
            pass

    def show_waiting(self):
        self.surface.fill(BLACK)
        font = pygame.font.Font(None, 60)
        text = font.render("waiting for opponent", True, BLUE)
        text_rect = text.get_rect()
        text_x = self.surface.get_width() / 2 - text_rect.width / 2
        text_y = self.surface.get_height() / 2 - text_rect.height / 2
        self.surface.blit(text, [text_x, text_y])
        pygame.display.flip()

    def show_ready(self):
        self.surface.fill(BLACK)
        font = pygame.font.Font(None, 60)
        text = font.render("game is about to start", True, BLUE)
        text_rect = text.get_rect()
        text_x = self.surface.get_width() / 2 - text_rect.width / 2
        text_y = self.surface.get_height() / 2 - text_rect.height / 2
        self.surface.blit(text, [text_x, text_y])
        pygame.display.flip()

    def show_result(self, message):
        self.surface.fill(BLACK)
        font = pygame.font.Font(None, 60)
        text = font.render(message, True, BLUE)
        text_rect = text.get_rect()
        text_x = self.surface.get_width() / 2 - text_rect.width / 2
        text_y = self.surface.get_height() / 2 - text_rect.height / 2
        self.surface.blit(text, [text_x, text_y])
        pygame.display.flip()

    def show_board(self, apple_row, apple_col, snake1, snake2):
        self.surface.fill(BLACK)
        self._draw_rect((apple_col, apple_row), RED)
        for y in range(32):
            cur = 1 << 31
            for x in range(32):
                if cur & snake1[y]:
                    self._draw_rect((x, y), self.snake_color[0])
                if cur & snake2[y]:
                    self._draw_rect((x, y), self.snake_color[1])
                cur = cur >> 1
        pygame.display.flip()

    def render(self):
        pygame.init()
        while True:
            self.move()
            if self.is_quit:
                break
            self.listener()
            message = None
            addr = None
            try:
                message, addr = self.listener_queue.get_nowait()
            except queue.Empty:
                pass
            if message is None:
                continue
            unpacked = packet_tools.unpack(message)
            if unpacked[0] == 4:
                self.show_waiting()
            if unpacked[0] == 5:
                self.show_ready()
            if unpacked[0] == 6:
                if unpacked[1] == 0:
                    self.show_result("It is a draw")
                else:
                    self.show_result(unpacked[2].decode(
                        "UTF-8") + " is winner")
            if unpacked[0] == 7:
                self.show_board(unpacked[2], unpacked[3],
                                unpacked[4], unpacked[5])


def main(argv):
    if len(argv) != 4:
        raise Exception("Incorrect parameters")
    if argv[0] != "create" and argv[0] != "join":
        raise Exception("Incorrect parameters")
    start_param = 0
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if argv[0] == "create":
        start_param = 1
    if argv[0] == "join":
        start_param = 2
    client_port = int(argv[3])
    ID = argv[1]
    name = argv[2]
    s.bind((config.CLIENT_IP, client_port))
    message = packet_tools.pack(start_param, ID.encode(
        "UTF-8"), name.encode("UTF-8"), client_port)
    s.sendto(message, (host_ip, host_port))
    s.settimeout(config.CLIENT_INTERVAL)
    clientAgent = ClientAgent(s, start_param, ID, name, start_param)
    clientAgent.render()


if __name__ == "__main__":
    main(sys.argv[1:])
