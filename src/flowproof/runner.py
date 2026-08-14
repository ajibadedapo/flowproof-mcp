from __future__ import annotations

import re
import shlex
import subprocess
from pathlib import Path
from typing import Protocol

from .hashing import sha256_file
from .models import OutputFile, PipelineManifest, RunResult, RunStatus

_SAFE_VALUE = re.compile(r"[A-Za-z0-9._/\-]+")
_PLACEHOLDER = re.compile(r"\{([A-Za-z0-9_]+)\}")


class UnsafeValue(ValueError):
    pass


def validate_value(name: str, value: str) -> str:
    if not _SAFE_VALUE.fullmatch(value) or value.startswith("-") or ".." in value:
        raise UnsafeValue(f"{name}={value!r} is not an allowed pipeline value")
    return value


def _resolve_token(token: str, substitutions: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in substitutions:
            raise UnsafeValue(f"unresolved placeholder in command template: {{{name}}}")
        return substitutions[name]

    return _PLACEHOLDER.sub(replace, token)


class RunBackend(Protocol):
    def run(
        self,
        manifest: PipelineManifest,
        run_dir: Path,
        inputs: dict[str, str],
        params: dict[str, str],
    ) -> RunResult: ...


def collect_outputs(run_dir: Path, output_globs: tuple[str, ...]) -> list[OutputFile]:
    outputs: list[OutputFile] = []
    seen: set[Path] = set()
    for pattern in output_globs:
        for match in sorted(run_dir.glob(pattern)):
            if not match.is_file() or match in seen:
                continue
            seen.add(match)
            outputs.append(
                OutputFile(
                    path=str(match.relative_to(run_dir)),
                    sha256=sha256_file(match),
                    size_bytes=match.stat().st_size,
                )
            )
    return outputs


class MockBackend:
    def run(
        self,
        manifest: PipelineManifest,
        run_dir: Path,
        inputs: dict[str, str],
        params: dict[str, str],
    ) -> RunResult:
        results_dir = run_dir / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        summary = results_dir / "run_summary.txt"
        lines = [f"pipeline={manifest.id}"]
        lines += [f"input:{name}={value}" for name, value in sorted(inputs.items())]
        lines += [f"param:{name}={value}" for name, value in sorted(params.items())]
        summary.write_text("\n".join(lines) + "\n")
        return RunResult(
            status=RunStatus.SUCCEEDED,
            output_files=collect_outputs(run_dir, ("results/*",)),
            log="mock backend: deterministic run complete",
            tool_versions={"mock": "1.0.0"},
            container_digests={manifest.container: "sha256:mock"},
        )


def _default_pipeline_dir() -> Path:
    bundled = Path(__file__).resolve().parent / "_pipelines"
    if bundled.is_dir():
        return bundled
    return Path(__file__).resolve().parents[2] / "pipelines"


DEFAULT_PIPELINE_DIR = _default_pipeline_dir()


def _default_sample() -> Path | None:
    candidates = (
        DEFAULT_PIPELINE_DIR / "assembly-ont" / "ont_sample.fastq",
        Path(__file__).resolve().parents[2] / "testdata" / "ont_sample.fastq",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


DEFAULT_SAMPLE = _default_sample()


class NextflowBackend:
    def __init__(
        self,
        executable: str = "nextflow",
        profile: str = "standard",
        pipeline_dir: Path | None = None,
    ) -> None:
        self.executable = executable
        self.profile = profile
        self.pipeline_dir = pipeline_dir or DEFAULT_PIPELINE_DIR

    def build_command(
        self,
        manifest: PipelineManifest,
        run_dir: Path,
        inputs: dict[str, str],
        params: dict[str, str],
    ) -> list[str]:
        substitutions = {
            "run_dir": str(run_dir),
            "profile": self.profile,
            "pipeline_dir": str(self.pipeline_dir),
        }
        for key, value in inputs.items():
            substitutions[f"input_{key}"] = validate_value(f"input_{key}", value)
        for key, value in params.items():
            substitutions[f"param_{key}"] = validate_value(f"param_{key}", value)

        argv: list[str] = [self.executable]
        for token in shlex.split(manifest.command_template):
            argv.append(_resolve_token(token, substitutions))
        return argv

    def run(
        self,
        manifest: PipelineManifest,
        run_dir: Path,
        inputs: dict[str, str],
        params: dict[str, str],
    ) -> RunResult:
        run_dir.mkdir(parents=True, exist_ok=True)
        command = self.build_command(manifest, run_dir, inputs, params)
        completed = subprocess.run(
            command,
            cwd=run_dir,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            return RunResult(
                status=RunStatus.FAILED,
                log=completed.stdout + completed.stderr,
                error=f"nextflow exited {completed.returncode}",
            )
        return RunResult(
            status=RunStatus.SUCCEEDED,
            output_files=collect_outputs(run_dir, manifest.output_globs),
            log=completed.stdout,
            tool_versions={"nextflow": self._nextflow_version()},
            container_digests={manifest.container: ""},
        )

    def _nextflow_version(self) -> str:
        try:
            out = subprocess.run(
                [self.executable, "-version"],
                capture_output=True,
                text=True,
            )
            for line in out.stdout.splitlines():
                if "version" in line.lower():
                    return line.strip()
        except FileNotFoundError:
            return "unknown"
        return "unknown"
