\# Assignment 1 — Learning \& Blocker Journal



\## Project



\*\*Meridian Pivot — Solstice Events Co.\*\*



\## Unfamiliar Technology



\*\*Redis / Memurai and asynchronous message queues\*\*



The unfamiliar technology selected for this sprint was Redis-based message queuing, using Memurai as the Windows-compatible Redis server.



The learning objective was to understand how a print request could be placed onto a queue, processed asynchronously by a worker, and eventually confirmed through a webhook rather than waiting for a synchronous printer response.



\---



\## Learning Objective



The original printer workflow was synchronous:



```text

QR Scan

&#x20;  ↓

Call printer API

&#x20;  ↓

Wait for printer response

&#x20;  ↓

Show Checked In

```



The pivot required an asynchronous architecture:



```text

QR Scan

&#x20;  ↓

Create pending state

&#x20;  ↓

Publish print request

&#x20;  ↓

Redis/Memurai queue

&#x20;  ↓

Worker processes request

&#x20;  ↓

Printer/vendor completes job

&#x20;  ↓

Webhook callback

&#x20;  ↓

Validate job

&#x20;  ↓

Checked In

```



The main learning objective was therefore to understand queues, asynchronous workers, job identifiers, and webhook-based completion.



\---



\# Learning and Blocker Log



\## Blocker 1 — WSL Installation Failure



\### Problem



The initial attempt to use WSL produced:



```text

The Windows Subsystem for Linux is not installed.

```



Running the installation command resulted in:



```text

Forbidden (403).

```



\### Investigation



The system was checked using PowerShell commands to determine the Windows version and build.



The machine reported:



```text

Windows 10 Pro

OS Build 26200

```



The WSL installation route was therefore not immediately usable.



\### Decision



Instead of allowing the environment problem to stop the project, the Redis-compatible Windows server option was changed to \*\*Memurai\*\*.



\### Learning



This demonstrated an important engineering principle:



> When an environmental dependency blocks the planned implementation, find a technically appropriate alternative rather than allowing the blocker to stop the entire sprint.



\---



\## Blocker 2 — Windows Feature Command Error



\### Problem



An attempt was made to inspect multiple Windows optional features with:



```powershell

Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux,VirtualMachinePlatform

```



PowerShell rejected the argument because the parameter expected a single string.



\### Learning



The problem was caused by command syntax rather than by the operating system itself.



This reinforced the importance of reading PowerShell error messages carefully rather than assuming that every failure is an installation failure.



\---



\## Blocker 3 — Memurai Setup



\### Problem



The project required a Redis-compatible queue on Windows.



\### Investigation



Memurai was installed and checked through Windows services.



The service was confirmed to be:



```text

Status: Running

Name: Memurai

DisplayName: Memurai

```



The installation directory was also inspected and confirmed to contain:



```text

memurai.exe

memurai-cli.exe

memurai.conf

```



\### Result



Memurai successfully provided the Redis-compatible backend required for the queue.



\### Learning



A Redis-compatible service can provide the queue infrastructure without requiring the original WSL-based setup.



\---



\## Blocker 4 — Python Indentation Errors



\### Problem



During development, Uvicorn failed to import the application because of Python indentation errors.



One error identified:



```text

IndentationError: unexpected unindent

```



Another occurred around the print-worker code:



```text

IndentationError: unexpected indent

```



\### Investigation



The errors occurred because blocks within the Python application did not have consistent indentation.



\### Resolution



The application was rewritten as a complete, consistently indented file rather than continuing to patch individual lines.



\### Learning



When structural Python errors accumulate, replacing the affected module with a clean, consistently structured version can be safer than repeatedly editing individual indentation levels.



\---



\# Blocker 5 — Transition to Redis Queue



\### Original Approach



The early implementation used an in-memory asynchronous queue.



The pivot required a more realistic message-queue architecture.



\### Change



Redis/Memurai was introduced using a dedicated queue:



```text

meridian\_print\_queue

```



Print requests were published to the queue and a background worker consumed them.



\### Result



The worker successfully produced evidence such as:



```text

Worker received queue job: A008, JOB-ceac9311

```



\### Learning



The queue separates the scan request from the actual printing process.



This means the scan operation does not need to remain blocked while printing completes.



\---



\# Blocker 6 — Webhook Returned 404



\### Problem



The first attempt to simulate the vendor's HTTP webhook produced:



```text

POST /print-confirmation HTTP/1.1" 404 Not Found

```



The vendor simulation completed printing, but the callback could not find the webhook route.



\### Investigation



The application contained two FastAPI application instances.



The webhook route had been registered on one application object, while Uvicorn was running the other application object.



\### Resolution



The application was reorganized so that a single FastAPI application instance owns all routes and the application lifespan.



\### Result



The webhook subsequently returned:



```text

POST /print-confirmation HTTP/1.1" 200 OK

```



and:



```text

Webhook response:

{

&#x20;   "message": "Attendee checked in.",

&#x20;   "attendee\_id": "A008",

&#x20;   "status": "checked\_in",

&#x20;   "job\_id": "JOB-ceac9311"

}

```



\### Learning



A route existing in source code does not guarantee that it belongs to the application instance actually being served.



This was an important lesson in understanding FastAPI application structure.



\---



\# Blocker 7 — Duplicate Check-In Protection



\### Requirement



An attendee who has already checked in must not receive another badge.



\### Test



A008 was scanned once and completed successfully.



A second scan of A008 was then performed.



The application returned HTTP 200 without creating another print job.



No second:



```text

Worker received queue job

```



message was generated.



\### Result



Duplicate protection remained effective after the asynchronous pivot.



\### Learning



The duplicate check must happen before a new print request is published to the queue.



\---



\# Blocker 8 — Incorrect Job ID



\### Requirement



Webhook confirmations may arrive out of order.



A confirmation must therefore be associated with the correct print job.



\### Test



A valid attendee was supplied with an intentionally incorrect job ID:



```text

JOB-WRONG123

```



\### Result



The application returned:



```json

{

&#x20; "message": "Job ID does not match."

}

```



\### Learning



A unique job ID provides an important correlation mechanism between:



\* the attendee,

\* the queued print request,

\* the vendor completion event,

\* and the webhook confirmation.



This prevents an unrelated or stale confirmation from checking in the wrong attendee.



\---



\# Final Working Test



A008 successfully demonstrated the complete asynchronous flow:



```text

POST /scan

&#x20;      ↓

pending

&#x20;      ↓

Redis/Memurai

&#x20;      ↓

Worker

&#x20;      ↓

Vendor simulation

&#x20;      ↓

Printing completed

&#x20;      ↓

HTTP POST /print-confirmation

&#x20;      ↓

HTTP 200 OK

&#x20;      ↓

checked\_in

```



Observed output included:



```text

Worker received queue job: A008, JOB-ceac9311

Vendor received print request: A008, JOB-ceac9311

Vendor completed printing: A008, JOB-ceac9311

Webhook confirmed successful print: A008, JOB-ceac9311

POST /print-confirmation HTTP/1.1" 200 OK

```



\---



\# Key Lessons Learned



\## 1. Separate acceptance from completion



A scan does not mean printing has completed.



The application therefore uses:



```text

pending

```



until the vendor confirms completion.



\## 2. Queues decouple work



Redis allows the scan operation to publish a job without waiting synchronously for printing.



\## 3. Webhooks represent eventual completion



The webhook provides the confirmation that the external printing operation has actually completed.



\## 4. Job IDs are essential



The job ID allows the service to associate a webhook with the correct print request.



\## 5. Duplicate protection must survive the architecture change



Changing from synchronous to asynchronous processing must not remove existing business rules.



The duplicate-scan requirement was therefore retained after the pivot.



\---



\# Autonomy and Troubleshooting Reflection



The project involved several genuine environmental and implementation failures.



The most significant lesson was that troubleshooting required breaking the problem into smaller questions:



1\. Is the required service installed?

2\. Is the service running?

3\. Can Python connect to it?

4\. Can the application start?

5\. Can a request enter the queue?

6\. Can the worker consume it?

7\. Can the simulated vendor complete it?

8\. Can the webhook receive the completion?

9\. Can the application prevent duplicate or invalid confirmations?



This progressively reduced a large system problem into individually testable components.



\---



\# Time Tracking



Exact timestamps were not consistently recorded for every individual troubleshooting event. Rather than inventing measurements, the project records observed completion states and actual technical outcomes.



For future sprints, a stronger measurement process would record:



\* planned duration before starting a task;

\* actual start time;

\* actual completion time;

\* number of failed attempts;

\* final resolution time.



This would make the time-to-completion metric more precise.



\---



\# Final Learning Outcome



The unfamiliar technology was successfully incorporated into a working asynchronous system.



The final prototype demonstrates practical understanding of:



\* Redis/Memurai;

\* message queues;

\* background workers;

\* asynchronous processing;

\* webhook callbacks;

\* job correlation;

\* duplicate protection;

\* failure handling;

\* and architectural adaptation.



The most important outcome was not simply learning Redis syntax. It was learning how to \*\*change an existing working architecture under a fixed deadline while preserving its business requirements\*\*.



