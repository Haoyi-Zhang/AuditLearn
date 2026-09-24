#!/usr/bin/env python3
"""Independent, standard-library release validator.

The validator intentionally does not import the simulator package.  It checks
serialized results and source files through a separate code path so that a
single implementation error is less likely to validate itself.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, platform, re, subprocess, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
AMBIGUOUS_METHODS = {"completed", "complete", "returned"}
REQUIRED_DOCS = [
    ROOT / "README.md",
    ROOT / "ARTIFACT-EVALUATION.md",
    ROOT / "DATA-DICTIONARY.md",
    ROOT / "STATISTICAL-INTERPRETATION.md",
    ROOT / "LIMITATIONS-MATRIX.md",
    ROOT / "verify_curated_results.py",
    ROOT / "audit_reference_evidence.py",
    ROOT / "proofs" / "misspecification-and-blackout.md",
    PROJECT / "REVIEWER-CHECKLIST.md",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="strict")


def iter_release_files() -> Iterable[Path]:
    excluded = {"__pycache__", ".git", ".pytest_cache"}
    for p in sorted(PROJECT.rglob("*")):
        if not p.is_file() or any(part in excluded for part in p.parts):
            continue
        if p.name in {"MANIFEST.sha256", "reproduction-manifest.json"}:
            continue
        yield p


def candidate_key(columns: list[str]) -> list[str]:
    preferred = [
        "campaign", "truth", "truth_id", "seed", "method", "delay",
        "delay_mechanism", "horizon", "episode", "time", "blocker_count",
        "audit_lag", "run_id", "cell_id",
    ]
    return [c for c in preferred if c in columns]


def inspect_csv(path: Path, full: bool) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        key = candidate_key(cols)
        rows = 0
        methods: Counter[str] = Counter()
        seen: set[tuple[str, ...]] = set()
        duplicate_keys = 0
        sorted_violation = False
        last: tuple[str, ...] | None = None
        for row in reader:
            rows += 1
            if "method" in row and row["method"]:
                methods[row["method"].strip().lower()] += 1
            if full and key:
                k = tuple(row.get(c, "") for c in key)
                if k in seen:
                    duplicate_keys += 1
                seen.add(k)
                if last is not None and k < last:
                    sorted_violation = True
                last = k
    bad = sorted(set(methods) & AMBIGUOUS_METHODS)
    return {
        "columns": cols,
        "rows": rows,
        "candidate_key": key,
        "duplicate_candidate_keys": duplicate_keys,
        "candidate_key_not_sorted": sorted_violation,
        "method_counts": dict(sorted(methods.items())),
        "ambiguous_method_labels": bad,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def source_audit() -> dict[str, Any]:
    py = [p for p in ROOT.rglob("*.py") if "__pycache__" not in p.parts]
    combined = "\n".join(text(p) for p in py)
    findings: dict[str, list[str]] = {}
    patterns = {
        "network_or_model_clients": r"\b(requests|urllib3|openai|anthropic|socket|httpx)\b",
        "gpu_frameworks": r"\b(torch|tensorflow|jax|cupy|cuda)\b",
        "shell_execution": r"\b(os\.system|subprocess\.(Popen|run|call|check_output))\b",
        "builtin_hash_calls": r"(?<![A-Za-z0-9_])hash\s*\(",
        "unseeded_system_random": r"\b(SystemRandom|secrets\.)",
    }
    for label, pat in patterns.items():
        hits=[]
        rx=re.compile(pat)
        for p in py:
            for n,line in enumerate(text(p).splitlines(),1):
                if rx.search(line):
                    hits.append(f"{p.relative_to(PROJECT)}:{n}:{line.strip()[:180]}")
        findings[label]=hits
    return {"python_files":len(py),"findings":findings}


def bibliography_audit() -> dict[str, Any]:
    bibs=list((PROJECT/"paper").rglob("*.bib")) if (PROJECT/"paper").exists() else []
    texs=list((PROJECT/"paper").rglob("*.tex")) if (PROJECT/"paper").exists() else []
    entries: set[str]=set()
    for p in bibs:
        entries.update(re.findall(r"@\w+\s*\{\s*([^,\s]+)", text(p)))
    cited: set[str]=set()
    for p in texs:
        s=re.sub(r"(?m)%.*$", "", text(p))
        for grp in re.findall(r"\\cite\w*\s*(?:\[[^\]]*\]\s*)*\{([^}]+)\}", s):
            cited.update(k.strip() for k in grp.split(",") if k.strip())
    return {
        "bib_entries":len(entries),"cited_keys":len(cited),
        "missing_entries":sorted(cited-entries),"uncited_entries":sorted(entries-cited),
        "uses_nocite":any("\\nocite" in text(p) for p in texs),
    }


def compile_check() -> dict[str, Any]:
    r=subprocess.run([sys.executable,"-m","compileall","-q",str(ROOT)],
                     stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    return {"returncode":r.returncode,"output":r.stdout[-4000:]}


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--quick",action="store_true",help="skip row-level duplicate/sort scan")
    ap.add_argument("--results",default=None,help="results directory; defaults to release results if present")
    ap.add_argument("--write-manifest",action="store_true")
    args=ap.parse_args()
    errors=[]
    warnings=[]
    for p in REQUIRED_DOCS:
        if not p.exists(): errors.append(f"missing required document: {p.relative_to(PROJECT)}")
    comp=compile_check()
    if comp["returncode"]: errors.append("Python compileall failed")
    results=Path(args.results).resolve() if args.results else None
    if results is None:
        candidates=[ROOT/"results",ROOT/"repro-results",ROOT/"reviewer-full",ROOT/"reviewer-results"]
        results=next((p for p in candidates if p.exists()), ROOT/"results")
    csv_info={}
    if results.exists():
        for p in sorted(results.rglob("*.csv")):
            rel=str(p.relative_to(results))
            info=inspect_csv(p,full=not args.quick)
            csv_info[rel]=info
            if info["ambiguous_method_labels"]:
                errors.append(f"ambiguous method label in {rel}: {info['ambiguous_method_labels']}")
            # Duplicate checks are only definitive when the heuristic key spans most identifiers.
            if not args.quick and len(info["candidate_key"])>=3 and info["duplicate_candidate_keys"]:
                warnings.append(f"heuristic candidate-key duplicates in {rel}: {info['duplicate_candidate_keys']}; authoritative campaign verification uses the configured key set")
    bib=bibliography_audit()
    if bib["missing_entries"]: errors.append(f"missing bibliography entries: {bib['missing_entries']}")
    if bib["uncited_entries"]: errors.append(f"uncited bibliography entries: {bib['uncited_entries']}")
    if bib["uses_nocite"]: errors.append("paper uses \\nocite")
    src=source_audit()
    # Network/GPU findings are not automatically errors because words may occur in comments/docs.
    if src["findings"]["builtin_hash_calls"]:
        errors.append("built-in hash() call found; release seeds must be stable across processes")
    manifest={
        "schema_version":1,
        "generated_utc":datetime.now(timezone.utc).isoformat(),
        "platform":{"python":sys.version,"implementation":platform.python_implementation(),
                    "platform":platform.platform(),"machine":platform.machine(),
                    "cpu_count":os.cpu_count()},
        "results_directory":str(results.relative_to(PROJECT)) if results.exists() and PROJECT in results.parents else str(results),
        "csv":csv_info,"bibliography":bib,"source_audit":src,"compileall":comp,
        "release_files":{str(p.relative_to(PROJECT)): {"bytes":p.stat().st_size,"sha256":sha256(p)} for p in iter_release_files()},
        "errors":errors,"warnings":warnings,
    }
    out=results/"reproduction-manifest.json" if results.exists() else ROOT/"reproduction-manifest.json"
    if args.write_manifest or not args.quick:
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS" if not errors else "FAIL","errors":errors,"warnings":warnings,
                      "csv_files":len(csv_info),"bib_entries":bib["bib_entries"],
                      "manifest":str(out)},indent=2))
    return 1 if errors else 0

if __name__=="__main__":
    raise SystemExit(main())
