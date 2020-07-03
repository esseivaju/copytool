import threading

from queue import Queue, Empty


class FileWritterMessage:

    def __init__(self, filename, message):
        self.filename = filename
        self.message = message


class FileWritterWorker(threading.Thread):

    def __init__(self, queue: Queue, stop_event: threading.Event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__msg_queue = queue
        self.__end = stop_event

    def run(self):
        while not self.__end.is_set():
            try:
                message = self.__msg_queue.get(timeout=0.1)
            except Empty:
                continue
            else:
                with open(message.filename, 'a') as f:
                    f.write(message.message)
                self.__msg_queue.task_done()
