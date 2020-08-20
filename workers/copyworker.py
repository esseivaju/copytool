import threading
import shutil
import hashlib
import os
import pathlib
import logging

from queue import Queue, Empty
from workers.filewritter import FileWritterMessage


class FileCopyMessage:

    def __init__(self, src, dst):
        self.src = src
        self.dst = dst


class FileCopyWorker(threading.Thread):

    def __init__(self, checksum_alg, checksum_file: str, work_queue: Queue, log_queue: Queue, stop_event: threading.Event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__checksum_file = checksum_file
        self.__base_dir = os.path.dirname(self.__checksum_file)
        self.__work_queue = work_queue
        self.__log_queue = log_queue
        self.__end = stop_event
        self.__hash_buffer = memoryview(bytearray(1024 * 128))
        self.__logger = logging.getLogger(self.getName())
        self.__hasher_alg = checksum_alg

    def __compute_file_hash(self, filename):
        hasher = hashlib.new(self.__hasher_alg)
        with open(filename, 'rb', buffering=0) as f:
            for n in iter(lambda: f.readinto(self.__hash_buffer), 0):
                hasher.update(self.__hash_buffer[:n])
        digest = hasher.hexdigest()
        return digest

    def __log_digest(self, digest, digested_file):
        log_to = self.__checksum_file
        rel_path = os.path.relpath(
            os.path.dirname(digested_file), self.__base_dir)
        rel_path = os.path.join(rel_path, os.path.basename(digested_file))
        message = FileWritterMessage(log_to, f"{digest}  {rel_path}\n")
        self.__log_queue.put(message)

    def pre_copy(self, message):
        digest = self.__compute_file_hash(message.src)
        return digest

    def post_copy(self, message):
        digest = self.__compute_file_hash(message.dst)
        self.__log_digest(digest, message.dst)
        return digest

    def run(self):

        while not self.__end.is_set():
            try:
                message = self.__work_queue.get(timeout=0.1)
            except Empty:
                continue
            else:
                digest_pre = self.pre_copy(message)
                cdir = pathlib.Path(os.path.dirname(message.dst))
                try:
                    if not cdir.exists():
                        cdir.mkdir(parents=True, exist_ok=True)
                    shutil.copy(message.src, message.dst)
                except Exception:
                    self.__logger.critical(f"Failed to copy {message.src}, it won't be present in the destination folder. skipping...")
                else:
                    digest_post = self.post_copy(message)
                    if digest_pre == digest_post:
                        self.__logger.info(
                            f"File {message.src} copied successfully.")
                        pass
                    else:
                        self.__logger.critical(
                            f"Source and destination checksum don't match for file {message.src}")
                self.__work_queue.task_done()
