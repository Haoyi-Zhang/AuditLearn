# Artifact evaluation guide

## What this artifact establishes

The artifact independently recomputes finite policy values, oracle minima, launch-sensitive coupling checks, completion-set geometry, delayed-exposure inequalities, selector information boundaries, and all frozen synthetic campaigns. It also rebuilds the tables/plot inputs used by the paper.

## What it does not establish

It does not mechanically prove the general theorems, execute a language model, benchmark serving hardware, establish population-level generalization, or certify novelty and acceptance. Those boundaries are explicit in the paper and `CURRENT-STATE.md`.

## Quick path

```bash
python run.py check --output check-results
python run.py smoke --output smoke-results
python validate_release.py --quick
```

## Complete path

Use the release script documented in `README.md`. Long campaigns are deterministic and sharded. Re-running a complete campaign may take materially longer than a quick check; use the recorded command-level resource log rather than an assumed runtime.

## Method information sets

- **prefix-only:** valid chronological-prefix confidence information.
- **completion-only:** valid confidence information from all returned counts plus the number of unresolved launched records.
- **intersection:** intersection of the preceding two valid sets.
- **returned-only:** deliberately invalid negative control that treats selected returns as if they were an iid sample.
- **plug-in:** nonconservative point-estimate diagnostic.
- **oracle:** truth-aware diagnostic lower reference, not a deployable learner.

The names are semantic contracts. `validate_release.py` rejects legacy ambiguous labels in generated tables.

## Determinism and integrity

Every campaign uses explicit stable integer seeds. Merge operations require the complete configured key set, reject duplicates, and sort rows before serialization. The release manifest records SHA-256 hashes for source, frozen data, and generated paper fragments.
