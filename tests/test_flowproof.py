from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from flowproof import RunManager, RunStatus, registry
from flowproof.hashing import sha256_file
from flowproof.runner import MockBackend, NextflowBackend, UnsafeValue


def test_registry_has_seed_pipelines():
    ids = {m.id for m in registry.list()}
    assert {"variant-call-short", "assembly-ont"} <= ids


def test_registry_has_nf_core_pipelines():
    ids = {m.id for m in registry.list()}
    assert {"rnaseq", "fetchngs", "viralrecon"} <= ids


def test_all_pipelines_build_safe_nextflow_commands(tmp_path: Path):
    backend = NextflowBackend()
    dummy = {
        "rnaseq": ({"samplesheet": "s.csv"}, {"genome": "GRCh38", "aligner": "star_salmon"}),
        "fetchngs": ({"ids": "ids.csv"}, {"nf_core_pipeline": "rnaseq"}),
        "viralrecon": ({"samplesheet": "s.csv"}, {"platform": "illumina", "protocol": "amplicon", "genome": "MN908947.3"}),
    }
    for pid, (inputs, params) in dummy.items():
        manifest = registry.get(pid)
        command = backend.build_command(manifest, tmp_path, inputs, params)
        assert command[0] == "nextflow"
        assert all(isinstance(token, str) and token for token in command)


def test_describe_has_short_and_long():
    read_types = {m.id: m.read_type.value for m in registry.list()}
    assert read_types["variant-call-short"] == "short"
    assert read_types["assembly-ont"] == "long"


def test_mock_run_succeeds_and_emits_outputs(tmp_path: Path):
    manager = RunManager(tmp_path, backend=MockBackend())
    record = manager.start_run(
        "variant-call-short",
        inputs={"samplesheet": "samples.csv"},
        params={"tools": "deepvariant"},
    )
    assert record.status is RunStatus.SUCCEEDED
    assert record.result is not None
    assert len(record.result.output_files) >= 1


def test_defaults_are_applied(tmp_path: Path):
    manager = RunManager(tmp_path, backend=MockBackend())
    record = manager.start_run("variant-call-short", inputs={"samplesheet": "s.csv"})
    assert record.params["genome"] == "GATK.GRCh38"
    assert record.params["tools"] == "strelka"


def test_output_checksums_are_real(tmp_path: Path):
    manager = RunManager(tmp_path, backend=MockBackend())
    record = manager.start_run("assembly-ont", inputs={"reads": "ont.fastq"})
    output = record.result.output_files[0]
    on_disk = Path(record.run_dir) / output.path
    assert sha256_file(on_disk) == output.sha256


def test_argv_keeps_each_user_value_a_single_element(tmp_path: Path):
    backend = NextflowBackend()
    manifest = registry.get("variant-call-short")
    argv = backend.build_command(
        manifest, tmp_path, {"samplesheet": "samples.csv"}, {"genome": "GRCh38", "tools": "strelka"}
    )
    assert "samples.csv" in argv
    assert argv.count("--input") == 1


def test_flag_smuggling_is_rejected(tmp_path: Path):
    backend = NextflowBackend()
    manifest = registry.get("variant-call-short")
    with pytest.raises(UnsafeValue):
        backend.build_command(
            manifest, tmp_path, {"samplesheet": "--with-trace"}, {"tools": "strelka"}
        )


def test_space_injection_cannot_add_arguments(tmp_path: Path):
    backend = NextflowBackend()
    manifest = registry.get("variant-call-short")
    with pytest.raises(UnsafeValue):
        backend.build_command(
            manifest, tmp_path, {"samplesheet": "a.csv --resume"}, {"tools": "strelka"}
        )


def test_provenance_crate_is_valid(tmp_path: Path):
    manager = RunManager(tmp_path, backend=MockBackend())
    record = manager.start_run("assembly-ont", inputs={"reads": "ont.fastq"})
    crate = json.loads(Path(record.provenance_path).read_text())
    assert "@graph" in crate
    ids = {node["@id"] for node in crate["@graph"]}
    assert "assembly-ont" in ids
    assert f"#run-{record.run_id}" in ids
    workflow = next(n for n in crate["@graph"] if n["@id"] == "assembly-ont")
    assert "ComputationalWorkflow" in workflow["@type"]
    outputs = [n for n in crate["@graph"] if n.get("@type") == "File" and "sha256" in n]
    assert any(n["sha256"] == record.result.output_files[0].sha256 for n in outputs)


NEXTFLOW = shutil.which("nextflow")
TESTDATA = Path(__file__).resolve().parents[1] / "testdata" / "ont_sample.fastq"


@pytest.mark.skipif(NEXTFLOW is None, reason="nextflow not installed")
def test_real_nextflow_run_end_to_end(tmp_path: Path):
    manager = RunManager(tmp_path, backend=NextflowBackend(profile="standard"))
    record = manager.start_run("assembly-ont", inputs={"reads": str(TESTDATA)})
    assert record.status is RunStatus.SUCCEEDED, record.result.log if record.result else "no result"
    paths = [f.path for f in record.result.output_files]
    assert any("read_stats.txt" in p for p in paths)
    crate = json.loads(Path(record.provenance_path).read_text())
    assert any(n.get("name") == "nextflow" for n in crate["@graph"])
