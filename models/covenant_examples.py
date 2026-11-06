"""Versioned public FY2025 anchors with explicitly illustrative schedules.

These are frozen review examples, not latest-live company financials. INR million
from IndiGo disclosures is divided by ten to obtain INR crore.
"""
from models.covenant_pilot import CompanySnapshot, DebtSchedule, LeaseSchedule

TATA_SOURCE = "https://www.tatasteel.com/media/newsroom/press-releases/india/2025/tata-steel-reports-consolidated-ebitda-of-rs-25-802-crores-for-fy2025/"
INDIGO_SOURCE = "https://www.goindigo.in/press-releases/indigo-reported-its-fourth-quarter-and-fiscal-year-2025-results.html"


def example_catalog() -> dict:
    """Return fresh immutable snapshots; no empirical calibration is implied."""
    tata = CompanySnapshot(
        "tata-steel-fy2025", "Tata Steel Ltd.", "2025-03-31", "Consolidated", "EBITDA",
        (25802 / 4,) * 12, (700.0,) * 12, (1500.0,) * 12, (250.0,) * 12,
        12222.0, 120000.0, 40000.0,
        (
            {"label": "Historical annual EBITDA", "value": 25802.0, "kind": "observed", "source": TATA_SOURCE, "unit": "INR crore", "as_of": "2025-03-31"},
            {"label": "Historical cash and cash equivalents", "value": 12222.0, "kind": "observed", "source": TATA_SOURCE, "unit": "INR crore", "as_of": "2025-03-31"},
            {"label": "Quarterly earnings forecast", "value": 25802 / 4, "kind": "assumption", "source": "FY2025 EBITDA divided equally into four quarters, held flat for three years"},
            {"label": "Debt balance and repayments", "value": 95000.0, "kind": "assumption", "source": "Illustrative gross debt; not derived from disclosed net debt. Floating 60%, fixed 40%, quarterly principal 1000 crore"},
            {"label": "Other projection inputs", "value": "tax 700; maintenance capex 1500; working capital 250 per quarter; TNW 120000; other liabilities 40000", "kind": "assumption", "source": "Review fixture, not sanction terms or management guidance"},
        ),
    )
    indigo = CompanySnapshot(
        "indigo-fy2025", "InterGlobe Aviation Ltd. (IndiGo)", "2025-03-31", "Consolidated", "EBITDAR",
        (21252 / 4,) * 12, (500.0,) * 12, (500.0,) * 12, (500.0,) * 12,
        33153.1, 25000.0, 10000.0,
        (
            {"label": "Historical annual EBITDAR", "value": 21252.0, "kind": "observed", "source": INDIGO_SOURCE, "unit": "INR crore", "as_of": "2025-03-31"},
            {"label": "Historical free cash", "value": 33153.1, "kind": "observed", "source": INDIGO_SOURCE, "unit": "INR crore", "as_of": "2025-03-31"},
            {"label": "Historical lease liability", "value": 47980.1, "kind": "observed", "source": INDIGO_SOURCE, "unit": "INR crore", "as_of": "2025-03-31"},
            {"label": "Debt excluding leases", "value": 18829.7, "kind": "derived", "source": INDIGO_SOURCE, "calculation": "66809.8 total debt minus 47980.1 lease liability"},
            {"label": "Quarterly earnings forecast", "value": 21252 / 4, "kind": "assumption", "source": "FY2025 EBITDAR divided equally into four quarters, held flat for three years; not EBITDA"},
            {"label": "Schedule and other projection inputs", "value": "debt rate 7.5%, floating; debt principal 200/quarter; lease rate 8%, principal 1500/quarter; tax, capex and working capital each 500/quarter; TNW 25000; other liabilities 10000", "kind": "assumption", "source": "Review fixture, not lease contracts, sanction terms or management guidance"},
        ),
    )
    return {
        "tata-steel-fy2025": {
            "snapshot": tata, "aliases": ("tata steel", "248136", "tata-steel-fy2025"),
            "debts": (DebtSchedule("Floating bank debt", 57000, 0.09, True, (600.0,) * 12),
                      DebtSchedule("Fixed bank debt", 38000, 0.08, False, (400.0,) * 12)),
            "leases": (),
        },
        "indigo-fy2025": {
            "snapshot": indigo, "aliases": ("indigo", "interglobe aviation", "395047", "indigo-fy2025"),
            "debts": (DebtSchedule("Bank debt excluding leases", 18829.7, 0.075, True, (200.0,) * 12),),
            "leases": (LeaseSchedule("Aircraft lease obligations", 47980.1, 0.08, (1500.0,) * 12, (0.0,) * 12),),
        },
    }
