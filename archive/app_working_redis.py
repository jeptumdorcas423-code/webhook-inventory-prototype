import asyncio
import uuid
from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI


# Temporary attendee storage
attendees = {}


# Connect to Memurai / Redis
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)


# Redis queue name
PRINT_QUEUE = "meridian_print_queue"


async def print_worker():
    while True:
        job = await asyncio.to_thread(
            redis_client.blpop,
            PRINT_QUEUE,
            1
        )

        if job is None:
            continue

        _, job_data = job

        attendee_id, job_id = job_data.split("|", 1)

        print(f"Printing badge for {attendee_id}...")

        # Simulate printer processing time
        await asyncio.sleep(3)

        print(f"Badge printed for {attendee_id}, job {job_id}")


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

    # Create unique print job ID
    job_id = f"JOB-{uuid.uuid4().hex[:8]}"

    # Store attendee
    attendees[attendee_id] = {
        "status": "pending",
        "job_id": job_id
    }

    # Put print job into Redis
    redis_client.rpush(
        PRINT_QUEUE,
        f"{attendee_id}|{job_id}"
    )

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

    # Check attendee exists
    if attendee_id not in attendees:
        return {
            "message": "Unknown attendee."
        }

    attendee = attendees[attendee_id]

    # Make sure webhook belongs to the correct print job
    if attendee["job_id"] != job_id:
        return {
            "message": "Job ID does not match."
        }

    # Only successful printing allows check-in
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