"""Start an empty RQ worker for local development."""

import sys

from rq import SpawnWorker, Worker

from server.workers.queue import create_queue


def main() -> None:
    queue = create_queue()
    worker_type = SpawnWorker if sys.platform == "win32" else Worker
    worker_type([queue], connection=queue.connection).work()


if __name__ == "__main__":
    main()
