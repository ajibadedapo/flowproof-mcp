#!/usr/bin/env python3
"""Independent verifier for a FlowProof Workflow Run RO-Crate.

Design constraint: this script must be able to run with no access to the
FlowProof server, no access to the run that produced the crate, and no
imports beyond the standard library. That is the whole point of experiments
R3 and R4 in REPRODUCIBILITY.md. If this file ever needs to import
flowproof, the independence claim in the paper is void.

Usage
  # R3: recompute every recorded checksum against the files on disk
  python verify_crate.py check path/to/crate

  # emit the normalised fixity set (volatile fields stripped) for comparison
  python verify_crate.py fixity path/to/crate > run01.fixity.json

  # R1/R2: compare fixity sets across repeated or cross-host runs
  python verify_crate.py compare run01.fixity.json run02.fixity.json

Exit codes: 0 pass, 1 mismatch found, 2 crate could not be read.
"""

import argparse
import hashlib
import json
import os
import sys

# Fields deliberately excluded from the fixity set because they differ
# between runs of identical content. This list is the auditable version of
# the "volatile fields" paragraph in the paper. Keep the two in sync.
VOLATILE_KEYS = {
    "startTime", "endTime", "dateCreated", "datePublished", "dateModified",
    "duration", "identifier", "@id", "url", "sessionId", "runId",
    "workingDirectory", "hostname", "user",
}

# Candidate property names for a SHA-256 digest on a File entity. RO-Crate
# profiles and generators differ here, so probe rather than assume.
HASH_KEYS = ("sha256", "sha-256", "checksum", "hasSha256", "contentSha256")


def die(msg, code=2):
    print("ERROR: %s" % msg, file=sys.stderr)
    sys.exit(code)


def load_crate(path):
    meta = path
    if os.path.isdir(path):
        meta = os.path.join(path, "ro-crate-metadata.json")
    if not os.path.isfile(meta):
        die("no ro-crate-metadata.json at %s" % path)
    try:
        with open(meta, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        die("crate metadata is not valid JSON: %s" % exc)
    graph = data.get("@graph")
    if not isinstance(graph, list):
        die("crate has no @graph array")
    return os.path.dirname(os.path.abspath(meta)), graph


def types_of(entity):
    t = entity.get("@type", [])
    return [t] if isinstance(t, str) else list(t)


def digest_of(entity):
    for key in HASH_KEYS:
        val = entity.get(key)
        if isinstance(val, str) and len(val) == 64:
            return key, val.lower()
        if isinstance(val, dict):  # e.g. {"@value": "..."}
            inner = val.get("@value")
            if isinstance(inner, str) and len(inner) == 64:
                return key, inner.lower()
    return None, None


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def file_entities(graph):
    for e in graph:
        if "File" in types_of(e):
            yield e


def cmd_check(args):
    root, graph = load_crate(args.crate)
    files = list(file_entities(graph))
    if not files:
        die("crate declares no File entities, nothing to verify")

    failures = []
    checked = 0
    unhashed = []

    for e in files:
        fid = e.get("@id", "<no @id>")
        key, recorded = digest_of(e)
        if recorded is None:
            unhashed.append(fid)
            continue
        target = fid if os.path.isabs(fid) else os.path.join(root, fid)
        if not os.path.isfile(target):
            failures.append((fid, "referenced file is missing on disk"))
            continue
        actual = sha256_file(target)
        checked += 1
        if actual != recorded:
            failures.append((fid, "digest mismatch: recorded %s, computed %s"
                             % (recorded[:16], actual[:16])))
            continue
        size = e.get("contentSize")
        if size is not None:
            try:
                if int(str(size).replace(",", "")) != os.path.getsize(target):
                    failures.append((fid, "contentSize disagrees with the file on disk"))
            except ValueError:
                failures.append((fid, "contentSize is not an integer: %r" % size))

    print("crate root : %s" % root)
    print("File nodes : %d" % len(files))
    print("verified   : %d" % checked)
    if unhashed:
        print("no digest  : %d (%s)" % (len(unhashed), ", ".join(unhashed[:5])))
    for fid, why in failures:
        print("FAIL %s: %s" % (fid, why))

    # A crate with no digests cannot fail, and a check that cannot fail is
    # not evidence. Treat it as a failure of the crate, not a pass.
    if unhashed and checked == 0:
        print("RESULT: FAIL (no verifiable digests present)")
        return 1
    print("RESULT: %s" % ("PASS" if not failures else "FAIL"))
    return 0 if not failures else 1


def prune(node):
    if isinstance(node, dict):
        return {k: prune(v) for k, v in sorted(node.items())
                if k not in VOLATILE_KEYS}
    if isinstance(node, list):
        return [prune(v) for v in node]
    return node


def cmd_fixity(args):
    _, graph = load_crate(args.crate)
    fixity = {"files": {}, "actions": []}
    for e in file_entities(graph):
        _, digest = digest_of(e)
        fixity["files"][os.path.basename(e.get("@id", ""))] = {
            "sha256": digest,
            "contentSize": e.get("contentSize"),
        }
    for e in graph:
        ts = types_of(e)
        if any(t in ("CreateAction", "ControlAction", "SoftwareApplication",
                     "ComputationalWorkflow") for t in ts):
            fixity["actions"].append(prune(e))
    json.dump(fixity, sys.stdout, indent=2, sort_keys=True)
    print()
    return 0


def cmd_compare(args):
    loaded = []
    for p in args.fixity:
        with open(p, "r", encoding="utf-8") as fh:
            loaded.append((p, json.load(fh)))
    ref_name, ref = loaded[0]
    rc = 0
    for name, other in loaded[1:]:
        if other == ref:
            print("MATCH %s == %s" % (ref_name, name))
        else:
            rc = 1
            print("DIFFER %s != %s" % (ref_name, name))
            ref_files, other_files = ref.get("files", {}), other.get("files", {})
            for key in sorted(set(ref_files) | set(other_files)):
                if ref_files.get(key) != other_files.get(key):
                    print("  file %s: %s vs %s"
                          % (key, ref_files.get(key), other_files.get(key)))
            if ref.get("actions") != other.get("actions"):
                print("  action metadata differs (diff the fixity files to see where)")
    print("RESULT: %s" % ("PASS" if rc == 0 else "FAIL"))
    return rc


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("check", help="recompute recorded digests against files on disk")
    p.add_argument("crate", help="crate directory or ro-crate-metadata.json")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("fixity", help="print the normalised fixity set as JSON")
    p.add_argument("crate")
    p.set_defaults(func=cmd_fixity)

    p = sub.add_parser("compare", help="compare two or more fixity sets")
    p.add_argument("fixity", nargs="+")
    p.set_defaults(func=cmd_compare)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
