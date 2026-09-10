"""Canonical, scope-aware cache identities for analytical responses."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


class CacheAuthorizationError(ValueError):
    """Raised when a cache operation lacks a trusted authenticated scope."""


def authenticated_cache_scope(username: str, role: str = "viewer") -> str:
    """Return a non-forgeable-by-callers cache scope for an authenticated user.

    This is an isolation label, not an authorization decision. Callers must
    perform their normal server-side authorization before invoking this helper.
    Anonymous callers must bypass cache reads and writes rather than becoming
    members of the public cache scope.
    """
    identity = str(username or "").strip().lower()
    if not identity:
        raise CacheAuthorizationError("authenticated username is required for cache access")
    normalized_role = str(role or "viewer").strip().lower() or "viewer"
    digest = hashlib.sha256(f"{identity}:{normalized_role}".encode("utf-8")).hexdigest()
    return f"principal:{digest}"


def build_cache_key(
    *,
    dataset_fingerprint: str,
    command: str,
    tenant_id: str = "",
    model: str = "",
    filters: Mapping[str, Any] | None = None,
    schema_version: str = "v1",
) -> str:
    """Return a deterministic cache identity with explicit data/scope inputs."""
    if not str(dataset_fingerprint).strip():
        raise ValueError("dataset_fingerprint is required")
    if not str(command).strip():
        raise ValueError("command is required")
    payload = {
        "schema_version": schema_version,
        "dataset_fingerprint": str(dataset_fingerprint),
        "tenant_id": str(tenant_id or "public"),
        "command": str(command).strip(),
        "model": str(model).strip(),
        "filters": dict(filters or {}),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
