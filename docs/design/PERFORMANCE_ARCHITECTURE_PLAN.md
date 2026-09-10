# Performance Architecture Plan

**Status:** SLICE 2 IMPLEMENTED — legacy callers and cache authorization boundary verified
**Date:** 2026-09-10
**Scope:** cache identity, isolation evidence, and measured optimization

**Research decision:** The formal Wave 6 challenge, topology, grammar,
authorization, migration, outage, and rollback plan is recorded in
[`PERFORMANCE_ARCHITECTURE_RESEARCH_AND_PLAN.md`](PERFORMANCE_ARCHITECTURE_RESEARCH_AND_PLAN.md).

## Approved now

1. Define one canonical cache identity from dataset fingerprint, tenant scope,
   command/specification, model/provider, and relevant filters.
2. Require explicit public-scope identity when no tenant is configured; never
   use a browser session ID as the sole cache identity.
3. Add cache hit/miss, latency, collision, and cross-scope tests before changing
   storage or callers.
4. Preserve backward-compatible cache reads and provide invalidation/versioning.
5. Produce GitHub-ready markdown evidence for every optimization.

## Deferred, not rejected

- Distributed cache (`diskcache`/Redis): requires deployment topology, locking,
  eviction, serialization, migration, outage fallback, and rollback decisions.
- AST parser: requires a complete Stata grammar, compatibility fixtures for all
  supported commands, error semantics, and a migration plan from the current
  parser. Regex hardening is not a substitute for that design.
- Fingerprint-only row-level security: a fingerprint detects dataset identity;
  it does not enforce authorization. Tenant/session authorization remains an
  independent boundary.

## Implementation sequence

1. Add canonical cache-key helper and red/green isolation tests.
2. Thread the helper through existing SQLite AI-cache callers without changing
   TTL or response semantics.
3. Add an authorization-before-cache boundary and scope-version context.
4. Measure baseline versus keyed-cache hit/miss latency.
5. Review evidence and only then design shared-worker storage.
6. Keep parser work as a separate Wave 6 slice with grammar fixtures.

## Slice 1 evidence

- Implemented: `models/cache_keys.py`.
- Focused cache tests: **15 passed, 8 warnings** including existing SQLite TTL
  and cache-hit coverage.
- Distributed storage and parser redesign remain deferred pending separate
  topology/grammar plans.

## Slice 2 evidence

- Authenticated page callers now pass a trusted username-derived scope into
  canonical cache identities.
- Anonymous direct adapter calls bypass cache reads and writes rather than
  entering the public scope.
- Existing SQLite cache schema, response behavior, and TTL defaults remain
  unchanged.
- Focused verification: **89 passed, 10 warnings** across cache, chatbot, and
  adapter compatibility tests.
