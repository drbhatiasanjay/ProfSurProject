"""Canonical parser-output validation for Stata-compatible commands."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Callable

import pandas as pd


Resolver = Callable[..., str | None]


def validation_error(
    code: str,
    stata_rc: int,
    message: str,
    *,
    invalid_argument: str = "",
    argument_role: str = "",
) -> dict:
    metadata = {
        "stata_rc": stata_rc,
        "invalid_argument": invalid_argument,
        "argument_role": argument_role,
    }
    return {
        "status": "error",
        "error_code": code,
        "message": message,
        "ascii_output": f"{message}\nr({stata_rc});",
        "metadata": metadata,
    }


def _resolve(
    variable: str, df: pd.DataFrame, resolver: Resolver, *, role: str = "variable"
) -> str | None:
    # Stata grouping/cluster identifiers are semantic arguments.  They must
    # name an actual column; analytical aliases such as stage/firm/id are not
    # valid substitutes for an explicitly requested grouping variable.
    if role in {"by", "cluster"}:
        raw = str(variable).strip()
        for column in df.columns:
            if raw == column or raw.lower() == str(column).lower():
                return str(column)
        return None
    try:
        return resolver(variable, df.columns, df=df)
    except TypeError:
        return resolver(variable, df.columns)


def _variable_references(term: str) -> list[str]:
    references = []
    for component in re.split(r"##|#", str(term)):
        cleaned = component.strip()
        cleaned = re.sub(r"^(?:[cifdLFD]\d*\.|ib\d+\.)", "", cleaned)
        if re.fullmatch(r"[A-Za-z_]\w*", cleaned):
            references.append(cleaned)
    return references


def _normalize_terms(
    terms: list,
    df: pd.DataFrame,
    resolver: Resolver,
    role: str,
) -> tuple[list, dict | None]:
    normalized = []
    for term in terms:
        raw_term = str(term)
        references = _variable_references(raw_term)
        if not references:
            return [], validation_error(
                "SYNTAX_ERROR", 198, f"invalid {role} syntax: {raw_term}",
                invalid_argument=raw_term, argument_role=role,
            )
        for reference in references:
            if _resolve(reference, df, resolver) is None:
                return [], validation_error(
                    "VARIABLE_NOT_FOUND", 111,
                    f"variable {reference} not found ({role})",
                    invalid_argument=reference, argument_role=role,
                )
        if len(references) == 1 and references[0] == raw_term:
            normalized.append(_resolve(raw_term, df, resolver))
        else:
            normalized.append(raw_term)
    return normalized, None


def _covariance_contract(options: dict) -> tuple[str, str | None, dict | None]:
    cluster_value = options.get("cluster")
    vce_value = options.get("vce")
    robust_flag = bool(options.get("robust"))

    if cluster_value and vce_value:
        return "", None, validation_error(
            "UNSUPPORTED_OPTION", 198, "specify either cluster() or vce(), not both",
            argument_role="covariance",
        )
    if cluster_value:
        return "cluster", str(cluster_value).strip(), None
    if vce_value is not None:
        if not isinstance(vce_value, str):
            return "", None, validation_error(
                "UNSUPPORTED_OPTION", 198, "vce() requires robust or cluster variable",
                argument_role="covariance",
            )
        value = vce_value.strip()
        if value.lower() == "robust":
            return "robust", None, None
        match = re.fullmatch(r"cluster\s+([A-Za-z_]\w*)", value, flags=re.IGNORECASE)
        if match:
            return "cluster", match.group(1), None
        return "", None, validation_error(
            "UNSUPPORTED_OPTION", 198, f"unsupported vce() specification: {value}",
            invalid_argument=value, argument_role="covariance",
        )
    return ("robust" if robust_flag else "nonrobust"), None, None


def validate_stata_command(
    parsed: dict,
    df: pd.DataFrame,
    resolver: Resolver,
) -> tuple[dict, dict | None]:
    normalized = deepcopy(parsed)
    normalized["options"] = deepcopy(parsed.get("options", {}))
    command = normalized.get("cmd", "")

    if normalized.get("parse_error"):
        return normalized, validation_error(
            "SYNTAX_ERROR", 198, normalized["parse_error"], argument_role="syntax"
        )

    regression_commands = {"regress", "reg", "xtreg", "gmm", "hdfe", "didregress", "predict_ml"}
    if command in regression_commands:
        raw_depvar = str(normalized.get("depvar", "")).strip()
        if not raw_depvar:
            return normalized, validation_error(
                "SYNTAX_ERROR", 198, f"{command} requires a dependent variable",
                argument_role="dependent_variable",
            )
        depvar = _resolve(raw_depvar, df, resolver)
        if depvar is None:
            return normalized, validation_error(
                "VARIABLE_NOT_FOUND", 111,
                f"variable {raw_depvar} not found (dependent variable)",
                invalid_argument=raw_depvar, argument_role="dependent_variable",
            )
        normalized["depvar"] = depvar

        raw_indepvars = list(normalized.get("indepvars", []))
        if command in {"regress", "reg", "xtreg", "hdfe", "gmm", "predict_ml"} and not raw_indepvars:
            return normalized, validation_error(
                "SYNTAX_ERROR", 198, f"{command} requires at least one independent variable",
                argument_role="independent_variable",
            )
        indepvars, error = _normalize_terms(raw_indepvars, df, resolver, "independent variable")
        if error:
            return normalized, error
        normalized["indepvars"] = indepvars

    if command == "ivregress":
        estimator = str(normalized.get("estimator", "2sls")).lower()
        if estimator != "2sls":
            return normalized, validation_error(
                "UNSUPPORTED_OPTION", 198,
                f"ivregress estimator {estimator} is unsupported; use 2sls",
                invalid_argument=estimator, argument_role="estimator",
            )
        raw_depvar = str(normalized.get("depvar", "")).strip()
        if not raw_depvar:
            return normalized, validation_error(
                "SYNTAX_ERROR", 198, "ivregress requires a dependent variable",
                argument_role="dependent_variable",
            )
        depvar = _resolve(raw_depvar, df, resolver)
        if depvar is None:
            return normalized, validation_error(
                "VARIABLE_NOT_FOUND", 111,
                f"variable {raw_depvar} not found (dependent variable)",
                invalid_argument=raw_depvar, argument_role="dependent_variable",
            )
        normalized["depvar"] = depvar
        for key, role in (
            ("exog_vars", "exogenous variable"),
            ("endog_vars", "endogenous variable"),
            ("instruments", "instrument"),
        ):
            terms = list(normalized.get(key, []))
            if key in {"endog_vars", "instruments"} and not terms:
                return normalized, validation_error(
                    "SYNTAX_ERROR", 198,
                    "ivregress 2sls requires endogenous variables and instruments",
                    argument_role=role,
                )
            resolved, error = _normalize_terms(terms, df, resolver, role)
            if error:
                return normalized, error
            normalized[key] = resolved
        normalized["indepvars"] = normalized["exog_vars"] + normalized["endog_vars"]

    if command == "tabstat":
        raw_vars = list(normalized.get("indepvars", []))
        if not raw_vars:
            return normalized, validation_error(
                "SYNTAX_ERROR", 198, "tabstat requires at least one variable",
                argument_role="variable",
            )
        variables, error = _normalize_terms(raw_vars, df, resolver, "variable")
        if error:
            return normalized, error
        normalized["indepvars"] = variables
        if "by" in normalized["options"]:
            raw_by = str(normalized["options"]["by"])
            by_variable = _resolve(raw_by, df, resolver, role="by")
            if by_variable is None:
                return normalized, validation_error(
                    "VARIABLE_NOT_FOUND", 111, f"variable {raw_by} not found (by)",
                    invalid_argument=raw_by, argument_role="by",
                )
            normalized["options"]["by"] = by_variable

    if command in {"box", "hbox"} and normalized["options"].get("over"):
        raw_group = str(normalized["options"]["over"]).strip()
        group = _resolve(raw_group, df, resolver, role="by")
        if group is None:
            return normalized, validation_error(
                "VARIABLE_NOT_FOUND", 111, f"variable {raw_group} not found (over)",
                invalid_argument=raw_group, argument_role="over",
            )
        normalized["options"]["over"] = group

    if command in {"margins", "marginsplot"} and normalized.get("indepvars"):
        raw_group = str(normalized["indepvars"][0]).strip("(),")
        group = _resolve(raw_group, df, resolver, role="by")
        if group is None:
            return normalized, validation_error(
                "VARIABLE_NOT_FOUND", 111, f"variable {raw_group} not found (group)",
                invalid_argument=raw_group, argument_role="group",
            )
        normalized["indepvars"][0] = group

    if command == "test":
        formula = str(normalized.get("formula", ""))
        references = [
            token for token in re.findall(r"[A-Za-z_]\w*", formula)
            if token.lower() not in {"const", "_cons"}
        ]
        for reference in references:
            if _resolve(reference, df, resolver) is None:
                return normalized, validation_error(
                    "VARIABLE_NOT_FOUND", 111,
                    f"variable {reference} not found (test)",
                    invalid_argument=reference, argument_role="test_variable",
                )

    list_commands = {
        "summarize", "sum", "pwcorr", "correlate", "corr", "tabulate", "tab",
        "mean", "proportion", "describe", "codebook", "winsor2", "lgraph",
    }
    if command in list_commands and normalized.get("indepvars"):
        variables, error = _normalize_terms(
            list(normalized["indepvars"]), df, resolver, "variable"
        )
        if error:
            return normalized, error
        normalized["indepvars"] = variables

    if command in {"scatter", "histogram", "hist"}:
        raw_depvar = str(normalized.get("depvar", "")).strip()
        if raw_depvar:
            depvar = _resolve(raw_depvar, df, resolver)
            if depvar is None:
                return normalized, validation_error(
                    "VARIABLE_NOT_FOUND", 111, f"variable {raw_depvar} not found",
                    invalid_argument=raw_depvar, argument_role="variable",
                )
            normalized["depvar"] = depvar
        if normalized.get("indepvars"):
            variables, error = _normalize_terms(
                list(normalized["indepvars"]), df, resolver, "variable"
            )
            if error:
                return normalized, error
            normalized["indepvars"] = variables

    if command in {"regress", "reg", "xtreg"}:
        covariance_type, cluster_raw, error = _covariance_contract(normalized["options"])
        if error:
            return normalized, error
        cluster_variable = None
        cluster_count = None
        if cluster_raw:
            cluster_variable = _resolve(cluster_raw, df, resolver, role="cluster")
            if cluster_variable is None:
                return normalized, validation_error(
                    "VARIABLE_NOT_FOUND", 111,
                    f"variable {cluster_raw} not found (cluster)",
                    invalid_argument=cluster_raw, argument_role="cluster",
                )
            cluster_count = int(df[cluster_variable].dropna().nunique())
        normalized["covariance_type"] = covariance_type
        normalized["cluster_variable"] = cluster_variable
        normalized["cluster_count"] = cluster_count

    if command == "scenario":
        raw_depvar = str(normalized.get("depvar", "")).strip()
        if not raw_depvar:
            return normalized, validation_error(
                "SYNTAX_ERROR", 198, "scenario requires an outcome variable",
                argument_role="dependent_variable",
            )
        depvar = _resolve(raw_depvar, df, resolver)
        if depvar is None:
            return normalized, validation_error(
                "VARIABLE_NOT_FOUND", 111,
                f"variable {raw_depvar} not found (scenario outcome)",
                invalid_argument=raw_depvar, argument_role="dependent_variable",
            )
        normalized["depvar"] = depvar
        interventions = normalized["options"].get("interventions")
        if not isinstance(interventions, dict) or not interventions:
            return normalized, validation_error(
                "SYNTAX_ERROR", 198, "scenario requires variable=value interventions",
                argument_role="intervention",
            )
        resolved_interventions = {}
        for raw_variable, shift in interventions.items():
            variable = _resolve(raw_variable, df, resolver)
            if variable is None:
                return normalized, validation_error(
                    "VARIABLE_NOT_FOUND", 111,
                    f"variable {raw_variable} not found (intervention)",
                    invalid_argument=raw_variable, argument_role="intervention",
                )
            resolved_interventions[variable] = float(shift)
        normalized["options"]["interventions"] = resolved_interventions

    if command == "hdfe":
        absorb_variables = normalized["options"].get("absorb", ["company_code", "year"])
        if not isinstance(absorb_variables, list):
            return normalized, validation_error(
                "SYNTAX_ERROR", 198, "absorb() must contain a variable list",
                argument_role="absorb",
            )
        resolved_absorb = []
        for raw_variable in absorb_variables:
            variable = _resolve(raw_variable, df, resolver)
            if variable is None:
                return normalized, validation_error(
                    "VARIABLE_NOT_FOUND", 111,
                    f"variable {raw_variable} not found (absorb)",
                    invalid_argument=raw_variable, argument_role="absorb",
                )
            resolved_absorb.append(variable)
        normalized["options"]["absorb"] = resolved_absorb

    return normalized, None
