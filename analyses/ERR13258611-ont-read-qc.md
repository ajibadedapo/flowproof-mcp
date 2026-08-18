# Reproducible Oxford Nanopore read QC on a real public genome, with FlowProof

This is a reproducible-methods demonstration on real, public data, not a new
biological finding, which is exactly the right claim for a provenance tool.

## What this is

I ran a real, public Oxford Nanopore sequencing dataset through [FlowProof](https://github.com/ajibadedapo/flowproof-mcp)
and recorded read-level statistics together with a verifiable provenance record.
The point is not the biology; it is that the result ships with everything needed to
reproduce it byte-for-byte.

## Data

- Run accession: **ERR13258611** (European Nucleotide Archive, project PRJEB51164)
- Organism: *Staphylococcus capitis*
- Platform: Oxford Nanopore
- File: `ERR13258611.fastq.gz` (138 MB), downloaded from ENA
- Input SHA-256 (from the crate): `e6cf10a5a6e7910a388589e8ee6044f7c12b2a9dbc66a8ae5c6499c923078dca`

## Method

FlowProof's `ont-read-stats` pipeline (a container-free Nextflow workflow) computed
read statistics over the FASTQ. FlowProof emitted a Workflow Run RO-Crate capturing
the pipeline, the exact tool version, the parameters, and SHA-256 checksums of the
input and the output.

```
# Download the real data
curl -O https://ftp.sra.ebi.ac.uk/vol1/fastq/ERR132/011/ERR13258611/ERR13258611.fastq.gz
gunzip ERR13258611.fastq.gz

# Then, from an MCP client (Claude Desktop / Cursor) with FlowProof configured:
#   "run ont-read-stats on ERR13258611.fastq"
```

Tool version recorded: Nextflow `26.04.6 build 12646`. Parameter: `genome_size=2.5m`.
Full command and environment are in the crate.

## Results

| Metric | Value |
|--------|-------|
| Reads | 51,946 |
| Total bases | 143,086,548 (143 Mbp) |
| Mean read length | ~2,755 bp |
| Output SHA-256 (`read_stats.txt`) | `29ff14950b5562e0271988184bd6ae9773ba249176b1e0359efedf383052b2df` |

## Reproducibility

The complete Workflow Run RO-Crate for this analysis is attached
([`ERR13258611-ro-crate-metadata.json`](./ERR13258611-ro-crate-metadata.json)). It
records the input file's SHA-256, the output file's SHA-256, the Nextflow version,
and the parameter, all from a real run. Anyone can recompute the recorded checksums
and re-run the pipeline from the crate's parameters to obtain the same `read_stats.txt`.
Nothing here is a black box: the recipe and fixity information travel with the result.

## A note found by running it for real

This run also surfaced a small robustness issue: when FlowProof is given a *relative*
run directory, Nextflow's working-directory handling nests the output path, and the
output collector then misses the result file (the crate still records the input, but
not the output). Using an absolute run directory produces the complete crate above.
Worth hardening in the runner so relative paths behave the same as absolute ones.

## Why it matters

Most "an AI ran an analysis for you" workflows hand back a number with no way to check
it. This run demonstrates the alternative on real data: an AI-drivable pipeline whose
output is independently verifiable. If you run Nextflow pipelines and want that property
at the AI boundary, FlowProof is `uvx flowproof-mcp` away.

*Data: ENA ERR13258611 (PRJEB51164). Software: FlowProof, https://doi.org/10.5281/zenodo.21932977.*
