#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from flowproof.runner import NextflowBackend
from flowproof.service import RunManager


def main() -> int:
    ap = argparse.ArgumentParser(description="Produce a real ont-read-stats run via the flowproof NextflowBackend.")
    ap.add_argument("outdir", help="directory to create the run under")
    ap.add_argument("--pipeline", default="ont-read-stats")
    ap.add_argument("--reads", default=None, help="optional reads path; omit to use bundled sample")
    ap.add_argument("--genome-size", default=None)
    args = ap.parse_args()

    inputs = {"reads": args.reads} if args.reads else None
    params = {"genome_size": args.genome_size} if args.genome_size else None

    mgr = RunManager(Path(args.outdir), backend=NextflowBackend())
    rec = mgr.start_run(args.pipeline, inputs, params)

    out = {
        "run_id": rec.run_id,
        "status": rec.status.value,
        "run_dir": rec.run_dir,
        "provenance_path": rec.provenance_path,
        "outputs": [
            {"path": f.path, "sha256": f.sha256, "size_bytes": f.size_bytes}
            for f in (rec.result.output_files if rec.result else [])
        ],
        "tool_versions": rec.result.tool_versions if rec.result else {},
        "error": rec.result.error if rec.result else "no result",
    }
    json.dump(out, sys.stdout, indent=2)
    print()
    return 0 if rec.status.value == "succeeded" else 1


if __name__ == "__main__":
    sys.exit(main())
