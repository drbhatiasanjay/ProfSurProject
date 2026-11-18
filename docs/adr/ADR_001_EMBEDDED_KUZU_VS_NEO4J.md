# Architecture Decision Record (ADR)
## ADR-001: Embedded Kùzu Property Graph vs. External Neo4j Server

**Status:** ACCEPTED  
**Date:** 2026-11-18  
**Context:** Milestone 11 — Pre-IPO Financial Knowledge Graph Platform  

### Context and Problem Statement
The platform requires a high-performance Property Graph Database engine to support multi-hop Cypher traversals (e.g. tracing distributor cheque bounce litigation across territories to EBITDA margins) and shortest-path algorithms across 100,000+ nodes and edges extracted from 500-page prospectuses. We evaluated two primary architectural options:
1. **Option A (External Neo4j Server / Aura DB):** Traditional enterprise property graph server.
2. **Option B (Embedded Kùzu Engine):** Modern in-process C++ graph database engine with native Cypher support.

### Decision Outcome
**Chosen Option:** **Option B (Embedded Kùzu Engine)**

### Positive Consequences & Justification
1. **Zero External Daemon Overhead:** Like SQLite and DuckDB, Kùzu runs embedded within the Python/FastAPI process. It requires no background JVM, Docker container, or cloud database management.
2. **Instant Local & Cloud Run Deployment:** The application can run locally (`http://localhost:8000/`) and deploy to Google Cloud Run seamlessly without managing external VPC peering, database connection pooling, or separate server costs.
3. **Sub-50ms Native Cypher Traversal:** Written in modern C++ with columnar storage and vectorized execution, Kùzu outperforms network-bound graph servers for analytical traversals.
4. **Zero-Copy Apache Arrow Integration:** Native interoperability with DuckDB and Polars for downstream quantitative financial calculations (SARD multiple discounts, DCF projections).

### Trade-offs & Mitigations
- *Trade-off:* Kùzu lacks Neo4j's enterprise Bloom GUI out of the box.
- *Mitigation:* We build our own modern, aesthetic-rich Bloom-style visual canvas in React 19 using `@xyflow/react`, providing a tailored, domain-specific UI that exceeds generic database viewers.
- *Extensibility:* If enterprise clients demand remote Neo4j hosting, the architecture includes an abstract `GraphStore` interface where a Neo4j driver can be plugged in without changing domain logic.
