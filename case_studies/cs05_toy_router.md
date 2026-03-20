# CS-05: The Toy Router Gap (Incomplete Safety Logic)

## Colab Relevance: MEDIUM
When copy-pasting safety logic into Colab notebooks to avoid import errors, the risk of omitting critical checks is high.

## The Failure
A notebook ran "successfully" but used simplified safety logic that missed multiple attack vectors. The incomplete logic produced invalid evaluation results.

## Root Cause
1. **Partial logic copy**: Only a subset of safety checks was pasted into the Colab notebook
2. **Dependency avoidance**: To avoid complex local imports, minimal logic was copy-pasted

## The Fix
When copy-pasting logic into Colab: include ALL regexes, ALL constants, ALL checks. Partial copying is a security failure.

## Prevention
The build skill's Full Armor Injection rule (S10.1) mandates complete logic copies.

## Triage Signature
**Category:** LOGIC.INCOMPLETE
