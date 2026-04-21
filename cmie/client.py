from __future__ import annotations

import hashlib
import json
import os
import random
import time
import zipfile
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

import requests

from cmie.errors import (
    CmieAuthError,
    CmieNetworkError,
    CmieRateLimitError,
    CmieZipError,
)
from cmie.rate_limit import TokenBucket


CMIE_QUERY_URL = "https://economyapi.cmie.com/query.php"
# Company consolidated download (ZIP + txt); public CMIE docs (verify HTTPS with your account).
CMIE_WAPICALL_URL = "https://economyapi.cmie.com/kommon/bin/sr.php?kall=wapicall"


@dataclass(frozen=True)
class DownloadProgress:
    received_bytes: int
    total_bytes: Optional[int]
    elapsed_s: float

    @property
    def pct(self) -> Optional[float]:
        if not self.total_bytes:
            return None
        if self.total_bytes <= 0:
            return None
        return min(100.0, 100.0 * (self.received_bytes / self.total_bytes))

    @property
    def bytes_per_s(self) -> float:
        return self.received_bytes / max(self.elapsed_s, 1e-6)

    @property
    def eta_s(self) -> Optional[float]:
        if not self.total_bytes:
            return None
        remaining = max(0, self.total_bytes - self.received_bytes)
        bps = self.bytes_per_s
        return remaining / bps if bps > 0 else None


def _hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:12]


def _zip_sanity_check(path: str, *, context: str) -> None:
    """
    CMIE sometimes returns HTML/JSON error bodies with HTTP 200.
    Detect non-zip responses early and show a useful snippet.
    """
    try:
        if zipfile.is_zipfile(path):
            return
    except Exception:
        # Fall through and raise ZIP_BAD with snippet.
        pass

    snippet = ""
    try:
        with open(path, "rb") as f:
            raw = f.read(4000)
        # best-effort decode
        for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                snippet = raw.decode(enc)
                break
            except Exception:
                continue
        if not snippet:
            snippet = raw.decode("latin-1", errors="replace")
        snippet = snippet.strip()
    except Exception as e:  # pragma: no cover
        snippet = f"(could not read response snippet: {e})"

    raise CmieZipError(
        code="ZIP_BAD",
        message=f"{context}: response was not a valid zip (CMIE may have returned an error body).",
        detail=snippet[:2000] if snippet else None,
    )


class CmieClient:
    """
    CMIE Economy API client.
    Best practices:
    - streaming download (large zip)
    - bounded retries with backoff + jitter
    - respect Retry-After if present
    - optional in-process rate limiter
    """

    def __init__(
        self,
        api_key: str,
        *,
        session: Optional[requests.Session] = None,
        limiter: Optional[TokenBucket] = None,
        timeout_s: float = 120.0,
        max_retries: int = 4,
    ):
        self.api_key = api_key
        self.api_key_hash = _hash_key(api_key)
        self._session = session or requests.Session()
        self._limiter = limiter
        self._timeout_s = float(timeout_s)
        self._max_retries = int(max_retries)

    def download_query_zip(
        self,
        payload: Dict,
        *,
        dest_path: str,
        on_progress: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> str:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        attempt = 0
        while True:
            attempt += 1
            if self._limiter is not None:
                ok = self._limiter.acquire(timeout_s=10.0)
                if not ok:
                    raise CmieRateLimitError(
                        code="RATE_LIMIT_LOCAL",
                        message="Local rate limiter blocked the request. Try again shortly.",
                    )

            started = time.monotonic()
            try:
                json_body = json.dumps(payload) if isinstance(payload, dict) else str(payload)
                with self._session.post(
                    CMIE_QUERY_URL,
                    data={"apikey": self.api_key, "json": json_body},
                    stream=True,
                    timeout=self._timeout_s,
                ) as resp:
                    if resp.status_code in (401, 403):
                        raise CmieAuthError(
                            code="AUTH",
                            message="Unauthorized. Check your CMIE API key and subscription.",
                            detail=f"HTTP {resp.status_code}",
                        )
                    if resp.status_code == 429:
                        retry_after = resp.headers.get("Retry-After")
                        raise CmieRateLimitError(
                            code="RATE_LIMIT_REMOTE",
                            message="CMIE rate limit reached. Please retry later.",
                            detail=f"Retry-After: {retry_after}" if retry_after else "HTTP 429",
                        )
                    if resp.status_code >= 500:
                        raise CmieNetworkError(
                            code="SERVER",
                            message="CMIE server error. Please retry later.",
                            detail=f"HTTP {resp.status_code}",
                        )
                    if resp.status_code != 200:
                        raise CmieNetworkError(
                            code="HTTP",
                            message="Unexpected response from CMIE API.",
                            detail=f"HTTP {resp.status_code}",
                        )

                    total = resp.headers.get("Content-Length")
                    total_bytes = int(total) if total and total.isdigit() else None
                    received = 0

                    with open(dest_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=1024 * 256):
                            if not chunk:
                                continue
                            f.write(chunk)
                            received += len(chunk)
                            if on_progress is not None:
                                on_progress(
                                    DownloadProgress(
                                        received_bytes=received,
                                        total_bytes=total_bytes,
                                        elapsed_s=time.monotonic() - started,
                                    )
                                )

                _zip_sanity_check(dest_path, context="query.php legacy zip")
                return dest_path

            except (CmieAuthError, CmieRateLimitError, CmieZipError) as e:
                # Do not retry auth / rate-limit / bad-zip automatically (user action or
                # remote policy; HTML-at-200 is almost always misconfig, not transient).
                raise e
            except requests.Timeout as e:
                err = CmieNetworkError(code="TIMEOUT", message="CMIE request timed out.", detail=str(e))
            except requests.RequestException as e:
                err = CmieNetworkError(code="NETWORK", message="Network error calling CMIE API.", detail=str(e))
            except Exception as e:  # pragma: no cover
                err = CmieNetworkError(code="UNKNOWN", message="Unexpected error calling CMIE API.", detail=str(e))

            if attempt > self._max_retries:
                raise err

            # Backoff with jitter (bounded)
            base = 1.0 * (2 ** (attempt - 1))
            sleep_s = min(20.0, base) * (0.7 + 0.6 * random.random())
            time.sleep(sleep_s)

        # defensive: should be unreachable
        # return dest_path

    def post_query_form(self, form_fields: Dict[str, Union[str, int, float]]) -> Any:
        """
        POST ``application/x-www-form-urlencoded`` to query.php (public CMIE examples use form fields).

        ``form_fields`` should include scheme-specific keys (e.g. scheme, indicnum, freq, nperiod).
        ``apikey`` is injected automatically.
        """
        data = {"apikey": self.api_key}
        for k, v in form_fields.items():
            if v is None:
                continue
            data[k] = v if isinstance(v, str) else str(v)

        attempt = 0
        while True:
            attempt += 1
            if self._limiter is not None:
                ok = self._limiter.acquire(timeout_s=10.0)
                if not ok:
                    raise CmieRateLimitError(
                        code="RATE_LIMIT_LOCAL",
                        message="Local rate limiter blocked the request. Try again shortly.",
                    )
            try:
                resp = self._session.post(CMIE_QUERY_URL, data=data, timeout=self._timeout_s)
                if resp.status_code in (401, 403):
                    raise CmieAuthError(
                        code="AUTH",
                        message="Unauthorized. Check your CMIE API key and subscription.",
                        detail=f"HTTP {resp.status_code}",
                    )
                if resp.status_code == 429:
                    raise CmieRateLimitError(
                        code="RATE_LIMIT_REMOTE",
                        message="CMIE rate limit reached.",
                        detail=resp.headers.get("Retry-After", "HTTP 429"),
                    )
                if resp.status_code >= 500:
                    raise CmieNetworkError(code="SERVER", message="CMIE server error.", detail=f"HTTP {resp.status_code}")
                if resp.status_code != 200:
                    raise CmieNetworkError(code="HTTP", message="Unexpected response from CMIE query.php.", detail=f"HTTP {resp.status_code}")
                return resp.json()
            except (CmieAuthError, CmieRateLimitError, CmieZipError):
                raise
            except requests.Timeout as e:
                err = CmieNetworkError(code="TIMEOUT", message="CMIE query.php timed out.", detail=str(e))
            except requests.RequestException as e:
                err = CmieNetworkError(code="NETWORK", message="Network error calling CMIE query.php.", detail=str(e))
            except ValueError as e:
                err = CmieNetworkError(code="JSON", message="CMIE query.php did not return valid JSON.", detail=str(e))
            except Exception as e:  # pragma: no cover
                err = CmieNetworkError(code="UNKNOWN", message="Unexpected error from CMIE query.php.", detail=str(e))

            if attempt > self._max_retries:
                raise err
            base = 1.0 * (2 ** (attempt - 1))
            time.sleep(min(20.0, base) * (0.7 + 0.6 * random.random()))

    def download_wapicall_zip(
        self,
        company_codes: List[int],
        *,
        dest_path: str,
        on_progress: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> str:
        """
        POST company download request; response body is a ZIP (per public CMIE documentation).

        Request JSON shape follows published examples: ``company_code`` array.
        """
        if not company_codes:
            raise ValueError("company_codes must be non-empty")
        os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
        body = {"apikey": self.api_key, "company_code": [str(c) for c in company_codes]}

        attempt = 0
        while True:
            attempt += 1
            if self._limiter is not None:
                ok = self._limiter.acquire(timeout_s=10.0)
                if not ok:
                    raise CmieRateLimitError(
                        code="RATE_LIMIT_LOCAL",
                        message="Local rate limiter blocked the request. Try again shortly.",
                    )
            started = time.monotonic()
            try:
                with self._session.post(
                    CMIE_WAPICALL_URL,
                    json=body,
                    stream=True,
                    timeout=self._timeout_s,
                ) as resp:
                    if resp.status_code in (401, 403):
                        raise CmieAuthError(
                            code="AUTH",
                            message="Unauthorized. Check your CMIE API key and subscription.",
                            detail=f"HTTP {resp.status_code}",
                        )
                    if resp.status_code == 429:
                        raise CmieRateLimitError(
                            code="RATE_LIMIT_REMOTE",
                            message="CMIE rate limit reached.",
                            detail=resp.headers.get("Retry-After", "HTTP 429"),
                        )
                    if resp.status_code >= 500:
                        raise CmieNetworkError(code="SERVER", message="CMIE server error.", detail=f"HTTP {resp.status_code}")
                    if resp.status_code != 200:
                        raise CmieNetworkError(code="HTTP", message="Unexpected response from wapicall.", detail=f"HTTP {resp.status_code}")

                    total = resp.headers.get("Content-Length")
                    total_bytes = int(total) if total and total.isdigit() else None
                    received = 0
                    with open(dest_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=1024 * 256):
                            if not chunk:
                                continue
                            f.write(chunk)
                            received += len(chunk)
                            if on_progress is not None:
                                on_progress(
                                    DownloadProgress(
                                        received_bytes=received,
                                        total_bytes=total_bytes,
                                        elapsed_s=time.monotonic() - started,
                                    )
                                )
                _zip_sanity_check(dest_path, context="wapicall")
                return dest_path
            except (CmieAuthError, CmieRateLimitError, CmieZipError):
                raise
            except requests.Timeout as e:
                err = CmieNetworkError(code="TIMEOUT", message="CMIE wapicall timed out.", detail=str(e))
            except requests.RequestException as e:
                err = CmieNetworkError(code="NETWORK", message="Network error calling CMIE wapicall.", detail=str(e))
            except Exception as e:  # pragma: no cover
                err = CmieNetworkError(code="UNKNOWN", message="Unexpected error calling CMIE wapicall.", detail=str(e))

            if attempt > self._max_retries:
                raise err
            base = 1.0 * (2 ** (attempt - 1))
            time.sleep(min(20.0, base) * (0.7 + 0.6 * random.random()))

