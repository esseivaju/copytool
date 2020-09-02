import threading
import shutil
import hashlib
import os
import pathlib
import logging
import time

from queue import Queue, Empty
from workers.filewriter import FileWriterMessage


# Message sent to the FileCopyWorker, should contain absolute path to the src file as well as absolute path to the destination file
class FileCopyMessage:

    def __init__(self, src, dst):
        self.src = src
        self.dst = dst


# Worker which performs copy of files. A hash will be computed before (on the src file) and after (on the dst file) the copy to verify the integrity of copied data
# Copy can be skipped if the destination file already exist and was more recently modified than the src file.
#
# Reads from the work_queue provided in the constructor and uses the log_queue amd FileWriter to write to file. 
#
# To stop the thread, stop_event needs to be set. The thread will empty the queue before exiting and should be joined before ending the program
class FileCopyWorker(threading.Thread):

    def __init__(self, checksum_alg, checksum_file: str, csv_file: str, full_copy: bool, work_queue: Queue, log_queue: Queue, stop_event: threading.Event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__checksum_file = checksum_file
        self.__csv_file = csv_file
        self.__full_copy = full_copy
        self.__base_dir = os.path.dirname(self.__checksum_file)
        self.__work_queue = work_queue
        self.__log_queue = log_queue
        self.__end = stop_event
        self.__hash_buffer = memoryview(bytearray(1024 * 128))
        self.__logger = logging.getLogger(self.getName())
        self.__hasher_alg = checksum_alg

    # Compute hash vaule of the file and returns it
    def __compute_file_hash(self, filename):
        hasher = hashlib.new(self.__hasher_alg)
        with open(filename, 'rb', buffering=0) as f:
            for n in iter(lambda: f.readinto(self.__hash_buffer), 0):
                hasher.update(self.__hash_buffer[:n])
        digest = hasher.hexdigest()
        return digest

    # log a hash entry '<hash><space><space><filepath>' to the checksum file as well as a csv summary file.
    def __log_digest(self, digest, digested_file):
        rel_path = os.path.relpath(
            os.path.dirname(digested_file), self.__base_dir)
        rel_path = os.path.join(rel_path, os.path.basename(digested_file))
        message = FileWriterMessage(self.__checksum_file, f"{digest}  {rel_path}\n")
        self.__log_queue.put(message)
        csv_message = FileWriterMessage(self.__csv_file, f"{rel_path},{digest}\n")
        self.__log_queue.put(csv_message)

    # Work to perform before the copy, compute the hash of the original file
    def pre_copy(self, message):
        digest = self.__compute_file_hash(message.src)
        return digest

    # Work to perform after the copy, compute the hash of the destination file file
    def post_copy(self, message):
        digest = self.__compute_file_hash(message.dst)
        self.__log_digest(digest, message.dst)
        return digest

    def run(self):

        while True:
            try:
                # tries to get a file to copy
                message = self.__work_queue.get(timeout=0.1)
            except Empty:
                if self.__end.is_set():  # --> queue.is_empty() and end.is_set()
                    break
                else:
                    time.sleep(0.1)
            else:
                try:
                    # creates dst dir if necessary, compute src hash
                    cdir = pathlib.Path(os.path.dirname(message.dst))
                    digest_pre = self.pre_copy(message)
                    if not cdir.exists():
                        cdir.mkdir(parents=True, exist_ok=True)

                    # if the destinaton already exists, check which of the src and dst is more recent.
                    # If the destination is more recent -> skip the copy
                    if os.path.isfile(message.dst) and not self.__full_copy:
                        stat_src = os.lstat(message.src)
                        stat_dst = os.lstat(message.dst)
                        if stat_src.st_mtime_ns > stat_dst.st_mtime_ns:
                            shutil.copy(message.src, message.dst)
                        else:
                            self.__logger.info(f"destination file {message.dst} modified after original file, skipping...")
                    else:
                        shutil.copy(message.src, message.dst)
                except shutil.SpecialFileError:
                    self.__logger.warning(f" {message.src} is a special file and cannot copier")
                except shutil.SameFileError:
                    self.__logger.warning(f"{message.src} Src and dst are the same files, skipping...")
                except Exception:
                    self.__logger.critical(f"Failed to copy {message.src}, it won't be present in the destination folder. skipping...")
                else:
                    try:
                        # if we successfully copied the file, compute the hash of the destination file.
                        digest_post = self.post_copy(message)
                    except Exception:
                        self.__logger.critical(
                            f"Failed to compute hash for destination file {message.dst}. It is most likely corrupted")
                    else:
                        # compare the hash of the source and destination files
                        if digest_pre == digest_post:
                            self.__logger.info(
                                f"File {message.src} copied successfully.")
                        else:
                            self.__logger.critical(
                                f"Source and destination checksum don't match for file {message.src}")
                self.__work_queue.task_done()
