import packet_tools
import time
import random
from collections import deque
from snake import Snake

HOSTED = 1
REQUESTED = 2
START = 3
RUNNING = 4
BROADCAST_RESULT = 5
EXIT = 6


class Board:
    def __init__(self, id, s):
        self.socket = s
        self.id = id
        self.name = [None] * 2
        self.send_addr = [None] * 2
        self.status = 0

        self.rows = 32
        self.cols = 32

        snake_start_pos = self._choose_random_pos()
        self.snake1 = Snake(snake_start_pos, self.rows, self.cols)
        snake2_pos = self._choose_random_pos()
        while snake_start_pos == snake2_pos:
            snake2_pos = self._choose_random_pos()
        self.snake2 = Snake(snake2_pos, self.rows, self.cols)
        self.apple = self._choose_random_pos()
        while self.apple == snake_start_pos or self.apple == snake2_pos:
            self.apple = self._choose_random_pos()

        self.op_queue = deque()
        self.name_to_id = {}
        self.player_move = [0] * 2
        self.time = time.time()
        self.time_count = 20
        self.seq = 0
        self.winner = 0

        self.status_handler = [None] * 6
        self.status_handler[0] = lambda: None
        self.status_handler[HOSTED] = self.status_handler[REQUESTED] = self.handle_begin
        self.status_handler[START] = self.handle_ready
        self.status_handler[RUNNING] = self.handle_running
        self.status_handler[BROADCAST_RESULT] = self.handle_end

    def _choose_random_pos(self):
        x = random.randrange(self.cols)
        y = random.randrange(self.rows)
        return x, y

    def run_once(self):
        if self.status >= BROADCAST_RESULT:
            return
        self.snake1._update_dir(self.player_move[0])
        self.snake2._update_dir(self.player_move[1])
        old_head1 = self.snake1.head()
        old_head2 = self.snake2.head()
        if not self.snake1.move(self.apple):
            self.winner |= 2
        if not self.snake2.move(self.apple):
            self.winner |= 1
        col_diff = (old_head1[0] - old_head2[0]) * \
            (self.snake1.head()[0]-self.snake2.head()[0])
        row_diff = (old_head1[1] - old_head2[1]) * \
            (self.snake1.head()[1]-self.snake2.head()[1])
        if col_diff == -1 or row_diff == -1:
            self.winner = 3
        if self.snake1.head() in self.snake2.body:
            self.winner |= 2
        if self.snake2.head() in self.snake1.body:
            self.winner |= 1
        if self.winner:
            self.status = BROADCAST_RESULT
        if self.snake1.head() == self.apple or self.snake2.head():
            while self.apple in self.snake1.body or self.apple in self.snake2.body:
                self.apple = self._choose_random_pos()

    def read_opeartion(self):
        while len(self.op_queue) > 0:
            cur, addr = self.op_queue.popleft()
            message_type, ID, name, number = cur
            if self.status < START and message_type < 3:
                if self.status & message_type:
                    continue
                self.status |= message_type
                self.send_addr[message_type-1] = addr
                self.name[message_type-1] = name
                self.name_to_id[name] = message_type-1
                continue
            if self.status == START:
                continue
            if self.status == RUNNING and message_type == 3:
                self.player_move[self.name_to_id[name]] = number

    def handle_running(self):
        packed = packet_tools.pack(
            7, self.seq, self.apple[1], self.apple[0], self.snake1.body, self.snake2.body)
        # print(packed)
        self.socket.sendto(packed, self.send_addr[0])
        self.socket.sendto(packed, self.send_addr[1])
        self.seq += 1
        self.seq %= 256
        self.run_once()

    def handle_begin(self):
        if self.send_addr[0]:
            self.socket.sendto(packet_tools.pack(4), self.send_addr[0])
        if self.send_addr[1]:
            self.socket.sendto(packet_tools.pack(4), self.send_addr[1])

    def handle_ready(self):
        self.socket.sendto(packet_tools.pack(5), self.send_addr[0])
        self.socket.sendto(packet_tools.pack(5), self.send_addr[1])
        self.time_count -= 1
        if self.time_count == 0:
            self.status = 4

    def handle_end(self):
        print("End")
        result = 1
        winner_name = b""
        if self.winner == 3:
            result = 0
        else:
            winner_name = self.name[self.winner-1]
        message = packet_tools.pack(6, result, winner_name)
        self.socket.sendto(packet_tools.pack(
            6, result, winner_name), self.send_addr[0])
        self.socket.sendto(packet_tools.pack(
            6, result, winner_name), self.send_addr[1])
        self.status = EXIT

    def handle_event(self):
        self.read_opeartion()
        self.status_handler[self.status]()
