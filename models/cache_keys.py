"""Canonical, scope-aware cache identities for analytical responses."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


class CacheAuthorizationError(ValueError):
    """Raised when a cache operation lacks a trusted authenticated scope."""


_CACHE_ALLOWED_ROLES = frozenset({"admin", "researcher", "viewer", "cfo", "guest"})


def authorized_cache_scope(username: str, role: str = "viewer", *, dataset_scope: str = "shared-analytical-panel") -> str:
    """Return a cache scope only after the explicit MVP policy passes.

    The MVP policy permits authenticated principals with approved application
    roles to access the shared analytical panel. This is deny-by-default and
    must be extended with dataset entitlements before tenant-private data is
    introduced. The result remains an isolation label, not the policy itself.
    """
    identity = str(username or "").strip().lower()
    if not identity:
        raise CacheAuthorizationError("authenticated username is required for cache access")
    normalized_role = str(role or "viewer").strip().lower() or "viewer"
    if normalized_role not in _CACHE_ALLOWED_ROLES:
        raise CacheAuthorizationError("application role is not authorized for cache access")
    scope = str(dataset_scope or "").strip()
    if not scope:
        raise CacheAuthorizationError("dataset authorization scope is required")
    digest = hashlib.sha256(f"{identity}:{normalized_role}:{scope}".encode("utf-8")).hexdigest()
    return f"principal:{digest}"


authenticated_cache_scope = authorized_cache_scope


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
