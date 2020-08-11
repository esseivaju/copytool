import threading
import hashlib
import os
import logging

from queue import Queue, Empty


class ChecksumMessage:

    def __init__(self, hash_entry):
        self.hash_entry = hash_entry


class ChecksumWorker(threading.Thread):

    def __init__(self, base_directory: str, work_queue: Queue, stop_event: threading.Event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__base_dir = base_directory
        self.__work_queue = work_queue
        self.__end = stop_event
        self.__hash_buffer = memoryview(bytearray(1024 * 128))
        self.__logger = logging.getLogger(self.getName())

    def __compute_file_hash(self, filename):
        hasher = hashlib.sha3_512()
        with open(filename, 'rb', buffering=0) as f:
            for n in iter(lambda: f.readinto(self.__hash_buffer), 0):
                hasher.update(self.__hash_buffer[:n])
        digest = hasher.hexdigest()
        return digest

    def run(self):

        while not self.__end.is_set():
            try:
                message = self.__work_queue.get(timeout=0.1)
            except Empty:
                continue
            else:
                line = message.hash_entry
                old_checksum, filename = line.rstrip('\n').split("  ", 1)
                f_abs = os.path.join(self.__base_dir, filename)
                try:
                    current_checksum = self.__compute_file_hash(f_abs)
                except FileNotFoundError:
                    self.__logger.critical(f"{f_abs}: File doesn't exist")
                else:
                    if current_checksum == old_checksum:
                        self.__logger.info(f"{f_abs}: Checksum OK")
                    else:
                        self.__logger.critical(f"{f_abs}: Checksum mismatch")
                self.__work_queue.task_done()
