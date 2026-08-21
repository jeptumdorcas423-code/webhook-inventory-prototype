\# Assignment 2 — Scope Delta Analysis



\## Project



\*\*Meridian Pivot — Solstice Events Co.\*\*



\## Pivot Summary



The original Solstice Events requirement used a synchronous badge-printing model.



When a staff member scanned an attendee's QR code, the kiosk service called the printer vendor synchronously and waited for the print operation to succeed before marking the attendee as checked in.



The client then announced a non-negotiable pivot:



> The synchronous printing API was being deprecated and would no longer be available within the required timeframe.



The service therefore had to move to an asynchronous architecture without receiving an extension to the deadline.



The new architecture uses \*\*Redis/Memurai as the message queue\*\*, a background worker to process print requests, and an HTTP webhook to receive the vendor's completion callback.



\---



\# 1. Original Specification



The original workflow was:



```text

QR Scan

&#x20;  ↓

Kiosk calls printer API

&#x20;  ↓

Kiosk waits synchronously

&#x20;  ↓

Printer returns success

&#x20;  ↓

Attendee becomes checked in

```



The key characteristics were:



\* synchronous printer communication;

\* the kiosk waited for the printer response;

\* the attendee was only checked in after the successful response;

\* duplicate scans were prevented;

\* at least three attendees had to be tested.



\---



\# 2. Pivot Requirement



The client required the synchronous printer API to be replaced.



The new requirement was:



```text

QR Scan

&#x20;  ↓

Create pending check-in

&#x20;  ↓

Publish print request to vendor queue

&#x20;  ↓

Return control to kiosk

&#x20;  ↓

Vendor processes print asynchronously

&#x20;  ↓

Vendor calls webhook

&#x20;  ↓

Validate completion

&#x20;  ↓

Attendee becomes checked in

```



The deadline remained unchanged.



The duplicate-scan rule also remained unchanged.



\---



\# 3. Scope Delta



| Area                              | Original                       | After Pivot                              | Change       |

| --------------------------------- | ------------------------------ | ---------------------------------------- | ------------ |

| Printer communication             | Synchronous REST call          | Asynchronous queue                       | \*\*Modified\*\* |

| Queue                             | Not required                   | Redis/Memurai                            | \*\*Added\*\*    |

| Background worker                 | Not required                   | Redis queue worker                       | \*\*Added\*\*    |

| Print completion                  | Immediate response             | Webhook callback                         | \*\*Modified\*\* |

| Check-in state                    | Success after synchronous call | `pending` then `checked\_in`              | \*\*Modified\*\* |

| Job identifier                    | Not central to flow            | Unique `JOB-...` identifier              | \*\*Added\*\*    |

| Duplicate protection              | Required                       | Still required                           | \*\*Retained\*\* |

| Wrong/stale confirmation handling | Not central                    | Job ID validation                        | \*\*Added\*\*    |

| Webhook endpoint                  | Not required                   | `/print-confirmation`                    | \*\*Added\*\*    |

| Vendor simulation                 | Synchronous printer            | Asynchronous simulated vendor            | \*\*Modified\*\* |

| Obsolete synchronous flow         | Active                         | Removed from final active implementation | \*\*Dropped\*\*  |



\---



\# 4. Dropped Components



\## Synchronous printer waiting



The application no longer waits for the printer to complete before returning the initial scan response.



The old conceptual behavior was:



```text

scan → print → wait → success

```



The new behavior is:



```text

scan → queue → pending

```



The printing process occurs independently.



\## Immediate print success as the trigger for check-in



The kiosk no longer treats the initial print request as proof that printing has completed.



Only a valid successful webhook confirmation can transition the attendee to:



```text

checked\_in

```



\---



\# 5. Modified Components



\## Scan workflow



The scan endpoint now creates a pending record:



```text

status = pending

```



and assigns a unique job ID.



Example:



```json

{

&#x20; "attendee\_id": "A008",

&#x20; "status": "pending",

&#x20; "job\_id": "JOB-ceac9311"

}

```



The print request is then placed into Redis.



\---



\## Print processing



Instead of the scan request performing the entire printing operation, a background worker consumes the Redis queue.



The observed flow was:



```text

Worker received queue job

&#x20;      ↓

Vendor received print request

&#x20;      ↓

Vendor completed printing

```



\---



\## Completion handling



The final confirmation occurs through:



```text

POST /print-confirmation

```



The webhook validates:



1\. attendee exists;

2\. job ID matches the attendee's current job;

3\. print status indicates success.



Only then does the attendee become checked in.



\---



\# 6. Added Components



\## Redis/Memurai queue



A Redis-compatible queue was introduced using Memurai.



The queue name is:



```text

meridian\_print\_queue

```



Print jobs are placed onto the queue as:



```text

attendee\_id|job\_id

```



The background worker consumes those jobs.



\---



\## Background worker



The worker continuously waits for print jobs from Redis.



This separates:



\* receiving the scan;

\* queuing the work;

\* processing the print;

\* confirming completion.



\---



\## Webhook endpoint



The application exposes:



```text

POST /print-confirmation

```



The simulated vendor uses HTTP to call this endpoint after the simulated print completes.



The final test produced:



```text

POST /print-confirmation HTTP/1.1" 200 OK

```



\---



\## Job ID validation



Every print request receives a unique identifier such as:



```text

JOB-ceac9311

```



The webhook must contain the matching job ID.



An intentionally incorrect confirmation was tested:



```json

{

&#x20; "attendee\_id": "A008",

&#x20; "job\_id": "JOB-WRONG123",

&#x20; "status": "success"

}

```



The service correctly returned:



```json

{

&#x20; "message": "Job ID does not match."

}

```



This protects the service from incorrectly applying a stale or unrelated confirmation.



\---



\# 7. Architecture Trade-offs



\## Advantages



\### Better responsiveness



The scan operation does not have to wait for the printer.



\### Decoupling



The kiosk and printer processing are separated by the queue.



\### Resilience



A temporary delay in printing does not require the scan request itself to remain open.



\### Explicit state



The `pending` state makes the asynchronous process visible.



\### Correlation



Unique job IDs allow webhook events to be associated with the correct print request.



\---



\# 8. Costs and Trade-offs



The pivot introduced additional complexity.



The system now requires:



\* Redis/Memurai;

\* a background worker;

\* webhook handling;

\* job ID validation;

\* pending-state management.



The original synchronous design was simpler because one request controlled the entire operation.



The asynchronous design is more complex but better matches the new vendor constraint and provides a clearer separation between request acceptance and job completion.



\---



\# 9. Regression Testing



The original business requirements were tested after the pivot.



\## Test 1 — New attendee



A008 was scanned.



Result:



```text

pending

```



The request was placed into Redis.



The worker processed it.



The vendor completed printing.



The webhook returned HTTP 200.



Final state:



```text

checked\_in

```



\*\*Result: PASS\*\*



\---



\## Test 2 — Duplicate scan



A008 was scanned again after successful check-in.



The service returned the existing check-in record.



No new Redis print job was created.



\*\*Result: PASS\*\*



\---



\## Test 3 — Invalid job confirmation



A webhook was sent using:



```text

JOB-WRONG123

```



instead of the attendee's actual job ID.



The service returned:



```text

Job ID does not match.

```



The attendee was not incorrectly checked in.



\*\*Result: PASS\*\*



\---



\## Test 4 — Multiple attendees



Multiple attendees were successfully processed during development, including:



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



This exceeded the minimum requirement of three test attendees.



\*\*Result: PASS\*\*



\---



\# 10. Reprioritized Backlog



\## Dropped



\* Synchronous printer waiting model.

\* Immediate printer response as the completion mechanism.



\## Modified



\* Scan state handling.

\* Print processing.

\* Completion handling.



\## Added



\* Redis/Memurai queue.

\* Background worker.

\* Webhook endpoint.

\* Job IDs.

\* Pending state.

\* Job ID validation.

\* Asynchronous vendor simulation.



\## Retained



\* QR attendee identification.

\* Duplicate protection.

\* Successful printing required before check-in.

\* At least three test attendees.



\---



\# 11. Adaptation Result



The pivot resulted in a genuine architectural change rather than a cosmetic modification.



The final implementation demonstrates:



```text

Synchronous architecture

&#x20;       ↓

Client pivot

&#x20;       ↓

Asynchronous architecture

&#x20;       ↓

Queue

&#x20;       ↓

Worker

&#x20;       ↓

Vendor

&#x20;       ↓

Webhook

&#x20;       ↓

Validated completion

```



The project therefore satisfies the central requirement of the pivot: the team adapted the implementation to a new non-negotiable requirement while preserving the original business rules.



\---



\# 12. Final Scope Assessment



\### Adaptation completeness



\*\*PASS\*\*



The new asynchronous specification is implemented and tested.



\### Architectural integrity



\*\*PASS\*\*



The solution has clear separation between scan handling, queueing, processing, and completion confirmation.



\### Trade-off documentation



\*\*PASS\*\*



The pivot increased architectural complexity but removed the dependency on synchronous printer completion.



\### Regression safety



\*\*PASS\*\*



Duplicate protection and successful check-in behavior were tested after the pivot.



\---



\## Final Conclusion



The pivot changed the system from a tightly coupled synchronous printer workflow into an asynchronous event-driven workflow.



The final implementation demonstrates that the team did not simply rename the old functionality. The printing lifecycle, state model, queueing mechanism, completion mechanism, and failure validation were all changed to support the new client requirement.



The resulting system provides a practical prototype of an asynchronous badge-printing workflow suitable for the Solstice Events scenario.



