"""Inspect or delete one explicitly selected capture-processing RQ job."""

import argparse
import sys
from pathlib import Path
from uuid import UUID

from redis.exceptions import RedisError
from rq.exceptions import NoSuchJobError
from rq.job import Job, JobStatus

# Support `python scripts/rq_queue_inspect.py` from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server.workers.queue import create_capture_processing_queue


def fetch_job(queue, job_id: str) -> Job | None:
    try:
        return Job.fetch(job_id, connection=queue.connection)
    except NoSuchJobError:
        print(f"Job {job_id} was not found.", file=sys.stderr)
        return None


def list_jobs(queue) -> int:
    job_ids = queue.get_job_ids()
    print(f"Queue: {queue.name}")
    print(f"Queued jobs: {len(job_ids)}")
    print("Job IDs:")
    for job_id in job_ids:
        print(f"  {job_id}")
    if not job_ids:
        print("  (none)")
    return 0


def show_job(queue, job_id: str) -> int:
    job = fetch_job(queue, job_id)
    if job is None:
        return 1
    if job.origin != queue.name:
        print(f"Job {job_id} belongs to queue {job.origin}, not {queue.name}.", file=sys.stderr)
        return 1

    print(f"Job ID: {job.id}")
    print(f"Status: {job.get_status().value}")
    print(f"Queue: {job.origin}")
    print(f"Function target: {job.func_name}")
    if len(job.args) == 1 and isinstance(job.args[0], str):
        try:
            UUID(job.args[0])
        except ValueError:
            print("Args: (non-UUID string; omitted)")
        else:
            print(f"Args: {job.args!r}")
            print(f"capture_id: {job.args[0]}")
    else:
        print("Args: (unexpected payload; omitted)")
    return 0


def delete_job(queue, job_id: str) -> int:
    job = fetch_job(queue, job_id)
    if job is None:
        return 1
    if job.origin != queue.name or job_id not in queue.get_job_ids():
        print(f"Job {job_id} is not queued in {queue.name}; nothing deleted.", file=sys.stderr)
        return 1
    if job.get_status() != JobStatus.QUEUED:
        print(f"Job {job_id} is not queued; nothing deleted.", file=sys.stderr)
        return 1

    print(f"Deleting job {job_id} from {queue.name}...")
    job.delete(remove_from_queue=True)
    if job_id in queue.get_job_ids():
        print(f"Job {job_id} remains in the queue.", file=sys.stderr)
        return 1
    try:
        Job.fetch(job_id, connection=queue.connection)
    except NoSuchJobError:
        print(f"Deleted and verified job {job_id}.")
        return 0
    print(f"Job {job_id} still exists in Redis.", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="Show queued job IDs")
    commands.add_parser("show", help="Show one job").add_argument("job_id")
    commands.add_parser("delete", help="Delete one queued job").add_argument("job_id")
    args = parser.parse_args()

    queue = create_capture_processing_queue()
    try:
        if args.command == "list":
            return list_jobs(queue)
        if args.command == "show":
            return show_job(queue, args.job_id)
        return delete_job(queue, args.job_id)
    except RedisError as exc:
        print(f"Redis/RQ operation failed: {type(exc).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
