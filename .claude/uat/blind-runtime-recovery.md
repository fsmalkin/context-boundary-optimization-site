# Certified blind runtime recovery

## Five whys

1. The second provider-free UAT attempt stopped because the heartbeat worker reported that its renewed lease no longer matched the launcher acquisition.
2. The launcher ran under PowerShell 7.6.4, whose `ConvertFrom-Json` converts ISO timestamps into `DateTime` values before the heartbeat compares them with the original ISO strings.
3. The shared lane-lock modules assume that JSON timestamp fields remain strings after deserialization.
4. That assumption held in Windows PowerShell 5.1 and changed in the installed PowerShell 7.6 runtime.
5. The certified launcher inherited the caller's PowerShell runtime instead of pinning the runtime exercised by its connected heartbeat tests.

## Recovery and instrument proof

Both failed attempts stopped before the blind actor started. The first lacked the task-local `jsonschema` dependency path. The second wrote no transcript, run log, debrief, or blindness certificate; its heartbeat summary records `actorStartedAt: null`.

The recovery uses the installed Windows PowerShell 5.1 runtime without changing the shared harness. A direct probe exercised the production lane-lock and heartbeat modules with a live lease. It recorded two distinct one-second renewals, retained the launcher PID and acquisition timestamp, advanced to the `verdict` stage, and exited zero. This distinguishes a working runtime from the PowerShell 7.6 false alarm before the single recovery invocation.

The recovery preserves the CBO candidate and the certified browser, transcript, and blindness-audit boundary. PowerShell 7.6 timestamp compatibility in the shared module remains a separate infrastructure defect.
