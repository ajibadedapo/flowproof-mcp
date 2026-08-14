from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ReadType(str, Enum):
    SHORT = "short"
    LONG = "long"


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class PipelineInput:
    name: str
    description: str
    required: bool = True


@dataclass(frozen=True)
class PipelineParam:
    name: str
    description: str
    default: str | None = None


@dataclass(frozen=True)
class PipelineManifest:
    id: str
    description: str
    read_type: ReadType
    inputs: tuple[PipelineInput, ...]
    params: tuple[PipelineParam, ...]
    output_globs: tuple[str, ...]
    command_template: str
    container: str
    hosted_runnable: bool = False


@dataclass(frozen=True)
class OutputFile:
    path: str
    sha256: str
    size_bytes: int


@dataclass
class RunResult:
    status: RunStatus
    output_files: list[OutputFile] = field(default_factory=list)
    log: str = ""
    tool_versions: dict[str, str] = field(default_factory=dict)
    container_digests: dict[str, str] = field(default_factory=dict)
    error: str | None = None


@dataclass
class RunRecord:
    run_id: str
    pipeline_id: str
    inputs: dict[str, str]
    params: dict[str, str]
    run_dir: str
    status: RunStatus = RunStatus.QUEUED
    result: RunResult | None = None
    provenance_path: str | None = None
