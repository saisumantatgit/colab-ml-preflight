# CS-03: Phantom Dataset References

## Colab Relevance: MEDIUM
On Colab, phantom references take a different form: Drive paths that don't exist, gdown URLs that are expired, or files lost after a disconnect.

## The Failure
A notebook referenced data files that did not exist at the expected paths, causing silent failures or FileNotFoundError.

## Root Cause
1. **Drive path mismatch**: File was at `/content/drive/MyDrive/data/` but code referenced `/content/data/`
2. **Lost files after disconnect**: Files uploaded to `/content/` were lost when the session disconnected
3. **Expired share links**: gdown URLs pointing to files that were no longer shared

## Colab-Specific Impact
- Everything in `/content/` is wiped on disconnect — this is the #1 cause of phantom data on Colab
- Drive paths are case-sensitive — `MyDrive` vs `mydrive` fails silently
- Google Drive share links expire or change permissions

## The Fix
1. Always verify data exists before processing:
   ```python
   import os
   for f in data_files:
       assert os.path.exists(f), f"Missing: {f}"
   ```
2. Store all data on Drive, not `/content/`
3. Use absolute Drive paths: `/content/drive/MyDrive/datasets/...`

## Prevention
The launch skill includes data access verification before execution. The check skill flags paths outside `/content/drive/`.

## Triage Signature
**Category:** DATA.PHANTOM, DATA.MISSING
