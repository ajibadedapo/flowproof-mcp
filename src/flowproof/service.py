from __future__ import annotations

import uuid
from pathlib import Path

from .models import RunRecord, RunStatus
from .provenance import write_provenance
from .registry import Registry
from .registry import registry as default_registry
from .runner import DEFAULT_SAMPLE, MockBackend, RunBackend


class RunManager:
    def __init__(
        self,
        base_dir: str | Path,
        backend: RunBackend | None = None,
        reg: Registry | None = None,
    ) -> None:
        self.base_dir = Path(base_dir)
        self.backend: RunBackend = backend or MockBackend()
        self.registry = reg or default_registry
        self._runs: dict[str, RunRecord] = {}

    def start_run(
        self,
        pipeline_id: str,
        inputs: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> RunRecord:
        manifest = self.registry.get(pipeline_id)
        resolved = {p.name: p.default for p in manifest.params if p.default is not None}
        resolved.update(params or {})
        resolved_inputs = dict(inputs or {})
        if pipeline_id == "ont-read-stats" and not resolved_inputs.get("reads") and DEFAULT_SAMPLE:
            resolved_inputs["reads"] = str(DEFAULT_SAMPLE)
        run_id = uuid.uuid4().hex[:12]
        run_dir = (self.base_dir / run_id).resolve()
        run_dir.mkdir(parents=True, exist_ok=True)
        record = RunRecord(
            run_id=run_id,
            pipeline_id=pipeline_id,
            inputs=resolved_inputs,
            params=resolved,
            run_dir=str(run_dir),
            status=RunStatus.RUNNING,
        )
        self._runs[run_id] = record
        result = self.backend.run(manifest, run_dir, record.inputs, record.params)
        record.result = result
        record.status = result.status
        record.provenance_path = str(
            write_provenance(manifest, record, result, run_dir)
        )
        return record

    def get(self, run_id: str) -> RunRecord:
        return self._runs[run_id]
