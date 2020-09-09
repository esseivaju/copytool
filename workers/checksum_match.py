import threading
import hashlib
import os
import logging
import time
from queue import Queue, Empty


# Message sent to the ChecksumWorker. This should contain one line of the checksum file.
class ChecksumMessage:

    def __init__(self, hash_entry):
        self.hash_entry = hash_entry


# Checks the integrity of files. Messages are received from the work_queue provided in the constructor.
# The message should contain a line of the checksum file formatted as '<hash><space><space><filepath>' e.g. '04e2  file.txt'
# To stop the thread, stop_event needs to be set. The thread will empty the queue before exiting and should be joined before ending the program
class ChecksumWorker(threading.Thread):

    def __init__(self, checksum_alg, base_directory: str, work_queue: Queue, stop_event: threading.Event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__base_dir = base_directory
        self.__work_queue = work_queue
        self.__end = stop_event
        self.__hash_buffer = memoryview(bytearray(1024 * 128))
        self.__logger = logging.getLogger(self.getName())
        self.__hasher_alg = checksum_alg

    # Compute the hash value of a file and returns it
    def __compute_file_hash(self, filename):
        hasher = hashlib.new(self.__hasher_alg)
        with open(filename, 'rb', buffering=0) as f:
            for n in iter(lambda: f.readinto(self.__hash_buffer), 0):
                hasher.update(self.__hash_buffer[:n])
        digest = hasher.hexdigest()
        return digest

    def run(self):

        while True:
            try:
                # try to get some work, if the queue is empty, retry.
                message = self.__work_queue.get(timeout=0.1)
            except Empty:
                if self.__end.is_set():  # --> queue.is_empty() and end.is_set()
                    break
                else:
                    time.sleep(0.1)
            else:
                # parse the line
                line = message.hash_entry
                old_checksum, filename = line.rstrip('\n').split("  ", 1)
                f_abs = os.path.join(self.__base_dir, filename)
                try:
                    # compute the file hash
                    current_checksum = self.__compute_file_hash(f_abs)
                except FileNotFoundError:
                    self.__logger.critical(f"{f_abs}: File doesn't exist")
                except Exception:
                    self.__logger.critical(f"Failed to compute hash for file {f_abs}. It is most likely corrupted")
                else:
                    # check that both match
                    if current_checksum == old_checksum:
                        self.__logger.info(f"{f_abs}: Checksum OK")
                    else:
                        self.__logger.critical(f"{f_abs}: Checksum mismatch")
                finally:
                    self.__work_queue.task_done()
