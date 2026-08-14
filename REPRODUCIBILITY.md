# FlowProof reproducibility protocol

This is the protocol behind the "Reproducibility evaluation" section of the paper.
Every `[FILL: ...]` marker in the manuscript maps to a step below. Run the steps,
paste the numbers, delete the markers.

Two rules make the difference between an evaluation and a demonstration:

1. **Report per-item outcomes, not just aggregates.** "38 of 40 rejected" with the
   two exceptions named is far more credible than "all rejected".
2. **Report the failures.** A reviewer who finds a limitation you did not disclose
   discounts everything else in the paper. A limitation you disclosed yourself
   costs you a sentence.

Everything below writes into `eval/results/`. Commit that directory.

---

## Step 0. Environment capture

Do this on every host before any run, and archive the output. The paper needs it,
and R2 is meaningless without it.

```bash
mkdir -p eval/results
HOST=H1   # H2 on the second machine

{
  echo "host_label: $HOST"
  uname -a
  echo "python: $(python3 --version)"
  echo "nextflow: $(nextflow -version 2>&1 | tr '\n' ' ')"
  echo "container: $(docker --version 2>/dev/null || singularity --version 2>/dev/null)"
  echo "flowproof: $(pip show flowproof-mcp | sed -n 's/^Version: //p')"
  echo "cpu: $(nproc) cores"
  echo "mem: $(free -h 2>/dev/null | awk '/^Mem:/{print $2}')"
  echo "commit: $(git rev-parse HEAD)"
} > "eval/results/env-$HOST.txt"
```

Choose H2 to differ from H1 in **operating system and architecture**, not just in
hostname. Ubuntu x86_64 against macOS arm64 is a real cross-host test. Two
identical cloud VMs are not, and a reviewer will say so.

## Step 1. Fix the pipeline identifier mismatch first

The bundled example is registered as `assembly-ont` but its output is
`read_stats.txt`, which is read statistics and not an assembly. Do one of:

- rename the manifest identifier to something truthful (`ont-read-stats`), or
- make it a real assembly (Flye or miniasm on the sample) and keep the name.

Do not publish a paper whose Table 2 says `assembly-ont` next to a 59-byte stats
file. It is the kind of detail that makes a reviewer start looking for others.
Whichever you pick, the manuscript's Table 2 and the manifest must agree.

## R1. Repeat determinism, one host

```bash
for i in $(seq -w 1 20); do
  flowproof run ont-read-stats --outdir "eval/results/H1/run-$i"
  python eval/verify_crate.py fixity "eval/results/H1/run-$i" \
    > "eval/results/H1/run-$i.fixity.json"
done

python eval/verify_crate.py compare eval/results/H1/run-*.fixity.json \
  | tee eval/results/R1.txt
```

Report: number of runs, whether all fixity sets matched, and any field that
differed. If something legitimately varies that is not already in
`VOLATILE_KEYS` inside `verify_crate.py`, add it there and say so in the paper.
Silently widening the exclusion list is how this experiment stops meaning
anything.

## R2. Cross-host reproduction

Run the same loop on H2, then compare across hosts:

```bash
python eval/verify_crate.py compare \
  eval/results/H1/run-01.fixity.json \
  eval/results/H2/run-01.fixity.json | tee eval/results/R2.txt
```

Expect the runner build string to differ if the Nextflow versions differ. That is
a finding, not a bug: it tells the reader the crate captures enough to explain a
divergence. Report it either way.

## R3. Independent verification from the crate alone

```bash
# on a machine that has never run the FlowProof server
python eval/verify_crate.py check eval/results/H1/run-01 | tee eval/results/R3.txt
```

Then re-execute from the crate contents only: read the recorded pipeline version,
container reference and parameter set out of `ro-crate-metadata.json`, run that,
and compare output digests. Script this as `eval/reexecute_from_crate.py` so the
reviewer can run it. The claim in the paper is that the crate is sufficient; the
proof is a script that consumes only the crate.

## R4. Tamper detection

Four injected faults. All four must be flagged, and the verifier should name the
divergent field.

```bash
mkdir -p eval/results/tamper
for case in byte_flip digest_edit container_swap param_change; do
  cp -r eval/results/H1/run-01 "eval/results/tamper/$case"
done

# 1. single byte flipped in an input, crate untouched
printf 'X' | dd of=eval/results/tamper/byte_flip/data/ont_sample.fastq \
  bs=1 seek=1000 conv=notrunc status=none

# 2. recorded digest edited, file untouched
python - <<'PY'
import json, pathlib
p = pathlib.Path("eval/results/tamper/digest_edit/ro-crate-metadata.json")
d = json.loads(p.read_text())
for e in d["@graph"]:
    if "sha256" in e:
        e["sha256"] = "0" * 64
        break
p.write_text(json.dumps(d, indent=2))
PY

# 3 and 4: edit the recorded container reference and one parameter value
#          in the respective copies, by hand or by script

for case in byte_flip digest_edit container_swap param_change; do
  echo "== $case"
  python eval/verify_crate.py check "eval/results/tamper/$case"
done | tee eval/results/R4.txt
```

Note that cases 3 and 4 are not caught by digest checking alone; they need the
re-execution path from R3. If your verifier catches 2 of 4, report 2 of 4 and say
which. That is still a much stronger result than the current paper has, and
claiming 4 of 4 with a script that only checks digests is the kind of thing that
gets found.

## R5. Parameter boundary

`eval/adversarial_params.json` holds the corpus. You need one harness function
that submits a value through the real run tool, because only you know the call
signature:

```python
# eval/test_param_boundary.py
import json, subprocess, pathlib

CORPUS = json.loads(pathlib.Path("eval/adversarial_params.json").read_text())

def submit(param_name, value):
    """Return (rejected: bool, argv: list[str] | None).

    Must go through the same entry point the MCP run tool uses, not a private
    validation helper. Testing the validator directly proves the validator
    works, not that the server calls it.
    """
    raise NotImplementedError

rows = []
for cls, values in CORPUS["classes"].items():
    for v in values:
        rejected, argv = submit("input", v)
        leaked = bool(argv) and any(v[:12] in a for a in argv)
        rows.append((cls, v, rejected, leaked))

canary = pathlib.Path(CORPUS["canary_path"])
assert not canary.exists(), "a payload reached a shell"

for cls, v, rejected, leaked in rows:
    print(f"{'REJECT' if rejected else 'ACCEPT':6} leak={leaked!s:5} {cls}: {v!r}")
print(f"\n{sum(r[2] for r in rows)}/{len(rows)} rejected, "
      f"{sum(r[3] for r in rows)} leaked into argv")
```

Report per class, and add a table row for any accepted value with the reason it
is safe to accept. Also assert the canary file does not exist afterwards.

## R6. Assistant-driven operation

Thirty task descriptions in natural language, run through at least two MCP
clients, scored as completed without human intervention or not.

Cover all six tools, and include roughly a quarter of tasks that **should** fail:
an unregistered pipeline name, a missing required input, a status poll on an
unknown run identifier, a parameter outside its declared enumeration. Correct
refusal counts as success; a plausible-looking answer to an impossible request is
a failure and worth reporting, because it is what an auditor of an AI-issued
analysis actually cares about.

Record for each attempt: client and model version, prompt, tool calls made,
outcome, and failure class where relevant. Report per client. Tool-calling
behaviour is a property of the model, not of your server, and conflating the two
invites the reviewer to dismiss the whole experiment.

```
eval/results/R6-<client>-<model>.csv
prompt_id,prompt,expected,tool_calls,outcome,failure_class
```

## Step 7. Overhead

One number, and it closes an obvious reviewer question:

```bash
hyperfine --warmup 1 \
  'flowproof run ont-read-stats --provenance on' \
  'flowproof run ont-read-stats --provenance off' \
  --export-markdown eval/results/overhead.md
```

If provenance emission cannot be disabled, time the emitter directly and say so.

## Step 8. Archive and cite

```bash
git tag -a v0.1.0-preprint -m "Version described in the preprint"
git push --tags
```

Then create the Zenodo release from the GitHub tag, and put the resulting DOI in
the abstract, Availability, and Data availability sections. A preprint that
points at a moving `main` branch is not reproducible in the sense the paper
claims, and this step costs about ten minutes.

---

## Filling the manuscript

| Manuscript location | Source |
| --- | --- |
| Abstract, evaluation sentence | R1, R3, R4, R5 headline counts |
| Setup paragraph | `eval/results/env-H1.txt`, `env-H2.txt` |
| Table 2, pipeline and container rows | manifest after Step 1, crate |
| R1 to R6 paragraphs | `eval/results/R*.txt` and the R6 CSVs |
| Table 3 | the same, one row each |
| Limitations, overhead sentence | Step 7 |
| Availability, repository and DOI | Step 8 |
| Availability, test count and coverage | `pytest -q`, `coverage report` |

Grep for `[FILL` before you post. There are 44 of them.
