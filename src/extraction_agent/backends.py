from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path

from deepagents import FilesystemPermission
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend

# Verified against the installed deepagents==0.7.15:
# - FilesystemBackend(root_dir, virtual_mode=True, max_file_size_mb=10) — no
#   permission/read-only kwarg; read-only enforcement is a `permissions=`
#   rule passed to create_deep_agent instead (see agents/triage.py).
# - CompositeBackend(default: BackendProtocol, routes: dict[str, BackendProtocol])
#   — NOT `backends={...}`. `default` catches anything outside the mounted
#   routes.
# - virtual_mode=True also blocks path traversal (`..`, `~`) and absolute
#   paths outside root_dir — real guardrail, not just "virtual path
#   semantics", worth keeping for both mounts below.
SKILLS_ROOT = Path(__file__).parent.parent.parent / "skills"


class InMemoryObjectStore:
    """Stand-in for the S3-compatible object store described in the
    architecture doc. Same put/get/list shape as the eventual real client so
    swapping it out later doesn't touch calling code.

    TODO(prod): replace with a boto3-based S3-compatible client. This class
    is dev/test-only and loses all data on process exit.
    """

    def __init__(self) -> None:
        self._files: dict[str, bytes] = {}
        self._lock = threading.Lock()

    def put(self, key: str, data: bytes) -> None:
        with self._lock:
            self._files[key] = data

    def get(self, key: str) -> bytes:
        with self._lock:
            return self._files[key]

    def list(self, prefix: str = "") -> list[str]:
        with self._lock:
            return [k for k in self._files if k.startswith(prefix)]

    def delete(self, key: str) -> None:
        with self._lock:
            self._files.pop(key, None)


@dataclass
class PipelineBackends:
    """Everything a run's agents need to read/write, wired per the
    CompositeBackend split in the architecture doc: skills are a read-only*
    filesystem mount, scratch/extraction-store data is a writable filesystem
    mount over the run's own temp dir (see ExtractionStore — no durable
    checkpointer, that requirement was dropped), and raw input files live in
    object storage (never container-local disk).

    * enforced via a `permissions` deny-write rule on /skills/** passed to
    create_deep_agent, not at the backend level — see agents/triage.py.
    """

    composite: CompositeBackend
    object_store: InMemoryObjectStore = field(default_factory=InMemoryObjectStore)


def build_skills_backend() -> FilesystemBackend:
    return FilesystemBackend(root_dir=str(SKILLS_ROOT), virtual_mode=True)


def build_scratch_backend(scratch_dir: str | Path) -> FilesystemBackend:
    return FilesystemBackend(root_dir=str(scratch_dir), virtual_mode=True)


def build_backends(scratch_dir: str | Path) -> PipelineBackends:
    """Dev/test wiring: writable filesystem backend over the run's scratch
    dir + local-disk skills backend + in-memory object store.

    TODO(prod): swap InMemoryObjectStore for a real S3-compatible client,
    per the architecture doc's backend strategy. No durable checkpointer is
    needed — state management inside a single run was explicitly decided
    not to require LangGraph checkpointer persistence.
    """
    composite = CompositeBackend(
        default=StateBackend(),
        routes={
            "/skills/": build_skills_backend(),
            "/scratch/": build_scratch_backend(scratch_dir),
        },
    )
    return PipelineBackends(composite=composite)


def to_virtual_skill_path(skill_dir: Path | None) -> str:
    """Convert a real skills/<agent>/vN directory into the virtual path
    `skills=[...]` expects, relative to the /skills/ mount above (e.g.
    "/skills/triage/v1/"). Verified empirically against deepagents' skill
    discovery (scans a source's immediate subdirectories for SKILL.md)."""
    if skill_dir is None:
        raise ValueError("profile has no skill path configured for this agent")
    relative = skill_dir.resolve().relative_to(SKILLS_ROOT.resolve())
    return f"/skills/{relative.as_posix()}/"


def skills_deny_write_permission() -> FilesystemPermission:
    return FilesystemPermission(operations=["write"], paths=["/skills/**"], mode="deny")
