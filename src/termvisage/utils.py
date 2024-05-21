"""Utilities"""

from __future__ import annotations

from multiprocessing import Queue as mp_Queue
from queue import Empty, Queue


def clear_queue(queue: Queue | mp_Queue):
    """Purges the given queue"""
    while True:
        try:
            # For multiprocessing queues, it can take a little while for items put
            # from one process to appear in another process. Hence, the timeout.
            # It results in a negligible cost, only when the queue is empty.
            queue.get(timeout=0.005)
        except Empty:
            break


def clear_queue_and_stop_loading(queue: Queue | mp_Queue):
    """Purges the given queue, stopping a loading operation for every item."""
    from .notify import stop_loading

    while True:
        try:
            # For multiprocessing queues, it can take a little while for items put
            # from one process to appear in another process. Hence, the timeout.
            # It results in a negligible cost, only when the queue is empty.
            queue.get(timeout=0.005)
        except Empty:
            break
        else:
            stop_loading()
