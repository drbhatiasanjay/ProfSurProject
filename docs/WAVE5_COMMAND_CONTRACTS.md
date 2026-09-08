# Wave 5 Command Contracts

**Date:** 2026-09-08
**Applies to:** reconciliation successor branches after reviewed commit `88ab5c2`

## Release-Blocking Invariant

A user-specified variable, grouping variable, clustering variable, estimator
option, absorb variable, or intervention is never silently dropped, replaced, or
defaulted. The engine executes the requested semantics or returns a typed error
before estimator dispatch.

- Unknown requested variable: `VARIABLE_NOT_FOUND`, `r(111)`.
- Malformed syntax: `SYNTAX_ERROR`, `r(198)`.
- Unsupported option or estimator: `UNSUPPORTED_OPTION`, `r(198)`.
- Errors contain `metadata.stata_rc`, `metadata.invalid_argument`, and
  `metadata.argument_role`.
- Error results contain no coefficient table, result data, chart, or plausible
  statistical output.

## Canonical Syntax and Parser Output

### OLS Regression

```stata
regress leverage profitability tangibility
regress leverage profitability, vce(robust)
regress leverage profitability, vce(cluster company_code)
```

Parser/validation output includes resolved `depvar`, ordered `indepvars`,
`covariance_type`, `cluster_variable`, and `cluster_count`.

### Fixed-Effects Panel Regression

```stata
xtreg leverage profitability tangibility, fe
xtreg leverage profitability, fe vce(robust)
xtreg leverage profitability, fe vce(cluster company_code)
```

Clustered covariance uses exactly the requested validated grouping variable.
Arbitrary invalid cluster variables fail with `r(111)`.

### Grouped Summary

```stata
tabstat leverage profitability, by(life_stage)
```

An omitted `by()` retains the documented `life_stage` default. A supplied invalid
`by()` variable is never replaced by that default.

### Scenario Intervention Preview

Canonical syntax:

```stata
scenario leverage tax=-0.05
```

Accepted alternate syntax:

```stata
scenario leverage, interventions(tax=-0.05)
```

Both forms produce:

```python
options["interventions"] == {"tax": -0.05}
```

Scenario output remains `partial`, with methodology status `CANDIDATE` and result
type `INTERVENTION_PREVIEW`. It is not a validated counterfactual forecast.

### High-Dimensional Fixed Effects

```stata
hdfe leverage profitability, absorb(company_code year)
```

Parser output requires:

```python
options["absorb"] == ["company_code", "year"]
```

Every absorb variable is validated before pyfixest execution. HDFE remains
`IMPLEMENTED_UNVERIFIED` and returns `partial` when execution succeeds.

### Instrumental Variables

```stata
ivregress 2sls leverage profitability (tangibility = log_size)
```

Execution availability is distinct from methodological validation. `ivregress`
is `IMPLEMENTED_UNVERIFIED`; instrument relevance, exogeneity, and exclusion
restrictions require independent review.

## Covariance Semantics

| Request | Result metadata | Implementation |
|---|---|---|
| no `vce()` | `nonrobust` | conventional covariance |
| `vce(robust)` | `robust` | HC1 for OLS; robust panel covariance for `xtreg` |
| `vce(cluster var)` | `cluster` + exact variable/count | genuine grouped cluster covariance |

Cluster requests are never mapped to HC1 and are never silently replaced with
`company_code`.

## Capability and Methodology Status

| Capability | Implemented | Executable | Numerically checked | Methodologically validated |
|---|---:|---:|---:|---:|
| WS1 `test`, `predict`, `winsor2` | Yes | Yes | Yes | Not a causal-method claim |
| WS1 `ivregress` | Yes | Yes | Synthetic checks | No |
| Experimental IV-GMM proxy | Yes | Yes | Limited | No |
| HDFE | Yes | Dependency-gated | Synthetic checks | No |
| ML Ridge | Yes | Yes | Group-holdout checks | No |
| Scenario preview | Yes | Yes (`partial`) | Contract checks | No |
| DiD | No | No (`unsupported`) | No | No |

The authoritative status must remain consistent across command registry, router,
result metadata, UI copy, reports, and `CURRENT_STATUS.md`.
