"""Company financing evidence and debt register validation. No assumed capacity."""
from datetime import date, datetime
from io import BytesIO
import zipfile

import pandas as pd

from models.debt_metrics import finite

FACILITY_COLUMNS = ["facility_id", "instrument", "lender", "currency", "drawn_balance",
    "committed_undrawn", "rate_type", "annual_rate_pct", "benchmark", "spread_bps",
    "next_reset", "maturity", "security", "source"]
REPAYMENT_COLUMNS = ["facility_id", "payment_date", "principal", "source"]
CONTEXT_FIELDS = ["currency", "scale", "statement_basis", "as_of", "source", "unrestricted_cash"]


def _blank(value):
    return value is None or (isinstance(value, str) and not value.strip()) or bool(pd.isna(value))


def _date(value, label, errors):
    if _blank(value):
        return None
    try:
        return value.date() if isinstance(value, datetime) else date.fromisoformat(str(value).strip())
    except ValueError:
        errors.append(f"{label}: use a valid YYYY-MM-DD date.")


def _rows(frame, columns):
    frame = pd.DataFrame(frame, columns=columns)
    return [row for row in frame.to_dict("records") if any(not _blank(v) for v in row.values())]


def validate_register(context, facilities, repayments):
    """Return cleaned inputs, blocking errors and explicit evidence gaps."""
    errors, gaps = [], []
    c = {key: None if _blank(context.get(key)) else context.get(key) for key in CONTEXT_FIELDS}
    for key in ("currency", "scale", "statement_basis", "source"):
        if c[key] is not None:
            c[key] = str(c[key]).strip()
    for key in ("currency", "scale", "statement_basis", "as_of", "source"):
        if c[key] is None:
            gaps.append(f"Confirm {key.replace('_', ' ')}.")
    if c["currency"] is not None:
        c["currency"] = str(c["currency"]).upper().strip()
        if len(c["currency"]) != 3 or not c["currency"].isalpha():
            errors.append("Currency must be a three-letter code such as INR.")
    as_of = _date(c["as_of"], "As-of date", errors)
    c["as_of"] = as_of.isoformat() if as_of else None
    if c["scale"] not in (None, "units", "thousands", "lakhs", "millions", "crores"):
        errors.append("Select a supported monetary scale.")
    if c["statement_basis"] not in (None, "standalone", "consolidated"):
        errors.append("Select standalone or consolidated statements.")
    cash = finite(c["unrestricted_cash"])
    if c["unrestricted_cash"] is not None and (cash is None or cash < 0):
        errors.append("Unrestricted cash must be a finite nonnegative amount.")
    c["unrestricted_cash"] = cash
    if cash is None:
        gaps.append("Confirm unrestricted cash; reported cash is not automatically available.")
    clean_facilities, ids, maturity_dates = [], set(), {}
    for i, row in enumerate(_rows(facilities, FACILITY_COLUMNS), 1):
        row = {key: None if _blank(v) else v for key, v in row.items()}
        for key in ("instrument", "lender", "rate_type", "benchmark", "security", "source"):
            if row[key] is not None:
                row[key] = str(row[key]).strip()
        fid = str(row["facility_id"] or "").strip()
        label = f"Facility row {i}"
        if not fid or fid in ids:
            errors.append(f"{label}: supply a unique facility ID.")
        ids.add(fid)
        row["facility_id"] = fid
        for key in ("instrument", "lender", "currency", "rate_type", "maturity", "source"):
            if row[key] is None:
                gaps.append(f"{fid or label}: supply {key.replace('_', ' ')}.")
        row["currency"] = str(row["currency"]).strip().upper() if row["currency"] else None
        if row["currency"] is not None and (len(row["currency"]) != 3 or not row["currency"].isalpha()):
            errors.append(f"{label}: currency must be a three-letter code.")
        if row["rate_type"] not in (None, "fixed", "floating"):
            errors.append(f"{label}: rate_type must be fixed or floating.")
        for key in ("drawn_balance", "committed_undrawn", "annual_rate_pct", "spread_bps"):
            value = finite(row[key])
            if row[key] is not None and (value is None or value < 0):
                errors.append(f"{label}: {key} must be finite and nonnegative.")
            if row[key] is None and key in ("drawn_balance", "committed_undrawn", "annual_rate_pct"):
                gaps.append(f"{fid or label}: supply {key.replace('_', ' ')}; blank is not zero.")
            row[key] = value
        if row["rate_type"] == "floating" and (not row["benchmark"] or row["spread_bps"] is None or not row["next_reset"]):
            gaps.append(f"{fid or label}: confirm floating benchmark, spread and next reset.")
        for key in ("maturity", "next_reset"):
            parsed = _date(row[key], f"{label} {key}", errors)
            row[key] = parsed.isoformat() if parsed else None
            if key == "maturity":
                maturity_dates[fid] = parsed
                if parsed and as_of and parsed < as_of:
                    gaps.append(f"{fid}: maturity is before as-of date; confirm overdue/refinanced status.")
        clean_facilities.append(row)
    clean_repayments = []
    seen = set()
    for i, row in enumerate(_rows(repayments, REPAYMENT_COLUMNS), 1):
        row = {key: None if _blank(v) else v for key, v in row.items()}
        fid = str(row["facility_id"] or "").strip()
        when = _date(row["payment_date"], f"Repayment row {i}", errors)
        principal = finite(row["principal"])
        if fid not in ids:
            errors.append(f"Repayment row {i}: facility ID does not exist.")
        if when is None or principal is None or principal <= 0:
            errors.append(f"Repayment row {i}: payment date and positive principal are required.")
        if when and as_of and when <= as_of:
            errors.append(f"Repayment row {i}: future principal must fall after as-of date.")
        if when and maturity_dates.get(fid) and when > maturity_dates[fid]:
            errors.append(f"Repayment row {i}: payment is after facility maturity.")
        if (fid, when) in seen:
            errors.append(f"Repayment row {i}: duplicate facility/date; combine principal amounts.")
        seen.add((fid, when))
        if not row["source"]:
            gaps.append(f"Repayment row {i}: add source evidence.")
        clean_repayments.append(dict(facility_id=fid, payment_date=when.isoformat() if when else None,
            principal=principal, source=str(row["source"]) if row["source"] is not None else None))
    for row in clean_facilities:
        total = sum(r["principal"] or 0 for r in clean_repayments if r["facility_id"] == row["facility_id"])
        if row["drawn_balance"] is not None:
            if total > row["drawn_balance"] + 1e-6:
                errors.append(f"{row['facility_id']}: scheduled principal exceeds drawn balance.")
            elif abs(total - row["drawn_balance"]) > 1e-6:
                gaps.append(f"{row['facility_id']}: repayment schedule does not cover the drawn balance.")
    if not clean_facilities:
        gaps.append("Add the instrument-level debt register.")
    return dict(context=c, facilities=clean_facilities, repayments=clean_repayments,
        errors=errors, gaps=list(dict.fromkeys(gaps)))


def reconcile_register(register, reported_debt, basis_confirmed=False):
    """Never sum currencies or assume that management/source bases match."""
    rows, c = register["facilities"], register["context"]
    comparable = bool(rows and basis_confirmed and c["currency"] and c["scale"] and
        c["statement_basis"] and c["as_of"] and all(r["currency"] == c["currency"] and
        r["drawn_balance"] is not None for r in rows))
    total = sum(r["drawn_balance"] for r in rows) if comparable else None
    debt = finite(reported_debt)
    return dict(comparable=comparable, drawn_total=total,
        difference=total-debt if total is not None and debt is not None else None)


def register_workbook(context=None, facilities=None, repayments=None):
    """One Excel template/import schema; blank template does not invent amounts."""
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        pd.DataFrame([context or {}], columns=CONTEXT_FIELDS).to_excel(writer, sheet_name="Context", index=False)
        pd.DataFrame(facilities, columns=FACILITY_COLUMNS).to_excel(writer, sheet_name="Facilities", index=False)
        pd.DataFrame(repayments, columns=REPAYMENT_COLUMNS).to_excel(writer, sheet_name="Repayments", index=False)
        # Management text is literal evidence, never an executable Excel formula.
        for sheet in writer.book.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    if isinstance(cell.value, str) and cell.value.startswith("="):
                        cell.data_type = "s"
    return out.getvalue()


def read_register_workbook(data):
    if len(data) > 5_000_000:
        raise ValueError("Workbook must be at most 5 MB.")
    with zipfile.ZipFile(BytesIO(data)) as archive:
        if sum(item.file_size for item in archive.infolist()) > 25_000_000:
            raise ValueError("Workbook expands beyond the 25 MB limit.")
    sheets = pd.read_excel(BytesIO(data), sheet_name=None, engine="openpyxl")
    for sheet, columns in (("Context", CONTEXT_FIELDS), ("Facilities", FACILITY_COLUMNS), ("Repayments", REPAYMENT_COLUMNS)):
        if sheet not in sheets or not set(columns).issubset(sheets[sheet].columns):
            raise ValueError(f"Use the template: missing {sheet} sheet or columns.")
        if len(sheets[sheet]) > 5000:
            raise ValueError(f"{sheet}: at most 5,000 rows.")
    if len(sheets["Context"]) > 1:
        raise ValueError("Context sheet must contain at most one row.")
    context = sheets["Context"].iloc[0].to_dict() if len(sheets["Context"]) else {}
    return validate_register(context, sheets["Facilities"], sheets["Repayments"])


def case_payload(register, facts, basis_confirmed):
    """Snapshot the exact observed facts separately from management evidence."""
    return dict(schema_version=1, calculation_version="static-coverage-1", context=register["context"], facilities=register["facilities"],
        repayments=register["repayments"], evidence_gaps=register["gaps"],
        observed_facts=facts, basis_confirmed=bool(basis_confirmed),
        limitations=["No forward cash-flow forecast, debt-capacity approval or covenant assessment is implied."])
