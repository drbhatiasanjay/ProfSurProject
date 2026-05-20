# lifecycle-ontology

OCaml semantic and analytics meta-layer for the LifeCycle Leverage platform.

## Setup (one-time)

```powershell
# 1. Download opam Windows binary (already done if opam.exe is in PATH)
# https://github.com/ocaml/opam/releases/latest

# 2. Initialize opam (installs internal Cygwin, ~5 min)
opam init --bare --disable-sandboxing -y

# 3. Create OCaml 5.2 switch (~10-20 min, compiles compiler)
opam switch create 5.2.0 ocaml-base-compiler -y

# 4. Install required packages (~10 min)
eval $(opam env)
opam install -y dune eio_main yojson ocamlgraph cmdliner dream alcotest

# 5. Build
cd lifecycle-ontology
dune build

# 6. Run tests
dune runtest
```

## Module structure

```
src/
  domain/          stage, period, metric, company, persona (ADTs + smart ctors)
  analytics_meta/  model, model_run, statistic, normative_band, scenario, explanation
  normative/       conformalized-QR bands + anomaly flags
  scenario/        scenario DSL + validation
  graph_export/    Macro/Meso/Micro JSON/DOT exporters (ocamlgraph)
  api/             Dream HTTP: /lifecycle_query /explain_stat /scenario_runner
  cli/             cmdliner entry point
test/              alcotest unit tests
```

## Build phases

| Phase | Deliverable | Gate |
|---|---|---|
| 1 | Scaffold — this directory | `dune build && dune runtest` green |
| 2 | Domain types + smart constructors | full alcotest coverage |
| 3 | Analytics meta + JSON serialization | yojson round-trip tests |
| 4 | Normative + Scenario logic | band/anomaly tests |
| 5 | Graph export | Macro/Meso/Micro JSON contract tests |
| 6 | CLI + HTTP (Dream/Eio) | integration tests |
