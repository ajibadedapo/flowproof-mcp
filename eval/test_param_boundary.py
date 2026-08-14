#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
from pathlib import Path

from flowproof.registry import registry
from flowproof.runner import NextflowBackend, UnsafeValue, validate_value

CORPUS = json.loads(pathlib.Path("eval/adversarial_params.json").read_text())
MANIFEST = registry.get("ont-read-stats")
BACKEND = NextflowBackend()


def submit(param_name, value):
    validator_rejected = False
    try:
        validate_value(param_name, value)
    except UnsafeValue:
        validator_rejected = True

    argv = None
    build_rejected = False
    with tempfile.TemporaryDirectory() as tmp:
        try:
            argv = BACKEND.build_command(
                MANIFEST, Path(tmp), {param_name: value}, {"genome_size": "5m"}
            )
        except UnsafeValue:
            build_rejected = True
    return validator_rejected, build_rejected, argv


def main() -> int:
    rows = []
    for cls, values in CORPUS["classes"].items():
        for v in values:
            vr, br, argv = submit("reads", v)
            rejected = vr and br
            leaked = bool(argv) and any(v[:12] in a for a in argv)
            rows.append({
                "class": cls, "value": v,
                "validator_rejected": vr, "build_rejected": br,
                "rejected": rejected, "leaked_into_argv": leaked,
            })

    canary = pathlib.Path(CORPUS["canary_path"])
    canary_exists = canary.exists()

    for r in rows:
        tag = "REJECT" if r["rejected"] else "ACCEPT"
        print(f"{tag:6} leak={str(r['leaked_into_argv']):5} {r['class']}: {r['value']!r}")

    print()
    per_class = {}
    for r in rows:
        d = per_class.setdefault(r["class"], {"total": 0, "rejected": 0, "leaked": 0, "accepted_values": []})
        d["total"] += 1
        d["rejected"] += 1 if r["rejected"] else 0
        d["leaked"] += 1 if r["leaked_into_argv"] else 0
        if not r["rejected"]:
            d["accepted_values"].append(r["value"])
    for cls, d in per_class.items():
        print(f"class {cls}: {d['rejected']}/{d['total']} rejected, {d['leaked']} leaked into argv")
        for av in d["accepted_values"]:
            print(f"    ACCEPTED: {av!r}")

    total = len(rows)
    total_rej = sum(1 for r in rows if r["rejected"])
    total_leak = sum(1 for r in rows if r["leaked_into_argv"])
    print(f"\n{total_rej}/{total} rejected, {total_leak} leaked into argv")
    print(f"canary {CORPUS['canary_path']} exists after corpus: {canary_exists}")

    dotdot = [r for r in rows if ".." in r["value"]]
    print(f"path-traversal '..' cases: {len(dotdot)}, all rejected: "
          f"{all(r['rejected'] for r in dotdot)}")

    Path("eval/results").mkdir(parents=True, exist_ok=True)
    Path("eval/results/R5.json").write_text(json.dumps(
        {"rows": rows, "per_class": per_class, "total": total,
         "total_rejected": total_rej, "total_leaked": total_leak,
         "canary_exists": canary_exists}, indent=2) + "\n")

    assert not canary_exists, "a payload reached a shell"
    return 0


if __name__ == "__main__":
    sys.exit(main())
