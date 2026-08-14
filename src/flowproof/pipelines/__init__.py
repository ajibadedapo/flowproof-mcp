from __future__ import annotations

from ..models import PipelineInput, PipelineManifest, PipelineParam, ReadType
from ..registry import registry

VARIANT_CALL_SHORT = PipelineManifest(
    id="variant-call-short",
    description="Short-read QC to germline variant calling",
    read_type=ReadType.SHORT,
    inputs=(
        PipelineInput("samplesheet", "CSV samplesheet of short-read FASTQ files"),
    ),
    params=(
        PipelineParam("genome", "Reference genome key", "GATK.GRCh38"),
        PipelineParam("tools", "Variant caller", "strelka"),
    ),
    output_globs=("results/**/*.vcf.gz", "results/**/*.vcf"),
    command_template=(
        "run nf-core/sarek -r 3.4.0 -profile {profile} "
        "--input {input_samplesheet} --outdir {run_dir}/results "
        "--genome {param_genome} --tools {param_tools}"
    ),
    container="nfcore/sarek:3.4.0",
)

ASSEMBLY_ONT = PipelineManifest(
    id="ont-read-stats",
    description="Oxford Nanopore long-read read statistics (QC); optional Flye assembly stage",
    read_type=ReadType.LONG,
    inputs=(
        PipelineInput("reads", "Oxford Nanopore long-read FASTQ. Omit to use the built-in demo sample."),
    ),
    params=(
        PipelineParam("genome_size", "Estimated genome size, e.g. 5m", "5m"),
    ),
    output_globs=("results/read_stats.txt", "results/*.fasta", "results/**/*.fasta"),
    command_template=(
        "-q run {pipeline_dir}/assembly-ont/main.nf -profile {profile} "
        "--reads {input_reads} --genome_size {param_genome_size} "
        "--outdir {run_dir}/results"
    ),
    container="staphb/flye:2.9.3",
    hosted_runnable=True,
)


RNASEQ = PipelineManifest(
    id="rnaseq",
    description="Short-read RNA-seq quantification (QC, trimming, alignment, gene counts)",
    read_type=ReadType.SHORT,
    inputs=(
        PipelineInput("samplesheet", "CSV samplesheet of RNA-seq FASTQ files"),
    ),
    params=(
        PipelineParam("genome", "Reference genome key", "GRCh38"),
        PipelineParam("aligner", "Alignment/quantification tool", "star_salmon"),
    ),
    output_globs=("results/**/*.tsv", "results/**/salmon.merged.gene_counts.tsv"),
    command_template=(
        "run nf-core/rnaseq -r 3.14.0 -profile {profile} "
        "--input {input_samplesheet} --outdir {run_dir}/results "
        "--genome {param_genome} --aligner {param_aligner}"
    ),
    container="nfcore/rnaseq:3.14.0",
)

FETCHNGS = PipelineManifest(
    id="fetchngs",
    description="Fetch raw sequencing reads and metadata from public archives (SRA/ENA/GEO)",
    read_type=ReadType.SHORT,
    inputs=(
        PipelineInput("ids", "CSV of public database accessions (e.g. SRR/ERR/GSE ids)"),
    ),
    params=(
        PipelineParam("nf_core_pipeline", "Downstream pipeline samplesheet format", "rnaseq"),
    ),
    output_globs=("results/**/*.fastq.gz", "results/**/samplesheet.csv"),
    command_template=(
        "run nf-core/fetchngs -r 1.12.0 -profile {profile} "
        "--input {input_ids} --outdir {run_dir}/results "
        "--nf_core_pipeline {param_nf_core_pipeline}"
    ),
    container="nfcore/fetchngs:1.12.0",
)

VIRALRECON = PipelineManifest(
    id="viralrecon",
    description="Viral genome reconstruction and variant calling from short-read amplicon data",
    read_type=ReadType.SHORT,
    inputs=(
        PipelineInput("samplesheet", "CSV samplesheet of viral amplicon FASTQ files"),
    ),
    params=(
        PipelineParam("platform", "Sequencing platform", "illumina"),
        PipelineParam("protocol", "Library protocol", "amplicon"),
        PipelineParam("genome", "Reference genome accession", "MN908947.3"),
    ),
    output_globs=("results/**/*.fa", "results/**/*.vcf.gz"),
    command_template=(
        "run nf-core/viralrecon -r 2.6.0 -profile {profile} "
        "--input {input_samplesheet} --outdir {run_dir}/results "
        "--platform {param_platform} --protocol {param_protocol} --genome {param_genome}"
    ),
    container="nfcore/viralrecon:2.6.0",
)


def register_builtin_pipelines() -> None:
    for manifest in (VARIANT_CALL_SHORT, ASSEMBLY_ONT, RNASEQ, FETCHNGS, VIRALRECON):
        try:
            registry.register(manifest)
        except ValueError:
            pass


register_builtin_pipelines()
