import socket
import queue
import packet_tools
import threading
import time
from collections import deque
import board
import config


# The server uses event driven model, and communicate with the
# listener thread in an assynchronous way.

class Server:
    def __init__(self):
        self.listener_queue = queue.Queue()
        self.event_queue = deque()
        self.cur_time = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((config.HOST_IP, config.HOST_PORT))
        print('Server started. Waiting for connection...')
        self.bufsize = 1024
        self.ID_dict = {}
        self.interval = config.SERVER_INTERVAL
        self.event = threading.Event()

    def dispatch_message(self, message_pair):
        # print(message_pair)
        message, addr = message_pair
        unpacked = packet_tools.unpack(message)
        if unpacked[1] not in self.ID_dict:
            new_board = board.Board(unpacked[1], self.socket)
            self.ID_dict[unpacked[1]] = new_board
            self.event_queue.append((time.time()+self.interval, new_board))
        self.ID_dict[unpacked[1]].op_queue.append((unpacked, addr))

    def listener(self):
        while True:
            a = self.socket.recvfrom(self.bufsize)
            self.listener_queue.put_nowait(a)
            self.event.set()

    def handler(self):
        """ Event handler of the server"""
        last_time = 0
        while True:
            self.event.wait()
            mssg = None
            try:
                mssg = self.listener_queue.get_nowait()
            except queue.Empty:
                pass
            if mssg:
                self.dispatch_message(mssg)
                # print(mssg)
            cur_time = time.time()
            while len(self.event_queue):
                event_time, event = self.event_queue.popleft()
                if event_time > cur_time:
                    self.event_queue.appendleft((event_time, event))
                    break
                # print(event_time-last_time)
                try:
                    event.handle_event()
                    if event.status != board.EXIT:
                        self.event_queue.append(
                            (event_time+self.interval, event))
                    else:
                        del self.ID_dict[event.id]
                except Exception as e:
                    del self.ID_dict[event.id]
                    print(e)
            if len(self.event_queue) == 0:
                self.event.clear()


def main():
    server = Server()
    threading.Thread(target=server.listener).start()
    server.handler()


if __name__ == "__main__":
    main()
