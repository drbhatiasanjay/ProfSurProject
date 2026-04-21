"""
Per-company CMIE batch pipeline — hardened wapicall loop.

Implements §F.3.1 / §F.3.3 / §F.3.4 / §F.3.5 from
docs/plans/2026-04-21-cmie-refactor-execution-strategy.md:

  F.3.1  Shared TokenBucket (rate_per_sec=2, burst=3) + max_retries=1
  F.3.3  Abort-on-auth — first CmieAuthError skips every remaining company
  F.3.4  Honour Retry-After — pause between companies instead of retrying current
  F.3.5  Circuit breaker — N consecutive SERVER errors skip the remainder

F.3.2 (don't retry ZIP_BAD) is already enforced in cmie/client.py (commit afb7a4a).
F.3.6 (retry_after_s typed attribute on CmieRateLimitError) is in cmie/errors.py
   (commit b25c052); this pipeline reads `e.retry_after_s` directly.

Does NOT write to capital_structure.db — call `import_results_to_db()` separately
if you want the successful zips merged into api_financials.

Public surface:
  CompanyResult        — dataclass: per-company outcome
  BatchSummary         — dataclass: aggregate outcome
  run_per_company_batch(api_key, companies, *, out_dir, …) → (results, summary)
  import_results_to_db(results, *, import_id=…, …) → version_id | None
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

from cmie.client import CmieClient
from cmie.errors import (
    CmieAuthError,
    CmieEntitlementError,
    CmieError,
    CmieNetworkError,
    CmieRateLimitError,
    CmieZipError,
)
from cmie.rate_limit import TokenBucket

# Signature: on_progress(index, total, message) — for Streamlit / CLI progress bars
ProgressCallback = Callable[[int, int, str], None]


@dataclass
class CompanyResult:
    """Per-company outcome. `outcome` is fine-grained; `status` is coarse."""

    company_code: int
    company_name: Optional[str]
    status: str  # "success" | "failed" | "skipped"
    outcome: str  # "ok" | "auth" | "entitlement" | "rate_limit" | "zip_bad"
    # | "server" | "network" | "other" | "aborted_auth" | "circuit_open"
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    error_detail: Optional[str] = None
    zip_path: Optional[str] = None
    bytes_downloaded: int = 0
    http_calls: int = 0  # conservative upper bound per §F.4 KPI
    elapsed_s: float = 0.0


@dataclass
class BatchSummary:
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    aborted_auth: bool = False
    circuit_opened: bool = False
    total_http_calls: int = 0
    total_bytes_downloaded: int = 0
    elapsed_s: float = 0.0


def _result_for_exception(
    code: int,
    name: Optional[str],
    exc: CmieError,
    max_retries: int,
    started: float,
    outcome: str,
    http_calls: int,
) -> CompanyResult:
    return CompanyResult(
        company_code=int(code),
        company_name=name,
        status="failed",
        outcome=outcome,
        error_code=exc.code,
        error_message=exc.message,
        error_detail=exc.detail,
        http_calls=http_calls,
        elapsed_s=time.monotonic() - started,
    )


def run_per_company_batch(
    api_key: str,
    companies: Iterable[tuple[int, Optional[str]]],
    *,
    out_dir: str | Path,
    max_retries: int = 1,
    rate_per_sec: float = 2.0,
    burst: int = 3,
    inter_call_delay_s: float = 0.5,
    circuit_breaker_threshold: int = 5,
    retry_after_default_s: float = 60.0,
    retry_after_cap_s: float = 300.0,
    timeout_s: float = 120.0,
    on_progress: Optional[ProgressCallback] = None,
    _client: Optional[CmieClient] = None,
) -> tuple[list[CompanyResult], BatchSummary]:
    """Fetch one company at a time via wapicall with §F hardening.

    Parameters
    ----------
    companies :
        Iterable of `(company_code, display_name_or_None)`. display_name is NOT
        sent to CMIE (see §E.1); it's retained for the result report only.
    out_dir :
        Directory to write `<company_code>.zip` files into. Created if missing.
    max_retries :
        Passed to `CmieClient(max_retries=…)`. Default 1 keeps per-company HTTP
        to ≤ 2, inside CMIE's 3-hit budget (§F.3.1).
    rate_per_sec / burst :
        TokenBucket params, shared across the whole batch. One limiter per
        `run_per_company_batch` call.
    inter_call_delay_s :
        Sleep between companies on happy path. Stacked with TokenBucket pacing.
    circuit_breaker_threshold :
        N consecutive SERVER outcomes → skip every remaining company with
        `outcome="circuit_open"`. Default 5.
    retry_after_default_s :
        Used when CMIE 429 response lacks a parsable `Retry-After` header.
    retry_after_cap_s :
        Upper bound on the pause; keeps UI responsive on absurd values.
    _client :
        Test-only injection point. Production code should omit this.
    """
    companies_list = list(companies)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if _client is None:
        limiter = TokenBucket(rate_per_sec=rate_per_sec, burst=burst)
        _client = CmieClient(
            api_key, timeout_s=timeout_s, limiter=limiter, max_retries=max_retries
        )

    results: list[CompanyResult] = []
    recent_server_errors = 0
    aborted_auth = False
    circuit_opened = False
    batch_started = time.monotonic()

    for i, (code, name) in enumerate(companies_list):
        if on_progress:
            on_progress(i, len(companies_list), f"Downloading {code}")

        zip_path = out_path / f"{int(code)}.zip"
        company_started = time.monotonic()

        try:
            _client.download_wapicall_zip([int(code)], dest_path=str(zip_path))
            results.append(
                CompanyResult(
                    company_code=int(code),
                    company_name=name,
                    status="success",
                    outcome="ok",
                    zip_path=str(zip_path),
                    bytes_downloaded=(
                        zip_path.stat().st_size if zip_path.exists() else 0
                    ),
                    http_calls=1,  # success = 1 HTTP; no retry needed
                    elapsed_s=time.monotonic() - company_started,
                )
            )
            recent_server_errors = 0

        except CmieAuthError as exc:
            # F.3.3: abort-on-auth
            results.append(
                _result_for_exception(code, name, exc, max_retries, company_started,
                                      outcome="auth", http_calls=1)
            )
            aborted_auth = True
            for rem_code, rem_name in companies_list[i + 1:]:
                results.append(
                    CompanyResult(
                        company_code=int(rem_code),
                        company_name=rem_name,
                        status="skipped",
                        outcome="aborted_auth",
                        error_code="ABORTED_AUTH",
                        error_message="Batch aborted after authentication failure.",
                    )
                )
            break

        except CmieEntitlementError as exc:
            # Entitlement is per-company — other companies may be entitled
            results.append(
                _result_for_exception(code, name, exc, max_retries, company_started,
                                      outcome="entitlement", http_calls=1)
            )
            recent_server_errors = 0

        except CmieRateLimitError as exc:
            # F.3.4: this company already paid its hits; pause before next
            results.append(
                _result_for_exception(code, name, exc, max_retries, company_started,
                                      outcome="rate_limit", http_calls=1)
            )
            wait_s = exc.retry_after_s if exc.retry_after_s is not None else retry_after_default_s
            wait_s = min(max(wait_s, 0.0), retry_after_cap_s)
            if on_progress:
                on_progress(
                    i, len(companies_list),
                    f"CMIE rate-limited, pausing {wait_s:.0f}s before next company",
                )
            if wait_s > 0:
                time.sleep(wait_s)
            recent_server_errors = 0

        except CmieZipError as exc:
            # F.3.2 in client already short-circuits retry; we just record and move on
            results.append(
                _result_for_exception(code, name, exc, max_retries, company_started,
                                      outcome="zip_bad", http_calls=1)
            )
            recent_server_errors = 0

        except CmieNetworkError as exc:
            # Retried up to max_retries inside the client, so conservative upper bound
            is_server = exc.code == "SERVER"
            outcome = "server" if is_server else "network"
            results.append(
                _result_for_exception(code, name, exc, max_retries, company_started,
                                      outcome=outcome, http_calls=1 + max_retries)
            )
            if is_server:
                recent_server_errors += 1
            else:
                recent_server_errors = 0

        except CmieError as exc:
            # Catch-all: SchemaError / ValidationError / StorageError / …
            results.append(
                _result_for_exception(code, name, exc, max_retries, company_started,
                                      outcome="other", http_calls=1)
            )
            recent_server_errors = 0

        # F.3.5: circuit breaker
        if recent_server_errors >= circuit_breaker_threshold:
            circuit_opened = True
            for rem_code, rem_name in companies_list[i + 1:]:
                results.append(
                    CompanyResult(
                        company_code=int(rem_code),
                        company_name=rem_name,
                        status="skipped",
                        outcome="circuit_open",
                        error_code="CIRCUIT_OPEN",
                        error_message=(
                            f"Skipped after {circuit_breaker_threshold} consecutive "
                            "server errors — CMIE may be down."
                        ),
                    )
                )
            break

        # Inter-call delay (only if we're continuing to next company)
        if (
            i < len(companies_list) - 1
            and inter_call_delay_s > 0
            and not aborted_auth
            and not circuit_opened
        ):
            time.sleep(inter_call_delay_s)

    summary = BatchSummary(
        total=len(results),
        succeeded=sum(1 for r in results if r.status == "success"),
        failed=sum(1 for r in results if r.status == "failed"),
        skipped=sum(1 for r in results if r.status == "skipped"),
        aborted_auth=aborted_auth,
        circuit_opened=circuit_opened,
        total_http_calls=sum(r.http_calls for r in results),
        total_bytes_downloaded=sum(r.bytes_downloaded for r in results),
        elapsed_s=time.monotonic() - batch_started,
    )
    return results, summary


def import_results_to_db(
    results: list[CompanyResult],
    *,
    import_id: Optional[str] = None,
    min_validation_years: int = 1,
    note: str = "batch_pipeline import",
    indicators: str = "",
    on_step: Optional[Callable[[int, str], None]] = None,
) -> Optional[str]:
    """Merge successful zips into `api_financials` via the existing
    `cmie.pipeline.merge_zip_paths_to_version`. Returns the new `version_id`,
    or `None` if nothing succeeded.
    """
    # Local import — keeps batch_pipeline.py independent of db.py for tests
    from cmie.pipeline import merge_zip_paths_to_version

    successes = [r for r in results if r.status == "success" and r.zip_path]
    if not successes:
        return None

    zip_paths = [r.zip_path for r in successes if r.zip_path is not None]
    return merge_zip_paths_to_version(
        zip_paths,
        import_id=import_id,
        on_step=on_step,
        min_validation_years=min_validation_years,
        indicators=indicators or f"batch_pipeline({len(zip_paths)} companies)",
        note=note,
    )
