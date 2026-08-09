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
    id="assembly-ont",
    description="Oxford Nanopore long-read de novo assembly",
    read_type=ReadType.LONG,
    inputs=(
        PipelineInput("reads", "Oxford Nanopore long-read FASTQ"),
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
)


def register_builtin_pipelines() -> None:
    for manifest in (VARIANT_CALL_SHORT, ASSEMBLY_ONT):
        try:
            registry.register(manifest)
        except ValueError:
            pass


register_builtin_pipelines()
