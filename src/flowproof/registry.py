from __future__ import annotations

from .models import PipelineManifest


class PipelineNotFound(KeyError):
    pass


class Registry:
    def __init__(self) -> None:
        self._pipelines: dict[str, PipelineManifest] = {}

    def register(self, manifest: PipelineManifest) -> None:
        if manifest.id in self._pipelines:
            raise ValueError(f"pipeline already registered: {manifest.id}")
        self._pipelines[manifest.id] = manifest

    def get(self, pipeline_id: str) -> PipelineManifest:
        try:
            return self._pipelines[pipeline_id]
        except KeyError as exc:
            raise PipelineNotFound(pipeline_id) from exc

    def list(self) -> list[PipelineManifest]:
        return sorted(self._pipelines.values(), key=lambda m: m.id)


registry = Registry()
