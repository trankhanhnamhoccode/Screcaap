"""Temporarily enqueue and inspect one real RQ capture-processing job."""

import argparse
import sys
from pathlib import Path
from uuid import uuid4

from rq.exceptions import NoSuchJobError
from rq.job import Job

# Support `python scripts/rq_queue_smoke_test.py` from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server.workers.queue import create_capture_processing_queue
from server.workers.rq_processing_queue import RqProcessingQueue

SMOKE_JOB_TARGET = "scripts.rq_smoke_job.echo_capture_id"


def find_smoke_job_ids(queue, prior_ids: set[str], capture_id: str) -> list[str]:
    """Find only new jobs matching this script's random capture ID and target."""
    new_ids = set(queue.get_job_ids()) - prior_ids
    matching_ids = []
    for job_id in new_ids:
        job = Job.fetch(job_id, connection=queue.connection)
        if job.func_name == SMOKE_JOB_TARGET and job.args == (capture_id,):
            matching_ids.append(job_id)
    return matching_ids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-pause", action="store_true", help="Verify and clean up automatically")
    args = parser.parse_args()

    queue = create_capture_processing_queue()
    adapter = RqProcessingQueue(queue, SMOKE_JOB_TARGET)
    capture_id = uuid4()
    payload = str(capture_id)
    prior_ids = set(queue.get_job_ids())

    try:
        adapter.enqueue_capture_processing(capture_id)
        matching_ids = find_smoke_job_ids(queue, prior_ids, payload)
        if len(matching_ids) != 1:
            print("Queue verification: FAIL (expected one new smoke job)")
            return 1

        job = Job.fetch(matching_ids[0], connection=queue.connection)
        print(f"queue name: {queue.name}")
        print(f"RQ job ID: {job.id}")
        print(f"capture_id payload: {payload}")
        if job.origin != queue.name or job.args != (payload,) or job.kwargs != {}:
            print("Queue verification: FAIL")
            return 1
        print("Queue verification: PASS")

        if not args.no_pause:
            input("Inspect this RQ job now. Press Enter to delete it and finish...")
    finally:
        for job_id in find_smoke_job_ids(queue, prior_ids, payload):
            print(f"Deleting smoke job {job_id}...")
            Job.fetch(job_id, connection=queue.connection).delete(remove_from_queue=True)
            if job_id in queue.get_job_ids():
                raise RuntimeError(f"Smoke job {job_id} remains in the queue")
            try:
                Job.fetch(job_id, connection=queue.connection)
            except NoSuchJobError:
                pass
            else:
                raise RuntimeError(f"Smoke job {job_id} still exists in Redis")
            print("Cleanup verified.")

    print("Smoke test complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
