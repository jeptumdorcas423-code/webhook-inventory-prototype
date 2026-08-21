import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI


attendees = {}
print_queue = asyncio.Queue()


async def print_worker():
    while True:
        job = await print_queue.get()

        attendee_id = job["attendee_id"]
        job_id = job["job_id"]

        print(f"Printing badge for {attendee_id}...")

        # Simulate printer processing time
        await asyncio.sleep(3)

        print(f"Badge printed for {attendee_id}, job {job_id}")

        print_queue.task_done()


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = asyncio.create_task(print_worker())

    yield

    worker_task.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/")
def home():
    return {
        "message": "Meridian Pivot Check-In Service is running!"
    }


@app.post("/scan")
async def scan_attendee(attendee_id: str):

    # Prevent duplicate print jobs
    if attendee_id in attendees:
        return {
            "message": "Attendee already has a check-in record.",
            "attendee_id": attendee_id,
            "status": attendees[attendee_id]["status"],
            "job_id": attendees[attendee_id]["job_id"]
        }

    job_id = f"JOB-{uuid.uuid4().hex[:8]}"

    attendees[attendee_id] = {
        "status": "pending",
        "job_id": job_id
    }

    await print_queue.put({
        "attendee_id": attendee_id,
        "job_id": job_id
    })

    return {
        "message": "Print request added to queue.",
        "attendee_id": attendee_id,
        "status": "pending",
        "job_id": job_id
    }


@app.post("/print-confirmation")
def print_confirmation(data: dict):

    attendee_id = data["attendee_id"]
    job_id = data["job_id"]
    status = data["status"]

    if attendee_id not in attendees:
        return {
            "message": "Unknown attendee."
        }

    attendee = attendees[attendee_id]

    if attendee["job_id"] != job_id:
        return {
            "message": "Job ID does not match."
        }

    if status == "success":
        attendee["status"] = "checked_in"

        return {
            "message": "Attendee checked in.",
            "attendee_id": attendee_id,
            "status": "checked_in",
            "job_id": job_id
        }

    return {
        "message": "Print was not successful.",
        "attendee_id": attendee_id,
        "status": attendee["status"],
        "job_id": job_id
    }