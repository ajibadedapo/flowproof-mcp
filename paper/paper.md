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
  - name: Independent researcher
    index: 1
date: 13 August 2026
bibliography: paper.bib
---

# Summary

FlowProof is a Model Context Protocol (MCP) server that lets a large language model (LLM) assistant run a bioinformatics pipeline and receive results whose provenance can be independently verified. Every run emits a Workflow Run RO-Crate [@wfrun-rocrate] recording the pipeline version, container image, tool versions, parameters, and SHA-256 checksums of every input and output, so an AI-driven analysis ships with the exact recipe and fixity information needed to reproduce it. Pipelines are executed through a runner-agnostic core: a dependency-free backend supports development and continuous integration, while a Nextflow [@nextflow] backend runs real workflows. FlowProof is registry-driven, so short-read and long-read (Oxford Nanopore) pipelines coexist and new ones are added by manifest without modifying the server. It is distributed as an open-source Python package (`pip install flowproof-mcp`) and exposes six MCP tools (list, describe, run, status, results, and provenance), usable by any MCP-capable assistant over a local (stdio) or hosted (HTTP) transport.

# Statement of need

Model Context Protocol servers are rapidly becoming the standard way for LLM assistants to reach scientific resources, and a community call has recently argued for MCP-enabled bioinformatics web services for LLM-driven discovery [@mcpmed]. The emerging ecosystem already covers two layers: *data access*, where MCP servers wrap biomedical databases [@biomcp], and *analysis planning*, where AI agents propose multi-step analyses [@biomni; @autoba]. The layer that remains underserved is *execution with trust*: actually running a reproducible pipeline and returning results whose provenance can be independently checked. An assistant that "runs an analysis" is only scientifically useful if the result is not a black box, computational reproducibility and provenance are longstanding requirements of the field [@nfcore], and they become more acute when a non-deterministic model is orchestrating the work.

FlowProof addresses this gap. Rather than adding another database wrapper or planning agent, it gives an LLM a disciplined execution surface: pipelines are versioned and registered, runs are containerizable through Nextflow, and each run produces a standards-based provenance record instead of a bespoke log. Because provenance is emitted as a Workflow Run RO-Crate, it is interoperable with existing workflow-provenance tooling rather than locked to FlowProof. The design deliberately separates the hosted convenience surface from real analysis: the hosted server runs a lightweight demonstration pipeline for real and refuses heavier reference-data workflows with a message directing the user to run them locally, where data and compute reside, so a demonstration is never mistaken for a production result.

FlowProof is aimed at bioinformaticians and platform engineers who want to expose pipelines to AI assistants without surrendering reproducibility, and at researchers evaluating how MCP can be used for trustworthy, auditable computational analysis. By making every AI-orchestrated run reproducible byte-for-byte and independently verifiable, it contributes the missing execution-and-trust component of the MCP-for-bioinformatics stack.

# Example provenance

Every run produces a Workflow Run RO-Crate. The excerpt below is taken verbatim from a real run of the bundled Oxford Nanopore pipeline (the complete crate is included in the repository). It records the executed action, the exact tool version, and SHA-256 checksums of the input and output, so a third party can independently confirm what was run and reproduce the result byte-for-byte.

```json
{ "@id": "#run", "@type": "CreateAction",
  "instrument": { "@id": "assembly-ont" },
  "object": [{ "@id": "ont_sample.fastq" }],
  "result": [{ "@id": "results/read_stats.txt" }],
  "actionStatus": "http://schema.org/CompletedActionStatus" }
{ "@id": "#tool-nextflow", "@type": "SoftwareApplication",
  "name": "nextflow", "version": "26.04.6" }
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
