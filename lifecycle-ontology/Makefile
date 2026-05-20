# lifecycle-ontology — common development commands
# Run from lifecycle-ontology/ directory after `eval $(opam env)`

.PHONY: build test clean watch install-deps fmt check

build:
	dune build

test:
	dune runtest

clean:
	dune clean

watch:
	dune build --watch

# Install all opam dependencies
install-deps:
	opam install --deps-only -y .

# Format OCaml source files (requires ocamlformat)
fmt:
	dune build @fmt --auto-promote 2>/dev/null || true

# Type-check without linking (faster CI feedback)
check:
	dune build @check

# Run the CLI (after build)
run:
	./_build/default/src/cli/main.exe
