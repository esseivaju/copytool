import threading
import time
from queue import Queue, Empty


# Message class that should be sent to the FileWritterWorker
class FileWriterMessage:

    def __init__(self, filename, message):
        self.filename = filename
        self.message = message


# Utility class to synchronize writing from multiple threads to the same file. Performs writing in a separate thread
# To communicate with the thread, messages if FileWriterMessage type should be sent to the queue provided in the constructor.
# This class can only append to a file.
#
# To stop the thread, stop_event needs to be set. The thread will empty the queue before exiting and should be joined before ending the program
class FileWriterWorker(threading.Thread):

    def __init__(self, queue: Queue, stop_event: threading.Event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__msg_queue = queue
        self.__end = stop_event
        # Keeps files open in a <filename, stream> to avoid doing too many syscall opening files
        self.__file_map = dict()

    def run(self):
        while True:
            try:
                message = self.__msg_queue.get(timeout=0.1)
            except Empty:
                if self.__end.is_set():  # --> queue.is_empty() and end.is_set()
                    break
                else:
                    time.sleep(0.1)
            else:
                try:
                    if message.filename not in self.__file_map:
                        self.__file_map[message.filename] = open(message.filename, 'a')
                    self.__file_map[message.filename].write(message.message)
                except Exception:
                    pass
                finally:
                    self.__msg_queue.task_done()
        for f in self.__file_map.values():
            f.close()
