"""Utilities"""

from __future__ import annotations

from multiprocessing import Queue as mp_Queue
from queue import Empty, Queue
from typing import Union


def clear_queue(queue: Union[Queue, mp_Queue]):
    """Purges the given queue"""
    while True:
        try:
            queue.get(timeout=0.005)
        except Empty:
            break


# Constants for escape sequences
ESC = "\033"
CSI = f"{ESC}["
COLOR_RESET = f"{CSI}m"
