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


class CmieRateLimitError(CmieError):
    pass


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

