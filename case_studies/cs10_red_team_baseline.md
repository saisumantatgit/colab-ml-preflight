# CS-10: The Red Team Baseline — Evaluation Harness Lessons

## Colab Relevance: LOW
The SameFileError from this case study is Kaggle-specific (/kaggle/working/ is the output dir). On Colab, /content/ is the working dir but not the persistent output dir.

## The Failure
An evaluation notebook completed successfully but reported ERROR due to a SameFileError when copying output files to the working directory.

## Colab Context
- On Colab, `/content/` is the working directory
- Unlike Kaggle, Colab does not auto-save from the working directory
- The SameFileError is unlikely on Colab because you save to Drive, not /content/

## Lessons That Apply to Colab
1. **tqdm buffering**: tqdm writes to stderr, which Colab buffers. Use explicit stdout heartbeats.
2. **Provenance metadata**: Capture GPU type, package versions, and git hash at runtime.
3. **Test contract maintenance**: When updating models, update expected test outputs too.

## Triage Signature
**Category:** LOGIC.SAMEFILE (Kaggle-specific, rare on Colab)
