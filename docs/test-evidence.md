\# Final Test Evidence — Meridian Pivot



\## Solstice Events Co. — Asynchronous Check-In Service



This document records the final functional tests performed after the synchronous-to-asynchronous pivot.



\---



\# Test 1 — Application Startup



\### Objective



Confirm that the FastAPI application and background worker start successfully.



\### Command



```powershell

uvicorn app:app --reload

```



\### Result



The application reported:



```text

Uvicorn running on http://127.0.0.1:8000

Started server process

Waiting for application startup.

Application startup complete.

```



\### Status



\*\*PASS\*\*



\---



\# Test 2 — New Attendee Scan



\### Objective



Confirm that a new attendee is accepted and placed into the `pending` state.



\### Attendee



```text

A008

```



\### Response



```json

{

&#x20; "message": "Print request added to queue.",

&#x20; "attendee\_id": "A008",

&#x20; "status": "pending",

&#x20; "job\_id": "JOB-ceac9311"

}

```



\### Expected Behavior



The attendee must not immediately become `checked\_in`.



The application must create a pending record and place the print request onto the queue.



\### Status



\*\*PASS\*\*



\---



\# Test 3 — Redis/Memurai Queue Processing



\### Objective



Confirm that the asynchronous worker receives the queued print request.



\### Observed Output



```text

Worker received queue job: A008, JOB-ceac9311

```



\### Expected Behavior



The background worker consumes the print request without requiring the original scan request to perform the printing synchronously.



\### Status



\*\*PASS\*\*



\---



\# Test 4 — Vendor Processing



\### Objective



Confirm that the simulated printer vendor receives and processes the queued job.



\### Observed Output



```text

Vendor received print request: A008, JOB-ceac9311

Vendor completed printing: A008, JOB-ceac9311

```



\### Status



\*\*PASS\*\*



\---



\# Test 5 — HTTP Webhook Callback



\### Objective



Confirm that the simulated vendor calls the application's webhook after printing completes.



\### Endpoint



```text

POST /print-confirmation

```



\### Observed Output



```text

POST /print-confirmation HTTP/1.1" 200 OK

```



\### Webhook Response



```json

{

&#x20; "message": "Attendee checked in.",

&#x20; "attendee\_id": "A008",

&#x20; "status": "checked\_in",

&#x20; "job\_id": "JOB-ceac9311"

}

```



\### Expected Behavior



Only after successful print confirmation should the attendee become checked in.



\### Status



\*\*PASS\*\*



\---



\# Test 6 — Complete Asynchronous Flow



\### Objective



Verify that the entire pivot architecture works from scan through completion.



\### Observed Sequence



```text

POST /scan

&#x20;    ↓

pending

&#x20;    ↓

Redis/Memurai

&#x20;    ↓

Worker received queue job

&#x20;    ↓

Vendor received print request

&#x20;    ↓

Vendor completed printing

&#x20;    ↓

HTTP webhook

&#x20;    ↓

200 OK

&#x20;    ↓

checked\_in

```



\### Status



\*\*PASS\*\*



\---



\# Test 7 — Duplicate Scan Protection



\### Objective



Confirm that an attendee who has already checked in cannot receive a second badge.



\### Attendee



```text

A008

```



A008 was scanned once and successfully checked in.



A second scan was then submitted.



\### Observed Behavior



The second request returned HTTP 200 without creating another print job.



The PowerShell output did not show another:



```text

Worker received queue job: A008

```



\### Expected Behavior



No second print request should be created.



\### Status



\*\*PASS\*\*



\---



\# Test 8 — Invalid Job ID



\### Objective



Confirm that a webhook confirmation with an incorrect job ID cannot incorrectly check in an attendee.



\### Test Payload



```json

{

&#x20; "attendee\_id": "A008",

&#x20; "job\_id": "JOB-WRONG123",

&#x20; "status": "success"

}

```



\### Response



```json

{

&#x20; "message": "Job ID does not match."

}

```



\### Expected Behavior



The confirmation must be rejected because the job does not belong to the attendee's current print request.



\### Status



\*\*PASS\*\*



\---



\# Test 9 — Multiple Attendees



\### Objective



Confirm that the service can process at least three attendees as required by the assignment.



\### Attendees Tested



```text

A001

A002

A003

A004

A005

A006

A007

A008

```



The project therefore exceeded the minimum requirement of three test attendees.



\### Status



\*\*PASS\*\*



\---



\# Regression Summary



| Requirement                   | Final Result |

| ----------------------------- | ------------ |

| Application starts            | PASS         |

| New attendee accepted         | PASS         |

| Pending state created         | PASS         |

| Queue processing              | PASS         |

| Asynchronous worker           | PASS         |

| Vendor processing             | PASS         |

| Webhook callback              | PASS         |

| Successful print → checked in | PASS         |

| Duplicate protection          | PASS         |

| Job ID validation             | PASS         |

| At least three attendees      | PASS         |



\---



\# Final Verification



The final implementation satisfies the central pivot requirement:



```text

The kiosk does not treat the initial scan as proof

that printing has completed.



The attendee remains pending until a valid

successful webhook confirmation is received.

```



The original duplicate-scan business rule remains functional after the architectural change.



\## Overall Test Result



\*\*PASS — Final asynchronous prototype verified.\*\*



