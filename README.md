## Live Deployment



- **Live Application:** https://meridian-pivot-dvwn.onrender.com

- **API Documentation:** https://meridian-pivot-dvwn.onrender.com/docs

- **OpenAPI Definition:** https://meridian-pivot-dvwn.onrender.com/openapi.json

- **GitHub Repository:** https://github.com/jeptumdorcas423-code/webhook-inventory-prototype



# Meridian Pivot — Asynchronous Event Check-In Service



## Solstice Events Co.



An asynchronous event check-in prototype developed for the **Meridian Pivot Simulation**.



The project demonstrates how an event check-in kiosk can adapt from a synchronous badge-printing workflow to an asynchronous architecture using **Redis/Memurai, a background worker, and an HTTP webhook**.



---



# 1. Scenario



Solstice Events Co. operates a multi-day technology conference.



When staff scan an attendee's QR code, the kiosk must request a badge print.



The original specification required the kiosk to communicate with the printer synchronously.



The client then announced a non-negotiable pivot:



> The synchronous printer API was being deprecated.



The service therefore had to move to an asynchronous model without extending the deadline.



---



# 2. Final Architecture



```text

&#x20;                  QR Scan

&#x20;                     │

&#x20;                     ▼

&#x20;             ┌───────────────┐

&#x20;             │    FastAPI    │

&#x20;             │   /scan       │

&#x20;             └───────┬───────┘

&#x20;                     │

&#x20;                 status:

&#x20;                 pending

&#x20;                     │

&#x20;                     ▼

&#x20;             ┌───────────────┐

&#x20;             │ Redis/Memurai │

&#x20;             │ Print Queue   │

&#x20;             └───────┬───────┘

&#x20;                     │

&#x20;                     ▼

&#x20;             ┌───────────────┐

&#x20;             │ Background    │

&#x20;             │ Worker        │

&#x20;             └───────┬───────┘

&#x20;                     │

&#x20;                     ▼

&#x20;             ┌───────────────┐

&#x20;             │ Simulated     │

&#x20;             │ Printer Vendor│

&#x20;             └───────┬───────┘

&#x20;                     │

&#x20;                HTTP callback

&#x20;                     │

&#x20;                     ▼

&#x20;             ┌───────────────┐

&#x20;             │ /print-       │

&#x20;             │ confirmation  │

&#x20;             └───────┬───────┘

&#x20;                     │

&#x20;               validate job ID

&#x20;                     │

&#x20;                     ▼

&#x20;                CHECKED IN

```



---



# 3. Key Technologies



* Python

* FastAPI

* Uvicorn

* Redis

* Memurai

* HTTPX

* PowerShell

* Swagger/OpenAPI



---



# 4. Why Redis/Memurai?



Redis provides a message-queue mechanism that allows print requests to be separated from the scan request.



Memurai was used because the development environment was Windows-based.



The queue used by the application is:



```text

meridian\_print\_queue

```



---



# 5. API Endpoints



## `GET /`



Health check.



Example response:



```json

{

&#x20; "message": "Meridian Pivot Check-In Service is running!"

}

```



---



## `POST /scan`



Creates a print request for an attendee.



Example:



```text

POST /scan?attendee\_id=A008

```



Initial response:



```json

{

&#x20; "message": "Print request added to queue.",

&#x20; "attendee\_id": "A008",

&#x20; "status": "pending",

&#x20; "job\_id": "JOB-ceac9311"

}

```



The attendee remains `pending` until successful print confirmation.



---



## `POST /print-confirmation`



Webhook used by the simulated printer vendor.



Example payload:



```json

{

&#x20; "attendee\_id": "A008",

&#x20; "job\_id": "JOB-ceac9311",

&#x20; "status": "success"

}

```



Successful response:



```json

{

&#x20; "message": "Attendee checked in.",

&#x20; "attendee\_id": "A008",

&#x20; "status": "checked\_in",

&#x20; "job\_id": "JOB-ceac9311"

}

```



---



# 6. Duplicate Protection



An attendee who already has a check-in record cannot create another print request.



For example, scanning A008 again after successful completion returns the existing state instead of publishing another print job.



This prevents duplicate badge printing.



---



# 7. Job ID Protection



Every print request receives a unique job ID.



Example:



```text

JOB-ceac9311

```



The webhook must provide the same job ID.



If a different job ID is supplied, the request is rejected:



```json

{

&#x20; "message": "Job ID does not match."

}

```



This protects the system against stale, incorrect, or out-of-order confirmations.



---



# 8. Installation



## Requirements



Python 3.13 or compatible Python version.



Memurai must be installed and running as a Windows service.



Verify the Memurai service with:



```powershell

Get-Service | Where-Object {

&#x20;   $\_.Name -like "*Memurai*" -or

&#x20;   $\_.DisplayName -like "*Memurai*"

}

```



Expected:



```text

Status   Name      DisplayName

Running  Memurai   Memurai

```



---



# 9. Install Python Dependencies



From the project directory:



```powershell

python -m pip install -r requirements.txt

```



---



# 10. Start the Application



Run:



```powershell

uvicorn app:app --reload

```



Expected output includes:



```text

Uvicorn running on http://127.0.0.1:8000

Application startup complete.

```



---



# 11. Open Swagger



Open:



```text

http://127.0.0.1:8000/docs

```



Swagger provides an interactive interface for testing the API.



---



# 12. End-to-End Test



Use:



```text

POST /scan

```



with a new attendee, for example:



```text

A008

```



The immediate response should show:



```text

status: pending

```



The worker then processes the queued request.



The simulated vendor completes the print.



The vendor sends an HTTP callback to:



```text

POST /print-confirmation

```



The attendee then becomes:



```text

checked\_in

```



---



# 13. Evidence From Final Testing



A008 successfully completed the final asynchronous flow.



Observed sequence:



```text

Worker received queue job: A008, JOB-ceac9311

Vendor received print request: A008, JOB-ceac9311

Vendor completed printing: A008, JOB-ceac9311

Webhook confirmed successful print: A008, JOB-ceac9311

POST /print-confirmation HTTP/1.1" 200 OK

```



Final webhook response:



```json

{

&#x20; "message": "Attendee checked in.",

&#x20; "attendee\_id": "A008",

&#x20; "status": "checked\_in",

&#x20; "job\_id": "JOB-ceac9311"

}

```



---



# 14. Regression Tests



The following tests were completed after the pivot.



| Test                                           | Result |

| ---------------------------------------------- | ------ |

| New attendee enters `pending` state            | PASS   |

| Redis queue receives request                   | PASS   |

| Worker consumes request                        | PASS   |

| Simulated vendor completes print               | PASS   |

| Webhook callback succeeds                      | PASS   |

| Successful print changes state to `checked\_in` | PASS   |

| Duplicate scan prevented                       | PASS   |

| Wrong job ID rejected                          | PASS   |

| More than three attendees tested               | PASS   |



---



# 15. Project Files



```text

meridian-pivot/

│

├── app.py

├── requirements.txt

├── README.md

│

├── docs/

│   ├── learning-blocker-journal.md

│   ├── scope-delta-analysis.md

│   └── test-evidence.md

│

└── archive/

&#x20;   └── app\_backup\_asyncio.py

```



---



# 16. Pivot Documentation



Additional documentation is available in:



* `docs/learning-blocker-journal.md`

* `docs/scope-delta-analysis.md`

* `docs/test-evidence.md`



These documents explain the learning process, troubleshooting, architectural change, trade-offs, and regression testing.



---



# 17. Important Prototype Limitation



This is a local simulation of the vendor's asynchronous printing system.



The simulated vendor runs locally and calls the webhook over HTTP after simulating print completion.



In a production deployment, the external badge-printer vendor would provide the real queue and would call the deployed webhook endpoint.



---



# 18. Final Outcome



The final system successfully demonstrates the required asynchronous pivot:



```text

Scan

&#x20;↓

Pending

&#x20;↓

Redis/Memurai queue

&#x20;↓

Background worker

&#x20;↓

Printer/vendor processing

&#x20;↓

Webhook callback

&#x20;↓

Job validation

&#x20;↓

Checked In

```



The original business requirement of preventing duplicate badge printing remains intact after the architectural change.




