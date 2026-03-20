# CS-02: Asynchronous Race Conditions

## Colab Relevance: LOW
Colab has no external monitoring API, so the classic poll-then-fetch race condition is less likely. However, this case study still applies if you use Google Apps Script or browser automation to interact with Colab.

## The Failure
An agent attempted to retrieve notebook output while execution was still in progress, causing incomplete data retrieval.

## Root Cause
1. **Race condition**: Output was fetched before execution completed
2. **Shell parsing**: Complex bash logic in monitoring scripts caused crashes

## The Fix
1. Use in-notebook heartbeats instead of external polling on Colab
2. Wait for explicit completion signals before copying outputs
3. Save outputs to Drive progressively, not all at the end

## Prevention
The monitor skill uses in-notebook heartbeat patterns instead of external polling for Colab.

## Triage Signature
**Category:** LOGIC.ESCAPING
