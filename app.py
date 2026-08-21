import asyncio
import uuid
from contextlib import asynccontextmanager

import httpx
import redis
from fastapi import FastAPI


# ---------------------------------------------------------
# Redis / Memurai
# ---------------------------------------------------------

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

PRINT_QUEUE = "meridian_print_queue"


# ---------------------------------------------------------
# Attendee state
# ---------------------------------------------------------

attendees = {}


# ---------------------------------------------------------
# Redis worker
# ---------------------------------------------------------

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

        print(
            f"Worker received queue job: "
            f"{attendee_id}, {job_id}"
        )

        await simulate_vendor(
            attendee_id,
            job_id
        )


# ---------------------------------------------------------
# Simulated printer vendor
# ---------------------------------------------------------

async def simulate_vendor(attendee_id: str, job_id: str):

    print(
        f"Vendor received print request: "
        f"{attendee_id}, {job_id}"
    )

    # Simulate printer processing
    await asyncio.sleep(3)

    print(
        f"Vendor completed printing: "
        f"{attendee_id}, {job_id}"
    )

    # Simulate vendor calling our webhook
    webhook_url = (
        "http://127.0.0.1:8000/print-confirmation"
    )

    payload = {
        "attendee_id": attendee_id,
        "job_id": job_id,
        "status": "success"
    }

    async with httpx.AsyncClient() as client:

        response = await client.post(
            webhook_url,
            json=payload
        )

        print(
            f"Webhook response: "
            f"{response.json()}"
        )


# ---------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    worker_task = asyncio.create_task(
        print_worker()
    )

    yield

    worker_task.cancel()


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    lifespan=lifespan
)


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------

@app.get("/")
def home():

    return {
        "message":
        "Meridian Pivot Check-In Service is running!"
    }


# ---------------------------------------------------------
# Scan endpoint
# ---------------------------------------------------------

@app.post("/scan")
async def scan_attendee(attendee_id: str):

    # Prevent duplicate scans
    if attendee_id in attendees:

        return {
            "message":
            "Attendee already has a check-in record.",

            "attendee_id":
            attendee_id,

            "status":
            attendees[attendee_id]["status"],

            "job_id":
            attendees[attendee_id]["job_id"]
        }

    # Create unique print job
    job_id = (
        f"JOB-{uuid.uuid4().hex[:8]}"
    )

    # Create pending attendee record
    attendees[attendee_id] = {
        "status": "pending",
        "job_id": job_id
    }

    # Publish print request to Redis
    redis_client.rpush(
        PRINT_QUEUE,
        f"{attendee_id}|{job_id}"
    )

    return {
        "message":
        "Print request added to queue.",

        "attendee_id":
        attendee_id,

        "status":
        "pending",

        "job_id":
        job_id
    }


# ---------------------------------------------------------
# Vendor webhook
# ---------------------------------------------------------

@app.post("/print-confirmation")
async def print_confirmation(data: dict):

    attendee_id = data["attendee_id"]
    job_id = data["job_id"]
    status = data["status"]

    # Reject unknown attendee
    if attendee_id not in attendees:

        return {
            "message":
            "Unknown attendee."
        }

    attendee = attendees[attendee_id]

    # Reject wrong or out-of-order job
    if attendee["job_id"] != job_id:

        return {
            "message":
            "Job ID does not match."
        }

    # Only successful printing checks attendee in
    if status == "success":

        attendee["status"] = "checked_in"

        print(
            f"Webhook confirmed successful print: "
            f"{attendee_id}, {job_id}"
        )

        return {
            "message":
            "Attendee checked in.",

            "attendee_id":
            attendee_id,

            "status":
            "checked_in",

            "job_id":
            job_id
        }

    return {
        "message":
        "Print was not successful.",

        "attendee_id":
        attendee_id,

        "status":
        attendee["status"],

        "job_id":
        job_id
    }