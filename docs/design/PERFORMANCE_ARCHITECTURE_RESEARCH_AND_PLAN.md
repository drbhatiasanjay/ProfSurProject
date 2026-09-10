# Wave 6 Performance Architecture: Research, Challenge, and Execution Plan

**Status:** APPROVED FOR DESIGN AND LEGACY-CALLER SLICE; DISTRIBUTED CACHE, AST, AND AUTHORIZATION ENFORCEMENT GATED
**Date:** 2026-09-10
**Owner:** Codex orchestrator
**Scope:** AI response caching, Stata command parsing, data authorization, and legacy integration

## Executive decision

The current cache-key slice is sound and remains the baseline. It identifies a
result by dataset fingerprint, tenant scope, command/specification, model,
filters, and schema version. It must now be threaded through every legacy caller
before storage is changed.

The following proposals are not approved as unconditional implementation tasks:

1. **Distributed cache:** not approved for immediate production rollout. A
   backend choice without topology, lock semantics, eviction, migration,
   outage, observability, and rollback design is incomplete.
2. **Full AST parser rewrite:** not approved as a big-bang replacement. Stata
   syntax is broad and the existing parser has compatibility behavior that must
   be captured before migration.
3. **Fingerprint-only security:** rejected as a security control. A fingerprint
   is an integrity and cache-identity value, not an authorization decision.
4. **Legacy caller integration:** approved as the next scoped implementation
   slice, with authorization context made explicit at the same boundary.

## Adversarial review of the proposals

### Distributed cache

The attractive proposal is “replace the local cache with Redis or diskcache.”
That omits the hard parts:

- A local SQLite/WAL cache can support multiple processes on one machine, but
  SQLite WAL uses shared memory and does not work on a network filesystem; it
  also permits only one writer at a time. It is therefore a local-host tier,
  not a multi-host distributed cache.
- Redis eviction is a correctness concern when cached results have different
  sensitivity, size, or freshness. `maxmemory`, policy, TTL, value size, and
  reserved replication/persistence memory must be explicit.
- A lock that prevents duplicate computation is not automatically a correctness
  lock. Lease expiry, process pauses, clock behavior, failover, and stale lock
  owners can produce overlapping writers. Fencing tokens are required if a
  lock protects a mutable or externally visible resource.
- A cache outage must degrade to recomputation or a typed “temporarily
  unavailable” result. It must never bypass authorization or return an entry
  from a broader scope.

**Decision:** implement a backend abstraction and local integration first;
select Redis only for a measured multi-worker deployment need. Treat cache
population as cache-aside optimization, not a source of truth.

### AST parser

The attractive proposal is “replace regex with Lark.” That is directionally
correct but operationally incomplete:

- The grammar must cover the commands actually supported by this repository,
  not an aspirational subset.
- Lexer precedence and ambiguity matter for quoted strings, comments, options,
  nested parentheses, factor variables, lags, `if`/`in`, and continuation
  markers.
- A parser migration can silently change command semantics even when parsing
  succeeds. Existing parsed dictionaries and typed errors are compatibility
  contracts.
- Unbounded input length, nesting, or ambiguous parses can become a denial of
  service. The parser needs limits and deterministic failure behavior.

**Decision:** build a bounded grammar in shadow mode. Compare its normalized
  AST with the legacy parser on a golden corpus, then enable it command by
  command behind a feature flag. Keep the legacy adapter until compatibility
  gates pass.

### Fingerprint-only security

A dataset fingerprint answers “which bytes/rows/schema were represented?” It
does not answer “may this principal access those bytes?” Identical public data
may legitimately have the same fingerprint, and an attacker who can obtain
the data can compute the same fingerprint. Conversely, a changed authorization
scope may require a different result even when the underlying data is
identical.

**Decision:** authorization is checked before cache lookup and before data
materialization. The MVP policy permits authenticated users with approved
application roles to access the shared analytical panel. Dataset entitlements
are still required before tenant-private data is introduced. The cache key
includes the effective authorization scope for isolation and invalidation, but
the key is never the authorization mechanism.

## Target architecture

```text
request
  -> authenticated principal
  -> server-side authorization decision (deny by default)
  -> authorized dataset query / row predicate
  -> content fingerprint + policy-scope version
  -> canonical CacheIdentity
  -> cache backend (local first; Redis only when enabled)
  -> typed result / recomputation
```

### Cache identity and authorization

`CacheIdentity` must contain:

- `dataset_fingerprint`: canonical content/schema fingerprint;
- `tenant_id` or explicit `public` scope;
- `authorization_scope_version`: policy/data-entitlement version;
- normalized command/specification;
- model/provider and relevant filters;
- cache schema/version namespace.

The effective tenant and authorization scope must come from trusted server
context, never from a client-supplied cache key. A cache hit is legal only
after the current request is authorized for the same scope. Unknown scope,
missing principal, or failed policy evaluation produces a typed denial or a
cache miss followed by normal authorization—not a public fallback.

## Distributed-cache design (future gated slice)

### Deployment topology

**Tier 0 — current/local:** SQLite AI cache on the application host. Use WAL,
bounded transactions, busy timeout, and scheduled checkpoint/size maintenance.
Do not place the WAL database on a network filesystem.

**Tier 1 — shared deployment:** one managed Redis service per environment
(dev/stage/prod), private network access, TLS, authentication, restricted
security group, explicit memory limit, monitoring, and backups/persistence
appropriate to the fact that this is a disposable cache. Application workers
must use connection pooling and short timeouts.

**Not approved:** an ad-hoc Redis container shared across environments, a
network-mounted SQLite cache, or a multi-primary lock design introduced only
to improve cache hit rate.

### Key namespace and serialization

Use a namespace such as:

`profsur:{environment}:{cache_schema}:{capability}:{identity_digest}`

Values are versioned envelopes containing result payload, metadata, created-at,
expiry, producer version, and authorization-scope version. Serialize only
validated JSON-compatible result contracts; never pickle untrusted cache data.
Set a maximum serialized value size and reject oversized entries.

### Locking and stampede control

The lock is only a single-flight optimization for one cache identity. It must
not be the authorization gate or the source of truth.

- Use a per-key lease with a unique random owner token and bounded TTL.
- Release only if the stored token still belongs to the caller.
- Bound acquisition attempts and lock wait time; on failure, recompute or
  return a typed backend-degraded result.
- Add jittered retry to reduce synchronized contention.
- For operations that mutate shared state, require fencing tokens validated by
  the resource owner. A cache fill should instead write an immutable value with
  compare/version semantics.
- Never serve a value merely because the caller acquired a lock; re-check
  authorization and identity before write.

Redis documents the safety/liveness trade-offs of leases, failover, expiry,
clock assumptions, and fencing; those constraints must be represented in the
implementation and test plan, not hidden behind a lock library.

### Eviction and freshness

- Default policy: evictable cache entries only; the durable database remains
  authoritative.
- Separate namespaces/quotas for public, tenant-scoped, and expensive model
  results where operationally justified.
- Apply TTL by result class; add bounded stale-if-error only for explicitly
  safe, non-sensitive results and mark stale metadata in the response.
- Track hit, miss, expired, evicted, oversized, backend-error, lock-wait, and
  stale-served counters, plus p50/p95/p99 latency and memory usage.
- Do not use `noeviction` as a substitute for capacity planning; write errors
  must have a defined user-visible fallback.

### Migration, outage fallback, and rollback

Migration is a state machine, not a flag flip:

1. **OFF:** current SQLite path only; collect baseline metrics.
2. **SHADOW:** compute the new identity and read shared cache only for metrics;
   no shared value affects responses.
3. **DUAL-WRITE:** write both backends after authorization; reads remain local.
4. **CANARY-READ:** selected capability/tenant cohorts read shared values;
   compare envelopes and provenance.
5. **PRIMARY:** shared cache is primary, local cache is bounded fallback.
6. **RETIRE:** only after rollback window and evidence review; retain purge
   tooling and old-reader compatibility for the agreed window.

Every stage is controlled by configuration with a kill switch. On timeout,
connection failure, schema mismatch, deserialization failure, or authorization
scope mismatch, discard the shared entry and use the prior safe path. Never
silently widen scope. Rollback means setting the read mode to local/off and,
if necessary, stopping writes to the shared backend; it does not require data
destruction.

### Distributed-cache go/no-go gates

Do not implement the shared backend until all are demonstrated:

- two or more application processes share a cache hit on one host;
- separate tenants and scopes cannot observe each other’s values;
- concurrent fills produce one accepted value and bounded duplicate work;
- lock expiry, process crash, Redis restart, timeout, and network partition
  recover without incorrect results;
- eviction, TTL, oversized values, and stale-if-error behavior are evidenced;
- dual-read/dual-write and kill-switch rollback are tested;
- benchmark shows a real p95 improvement over SQLite/recomputation;
- GitHub-ready evidence and an operator runbook exist.

## AST parser design (future gated slice)

### Grammar coverage contract

The initial grammar inventory must be generated from the command registry and
existing fixtures. At minimum it covers current supported families:

- descriptive and tabular commands;
- panel and regression commands;
- `ivregress`, `gmm`, `hdfe`, `didregress`, and ML/predict routing;
- post-estimation commands such as `test`, `predict`, and `margins`;
- scenario commands and documented options.

Lexical coverage must include whitespace, case normalization, comments,
quoted strings, `///` continuation, identifiers, numeric literals, factor
variables, lag operators, `if`/`in`, comma-separated options, and nested
parentheses. Unsupported syntax must return a typed unsupported/syntax error,
not a partial command.

### AST and compatibility boundary

Use immutable nodes for `Command`, `VarList`, `VarRef`, `FactorTerm`, `LagTerm`,
`IfExpression`, `InRange`, `Option`, `QuotedValue`, and estimator-specific
parenthesized blocks. Preserve source spans for diagnostics, but pass a
normalized legacy dictionary through the current execution boundary initially.

Test layers:

1. golden parse fixtures for every supported command and option;
2. differential tests: legacy parser versus AST-to-legacy normalization;
3. typed-error tests for malformed, unsupported, oversized, and deeply nested
   inputs;
4. property/fuzz tests for tokenizer/parser termination and round-trip
   normalization;
5. security corpus for injection-like strings and comment/quote confusion;
6. shadow-mode production telemetry comparing parse outcomes without changing
   execution.

The parser is promoted per command only when all fixtures pass, normalized
output is stable, performance is bounded, and the old path remains available
for rollback.

## Legacy-caller integration (approved next slice)

The current callers are `models/board_export.py` and
`models/llm_adapters.py`, backed by `db.ai_cache_get/set`; estimator pages call
the narrative adapter. Integration work is limited to these boundaries:

1. Introduce a small internal cache-context/identity adapter around the existing
   helper; do not alter response text or current TTL defaults.
2. Derive dataset fingerprint and trusted authorization scope at the caller or
   immediately before the cache operation; deny anonymous callers, unknown
   roles, and missing dataset scope. For the shared MVP dataset, the authorized
   scope is reusable across users; role remains part of role-sensitive output
   identity.
3. Preserve legacy reads only for explicitly public, versioned entries; never
   guess a tenant for an old unscoped entry.
4. Add per-caller tests proving changes in fingerprint, tenant/scope, command,
   model, and filters produce distinct keys.
5. Add an authorization-before-cache test and a cache-backend-error fallback
   test.
6. Record baseline and post-integration hit/miss latency; no Redis dependency
   is introduced in this slice.

**Acceptance:** all existing cache tests pass; caller response/TTL semantics
remain unchanged; unauthorized requests cannot read or populate entries; the
focused integration suite is GitHub-ready; and the restart handoff records the
exact test command and result.

## Source notes

- Redis distributed locks: <https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/>
- Redis eviction policies and memory limits: <https://redis.io/docs/latest/develop/reference/eviction/>
- SQLite WAL concurrency and network-filesystem limitation: <https://sqlite.org/wal.html>
- OWASP authorization guidance (deny by default, validate every request, least privilege, testing): <https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html>
- Lark grammar, terminals, precedence, and ambiguity: <https://lark-parser.readthedocs.io/en/stable/grammar.html>

## Current disposition

Wave 6 remains active planning. The approved implementation next step is
legacy-caller integration plus explicit authorization context. Distributed
storage and AST parsing remain gated design slices. No capability status,
deployment state, branch, or release baseline is promoted by this document.
