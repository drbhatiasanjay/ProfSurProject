"""Performance architecture contracts for cache identity and scope."""

import pytest

from models.cache_keys import CacheAuthorizationError, authorized_cache_scope, build_cache_key


def test_same_identity_replays_and_ordered_filters_are_canonical():
    first = build_cache_key(
        dataset_fingerprint="sha256:data-a", command="regress y x",
        tenant_id="tenant-a", model="model-1", filters={"year": [2020, 2021], "stage": "Maturity"},
    )
    second = build_cache_key(
        dataset_fingerprint="sha256:data-a", command=" regress y x ",
        tenant_id="tenant-a", model="model-1", filters={"stage": "Maturity", "year": [2020, 2021]},
    )
    assert first == second


@pytest.mark.parametrize(
    "change",
    [
        {"dataset_fingerprint": "sha256:data-b"},
        {"tenant_id": "tenant-b"},
        {"command": "regress y z"},
        {"model": "model-2"},
        {"filters": {"year": [2021]}},
    ],
)
def test_scope_or_specification_changes_never_collide(change):
    base = {"dataset_fingerprint": "sha256:data-a", "command": "regress y x", "tenant_id": "tenant-a", "model": "model-1", "filters": {"year": [2020]}}
    changed = {**base, **change}
    assert build_cache_key(**base) != build_cache_key(**changed)


def test_missing_identity_inputs_fail_closed():
    with pytest.raises(ValueError):
        build_cache_key(dataset_fingerprint="", command="regress y x")
    with pytest.raises(ValueError):
        build_cache_key(dataset_fingerprint="sha256:data-a", command="")


def test_anonymous_cache_scope_fails_closed():
    with pytest.raises(CacheAuthorizationError):
        authorized_cache_scope("")


def test_authenticated_scope_is_stable_but_role_isolated():
    assert authorized_cache_scope("Alice", "viewer") == authorized_cache_scope("alice", "viewer")
    assert authorized_cache_scope("alice", "viewer") != authorized_cache_scope("alice", "researcher")


def test_cache_policy_denies_unknown_roles_and_empty_dataset_scope():
    with pytest.raises(CacheAuthorizationError):
        authorized_cache_scope("alice", "superuser")
    with pytest.raises(CacheAuthorizationError):
        authorized_cache_scope("alice", "viewer", dataset_scope="")
