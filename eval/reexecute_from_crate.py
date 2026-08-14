#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

from flowproof.runner import NextflowBackend
from flowproof.service import RunManager

HASH_KEYS = ("sha256", "sha-256", "checksum", "hasSha256", "contentSha256")


def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _types(entity: dict) -> list[str]:
    t = entity.get("@type", [])
    return [t] if isinstance(t, str) else list(t)


def _digest(entity: dict):
    for key in HASH_KEYS:
        val = entity.get(key)
        if isinstance(val, str) and len(val) == 64:
            return val.lower()
    return None


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Re-execute a pipeline using ONLY the crate's ro-crate-metadata.json, "
        "then compare re-run output digests against the crate's recorded output digests."
    )
    ap.add_argument("crate", help="crate directory or ro-crate-metadata.json path")
    args = ap.parse_args()

    meta = Path(args.crate)
    if meta.is_dir():
        meta = meta / "ro-crate-metadata.json"
    data = json.loads(meta.read_text())
    graph = data["@graph"]

    run_action = next(
        e for e in graph
        if e.get("@type") == "CreateAction" and str(e.get("@id", "")).startswith("#run-")
    )
    pipeline_id = run_action["instrument"]["@id"]

    workflow = next(
        (e for e in graph if isinstance(e.get("@type"), list)
         and "ComputationalWorkflow" in e["@type"]),
        None,
    )
    recorded_version = workflow.get("version") if workflow else None

    files_by_id = {e.get("@id"): e for e in graph if "File" in _types(e)}

    crate_root = meta.resolve().parent

    def resolve_ref(ref: str) -> str:
        p = Path(ref)
        return str(p if p.is_absolute() else (crate_root / p))

    input_object_ids = [o.get("@id") for o in run_action.get("object", [])]
    inputs: dict[str, str] = {}
    for oid in input_object_ids:
        ent = files_by_id.get(oid, {})
        name = ent.get("name")
        if name:
            inputs[name] = resolve_ref(oid)

    property_values = {
        e.get("name"): e.get("value")
        for e in graph
        if e.get("@type") == "PropertyValue" and e.get("name") is not None
    }
    params: dict[str, str] = {}
    for oid in input_object_ids:
        if str(oid).startswith("#param-"):
            ent = next((e for e in graph if e.get("@id") == oid), {})
            name = ent.get("name")
            if name is not None and ent.get("value") is not None:
                params[name] = ent.get("value")
    for name, value in property_values.items():
        params.setdefault(name, value)

    output_result_ids = [o.get("@id") for o in run_action.get("result", [])]
    recorded_outputs = {}
    for oid in output_result_ids:
        ent = files_by_id.get(oid, {})
        recorded_outputs[oid] = _digest(ent)

    print(f"crate            : {meta}")
    print(f"pipeline id      : {pipeline_id}")
    print(f"recorded version : {recorded_version}")
    print(f"inputs (from crate): {inputs}")
    print(f"params (from crate PropertyValue nodes): {params}")

    for name, path in inputs.items():
        if not Path(path).is_file():
            print(f"ERROR: input '{name}' referenced at {path} is missing on disk; "
                  "cannot re-execute from this crate on this host.", file=sys.stderr)
            return 2

    with tempfile.TemporaryDirectory(prefix="reexec-") as tmp:
        mgr = RunManager(Path(tmp), backend=NextflowBackend())
        rec = mgr.start_run(pipeline_id, dict(inputs), dict(params) or None)
        if rec.status.value != "succeeded":
            print(f"RESULT: FAIL (re-execution did not succeed: "
                  f"{rec.result.error if rec.result else 'no result'})")
            return 1

        rerun_by_basename = {}
        for f in rec.result.output_files:
            rerun_by_basename[Path(f.path).name] = f.sha256

        all_match = True
        matched = 0
        for oid, recorded in recorded_outputs.items():
            base = Path(oid).name
            actual = rerun_by_basename.get(base)
            ok = actual is not None and actual == recorded
            matched += 1 if ok else 0
            all_match = all_match and ok
            print(f"output {oid}")
            print(f"  recorded : {recorded}")
            print(f"  re-run   : {actual}")
            print(f"  {'MATCH' if ok else 'MISMATCH'}")

        print(f"RESULT: {'PASS' if all_match else 'FAIL'} "
              f"({matched}/{len(recorded_outputs)} outputs reproduced byte-for-byte)")
        return 0 if all_match else 1


if __name__ == "__main__":
    sys.exit(main())
