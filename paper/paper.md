---
title: 'FlowProof: Reproducible bioinformatics pipeline execution over the Model Context Protocol with verifiable provenance'
tags:
  - bioinformatics
  - reproducibility
  - provenance
  - Model Context Protocol
  - workflows
  - Nextflow
  - RO-Crate
  - large language models
authors:
  - name: Hammed Adedapo Ajibade
    orcid: 0000-0003-3120-4439
    affiliation: 1
affiliations:
  - name: Specvista Technology Limited
    index: 1
date: 14 August 2026
bibliography: paper.bib
---

# Summary

FlowProof is a Model Context Protocol (MCP) server that lets a large language model (LLM) assistant run a bioinformatics pipeline and receive results whose provenance can be independently verified. Every run emits a Workflow Run RO-Crate [@wfrun-rocrate] recording the pipeline version, container image, tool versions, parameters, and SHA-256 checksums of every input and output, so an AI-driven analysis ships with the exact recipe and fixity information needed to reproduce it. Pipelines are executed through a runner-agnostic core: a dependency-free backend supports development and continuous integration, while a Nextflow [@nextflow] backend runs real workflows. FlowProof is registry-driven, so short-read and long-read (Oxford Nanopore) pipelines coexist and new ones are added by manifest without modifying the server. It is distributed as an open-source Python package (`pip install flowproof-mcp`) and exposes six MCP tools (list, describe, run, status, results, and provenance), usable by any MCP-capable assistant over a local (stdio) or hosted (HTTP) transport.

# Statement of need

Model Context Protocol servers are rapidly becoming the standard way for LLM assistants to reach scientific resources, and a community call has recently argued for MCP-enabled bioinformatics web services for LLM-driven discovery [@mcpmed]. The emerging ecosystem already covers two layers: *data access*, where MCP servers wrap biomedical databases [@biomcp], and *analysis planning*, where AI agents propose multi-step analyses [@biomni; @autoba]. The layer that remains underserved is *execution with trust*: actually running a reproducible pipeline and returning results whose provenance can be independently checked. An assistant that "runs an analysis" is only scientifically useful if the result is not a black box, computational reproducibility and provenance are longstanding requirements of the field [@nfcore], and they become more acute when a non-deterministic model is orchestrating the work.

FlowProof is aimed at bioinformaticians and platform engineers who want to expose pipelines to AI assistants without surrendering reproducibility, and at researchers evaluating how MCP can be used for trustworthy, auditable computational analysis. Its reproducibility claims are evaluated rather than asserted (see below), and the code, evaluation scripts, and protocol are archived at a permanent DOI [@flowproof-archive].

# State of the field

Execution over MCP and standards-based provenance are not untouched ground. The Seqera MCP server exposes the Seqera Platform to MCP clients so an assistant can launch and monitor Nextflow pipelines, and the `nf-prov` plugin serialises Nextflow runs as Workflow Run RO-Crates. FlowProof differs on three axes those leave open: independence from any single engine or hosted control plane (its provenance emitter sits above a backend interface, not inside the engine, and it runs locally over stdio with no service account); an explicit, enforced boundary on the values a non-deterministic model substitutes into a command; and provenance retrievable through the same interface that issued the run. Rather than adding another database wrapper or planning agent, it gives an LLM a disciplined execution surface: pipelines are versioned and registered, execution is delegated to Nextflow, and each run produces a standards-based provenance record instead of a bespoke log. The design deliberately separates the hosted convenience surface from real analysis: the hosted server runs a lightweight demonstration pipeline for real and refuses heavier reference-data workflows, directing the user to run them locally where data and compute reside, so a demonstration is never mistaken for a production result.

# Software design

FlowProof is layered so that provenance and safety do not depend on any single execution engine. A runner-agnostic core defines a backend interface; a dependency-free backend serves development and continuous integration, while a Nextflow [@nextflow] backend runs real workflows. Pipelines are registry-driven: each is described by a manifest declaring its parameters and outputs, so short-read and long-read pipelines coexist and new ones are added without modifying the server. Between the model and the shell sits a command-assembly boundary that validates every substituted value and executes the argument vector without a shell interpreter. The provenance emitter sits above the backend interface, so the Workflow Run RO-Crate [@wfrun-rocrate] is produced identically regardless of which backend ran the pipeline, and is retrievable through the same MCP interface that issued the run.

# Research impact statement

FlowProof targets the trust gap that opens when a non-deterministic model orchestrates scientific computation: it lets AI assistants run real bioinformatics pipelines while emitting standards-based, independently verifiable provenance, so an AI-produced result carries the exact recipe and fixity information needed to reproduce and audit it. By making reproducibility a checkable property of an AI-driven run rather than an assertion, it offers a template for trustworthy autonomous analysis that extends beyond bioinformatics to any domain where LLM agents execute consequential computation.

# Evaluation

The reproducibility claims are tested empirically; scripts and the protocol are in the repository. Across 20 repeated runs of the bundled long-read example on one host, and a run on a second host of a different operating system and processor architecture (macOS/arm64 and Ubuntu/x86_64), the output checksums were byte-identical. An independent verifier given only the crate recomputed and confirmed the recorded checksums and re-executed the pipeline from the crate's recorded parameters, reproducing both a default and a non-default run. Of four deliberately tampered crates, three were flagged (a mutated input, an altered recorded checksum, and an altered recorded parameter); the fourth, a swapped container reference, is undetectable for this pipeline because its default stage runs without a container, a limitation reported rather than hidden. Of 45 adversarial parameter strings submitted to the command-assembly boundary, 32 were rejected and none reached a shell interpreter (the argument vector is executed without a shell, and a canary a successful injection would create never appeared). The suite comprises 36 automated tests.

# Example provenance

Every run produces a Workflow Run RO-Crate. The excerpt below is taken verbatim from a real run of the bundled Oxford Nanopore pipeline (the complete crate is included in the repository). It records the executed action, the exact tool version, and SHA-256 checksums of the input and output, so a third party can independently confirm what was run and reproduce the result byte-for-byte.

```json
{ "@id": "#run", "@type": "CreateAction",
  "instrument": { "@id": "ont-read-stats" },
  "object": [{ "@id": "ont_sample.fastq" }, { "@id": "#param-genome_size" }],
  "result": [{ "@id": "results/read_stats.txt" }],
  "actionStatus": "http://schema.org/CompletedActionStatus" }
{ "@id": "#tool-nextflow", "@type": "SoftwareApplication",
  "name": "nextflow", "version": "26.04.6" }
{ "@id": "#param-genome_size", "@type": "PropertyValue",
  "name": "genome_size", "value": "5m" }
{ "@id": "ont_sample.fastq", "@type": "File", "name": "reads",
  "contentSize": 120020,
  "sha256": "285a12b2d6dee106c3f7f30bf31582f6c2cd9546796997236e563888de498702" }
{ "@id": "results/read_stats.txt", "@type": "File",
  "contentSize": 59,
  "sha256": "c70ab03d12b9611d218bfa686d1e6d1788f2585d9aaab337c22de73f9d23eee2" }
```

# Acknowledgements

We thank the maintainers of Nextflow, nf-core, and the RO-Crate community, whose standards FlowProof builds upon.

# References
