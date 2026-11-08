"""Migration helper for existing legacy pickled Pre-IPO dossiers into the owner-scoped evidence ledger."""
from pathlib import Path
from typing import Optional
import pickle
import io
from datetime import date
from models.pre_ipo_schema import PreIPODealDossier
from models import pre_ipo_evidence as ledger

CUSTOM_STORE_DIR = Path(__file__).resolve().parent.parent / "data" / "pre_ipo_custom"

def get_custom_store_dir() -> Path:
    CUSTOM_STORE_DIR.mkdir(parents=True, exist_ok=True)
    return CUSTOM_STORE_DIR

def migrate_legacy_pickle(owner: str, role: str, pkl_path: Path) -> Optional[str]:
    """Explicit, controlled migration of an existing saved dossier into the owner-scoped evidence ledger."""
    ledger.actor(owner, role)
    if role not in {"admin", "researcher"}:
        raise PermissionError("Viewers cannot migrate dossiers")
    if not pkl_path.exists():
        return None
    with open(pkl_path, "rb") as f:
        dossier = pickle.load(f)
    if not isinstance(dossier, PreIPODealDossier):
        raise ValueError("Invalid dossier file structure")

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(100, 750, f"Migrated Prospectus: {dossier.company_name}")
    c.drawString(100, 730, f"Filing: {dossier.filing_type} {dossier.filing_date}")
    c.save()
    pdf_bytes = buf.getvalue()

    metadata = {
        "title": f"{dossier.company_name} {dossier.filing_type}",
        "filing_type": dossier.filing_type or "DRHP",
        "version": dossier.filing_date or "Draft 1.0",
        "available_by": str(date.today()),
        "rights": "Migrated Regulatory Filing",
        "official_url": "Legacy Migration",
        "issuer": dossier.company_name,
        "retention_policy": "Migrated into evidence ledger",
    }
    return ledger.import_dossier(owner, role, dossier.company_name, dossier, pdf_bytes, metadata)
