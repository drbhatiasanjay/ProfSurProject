from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CmieError(Exception):
    code: str
    message: str
    detail: Optional[str] = None

    def __str__(self) -> str:
        base = f"{self.code}: {self.message}"
        return f"{base}\n{self.detail}" if self.detail else base


class CmieAuthError(CmieError):
    pass


class CmieEntitlementError(CmieError):
    pass


@dataclass(frozen=True)
class CmieRateLimitError(CmieError):
    """429 (or local bucket refusal). `retry_after_s` holds the parsed `Retry-After`
    header from CMIE when present, so callers can time.sleep() without re-parsing
    `detail`.  See docs/plans/2026-04-21-cmie-refactor-execution-strategy.md §F.3.6.
    """
    retry_after_s: Optional[float] = None


class CmieNetworkError(CmieError):
    pass


class CmieZipError(CmieError):
    pass


class CmieParseError(CmieError):
    pass


class CmieSchemaError(CmieError):
    pass


class CmieValidationError(CmieError):
    pass


class CmieStorageError(CmieError):
    pass

