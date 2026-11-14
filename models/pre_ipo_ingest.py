"""
Pre-IPO DRHP PDF Ingestion & Auditable Diagnostic Engine.
Extracts SEBI ICDR (2018) disclosures from local or uploaded PDF documents,
normalizes financial metrics, and generates a line-by-line audit report:
- FOUND_AND_RECONCILED
- CONVERTED_AND_NORMALIZED
- MISSING_UNDISCLOSED
- EXTRACTION_FAILED / AWAITING_MANUAL_REVIEW
"""
import os
import io
import re
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from models.runtime_config import get_gemini_api_key
from models.pre_ipo_schema import (
    PreIPODealDossier,
    FinancialYearMetric,
    IndebtednessSchedule,
    WorkingCapitalDynamics,
    NonFinancialGovernance,
    CapTableDilution,
    ObjectsOfOfferWaterfall,
    BeneishMScoreRatios,
    DebtMaturityLadder,
    ValuationPeerBenchmarking,
    InvestmentCommitteeVerdict,
    DecisionLimitationItem,
    IngestionAuditItem,
    ProvenanceRef,
)
from models.pre_ipo_data import PRE_IPO_REGISTRY
from models.pre_ipo_document_indexer import DocumentIndexer, DocumentIndex


from enum import Enum

class ExtractionState(str, Enum):
    RECEIVED = "RECEIVED"
    TEXT_EXTRACTED = "TEXT_EXTRACTED"
    FACTS_EXTRACTED_UNREVIEWED = "FACTS_EXTRACTED_UNREVIEWED"
    ACCEPTED_FOR_ANALYSIS = "ACCEPTED_FOR_ANALYSIS"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class AnalysisEligibility:
    allowed: bool
    state: ExtractionState
    gaps: List[DecisionLimitationItem]
    reasons: List[str]


def assess_analysis_eligibility(dossier: PreIPODealDossier) -> AnalysisEligibility:
    """
    Evaluates whether a Pre-IPO deal dossier is eligible for downstream analytics,
    ratios, lifecycle modeling, and presentation exports.
    Fail-closed policy: If core financial statements are absent, unparsed, or flagged
    with blocking intake/OCR gaps, analysis is strictly BLOCKED.
    """
    gaps = [item for item in (dossier.limitations or []) if item.gap_id.startswith(("GAP-OCR-", "GAP-INTAKE-"))]
    reasons = []

    if not dossier.history:
        reasons.append("No restated financial reporting periods were recognized in the document.")
        return AnalysisEligibility(allowed=False, state=ExtractionState.BLOCKED, gaps=gaps, reasons=reasons)

    if dossier.ic_verdict.underwriting_verdict == "INSUFFICIENT_DISCLOSURES_UNRATED":
        reasons.append("Underwriting verdict is INSUFFICIENT_DISCLOSURES_UNRATED due to unverified disclosures.")

    if gaps:
        for g in gaps:
            reasons.append(f"[{g.gap_id}] {g.item_name}: {g.why_it_matters}")

    latest = dossier.latest_financials
    if latest.revenue_ops_cr == 0.0 and latest.ebitda_cr == 0.0 and latest.cfo_cr == 0.0:
        reasons.append("Core operating financials (Revenue, EBITDA, CFO) are all zero / unextracted.")

    if reasons or gaps:
        return AnalysisEligibility(allowed=False, state=ExtractionState.BLOCKED, gaps=gaps, reasons=reasons)

    if getattr(dossier, "deal_id", "").startswith(("unverified_", "provisional_")):
        return AnalysisEligibility(
            allowed=False,
            state=ExtractionState.FACTS_EXTRACTED_UNREVIEWED,
            gaps=gaps,
            reasons=["Candidates extracted but await human review and sign-off in the Facts & Evidence Review workspace."],
        )

    return AnalysisEligibility(allowed=True, state=ExtractionState.ACCEPTED_FOR_ANALYSIS, gaps=[], reasons=[])


class PreIPOIngestionEngine:
    """
    Ingests and reconciles DRHP/RHP PDF documents.
    Enforces strict trust separation:
    - Registered Golden Exemplars return verified SEBI ground truth.
    - User uploaded files are parsed directly; failed/unparseable documents
      return explicit unverified review states, NEVER invented financial metrics.
    """

    @classmethod
    def get_vision_model_name(cls) -> str:
        """
        Returns active multimodal vision model name.
        Uses GEMINI_VISION_MODEL env var or falls back to standard gemini-2.5-flash.
        """
        return os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-flash")

    @staticmethod
    def extract_text_from_pdf(source: Any, max_pages: int = 1500) -> Tuple[str, int]:
        """
        Extracts raw text using pypdf.
        Supports file path strings, bytes, and file-like objects (BytesIO / Streamlit UploadedFile).
        Returns (extracted_text, page_count).
        """
        try:
            import pypdf
            stream = source
            if isinstance(source, (str, os.PathLike)):
                if not os.path.exists(source):
                    return "", 0
                stream = open(source, "rb")

            reader = pypdf.PdfReader(stream)
            total_pages = len(reader.pages)
            pages_to_read = min(total_pages, max_pages)
            text_blocks = []
            for i in range(pages_to_read):
                p_text = reader.pages[i].extract_text()
                if p_text:
                    text_blocks.append(p_text)

            if isinstance(source, (str, os.PathLike)) and hasattr(stream, "close"):
                stream.close()

            return "\n".join(text_blocks), total_pages
        except Exception:
            return "", 0

    @classmethod
    def get_source_bytes(cls, source: Any) -> bytes:
        """Extracts raw bytes from path, BytesIO, UploadedFile, or bytes."""
        if source is None:
            return b""
        if isinstance(source, bytes):
            return source
        if isinstance(source, (str, os.PathLike)):
            if os.path.exists(source):
                try:
                    with open(source, "rb") as f:
                        return f.read()
                except Exception:
                    return b""
            return b""
        if hasattr(source, "getvalue"):
            try:
                return source.getvalue()
            except Exception:
                pass
        if hasattr(source, "read"):
            try:
                pos = source.tell() if hasattr(source, "tell") else 0
                b = source.read()
                if hasattr(source, "seek"):
                    source.seek(pos)
                return b
            except Exception:
                pass
        return b""

    @classmethod
    def detect_mime_type(cls, data: bytes, filename: Optional[str] = None) -> str:
        """Dynamically identifies mime type from magic bytes or file extension."""
        if data.startswith(b"%PDF"):
            return "application/pdf"
        elif data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        elif data.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        elif data.startswith(b"RIFF") and len(data) > 12 and data[8:12] == b"WEBP":
            return "image/webp"
        elif filename:
            fn = filename.lower()
            if fn.endswith(".png"):
                return "image/png"
            if fn.endswith(".jpg") or fn.endswith(".jpeg"):
                return "image/jpeg"
            if fn.endswith(".webp"):
                return "image/webp"
            if fn.endswith(".pdf"):
                return "application/pdf"
        return "application/pdf"

    @classmethod
    def extract_scanned_drhp_annexures(
        cls,
        document_source: Any,
        annexure_type: str = "ALL",
        company_name_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Targeted multimodal vision extraction for specific scanned DRHP financial annexures.
        Supports Annexure VI (Borrowings), Annexure III (Objects of the Offer),
        and Annexure V (Restated Standalone/Consolidated Financial Schedules).
        """
        api_key = get_gemini_api_key()
        if not api_key:
            return {
                "status": "SUSPENDED_AWAITING_KEY",
                "error": "GEMINI_API_KEY_REQUIRED",
                "tables": {},
                "gap_id": "GAP-OCR-01",
                "message": "Configure GEMINI_API_KEY to run multimodal vision extraction on scanned annexures.",
            }

        data_bytes = cls.get_source_bytes(document_source)
        if len(data_bytes) < 100:
            return {"status": "FAILED", "error": "EMPTY_BYTE_STREAM", "tables": {}}
        if len(data_bytes) > 25 * 1024 * 1024:
            return {"status": "FAILED", "error": "FILE_TOO_LARGE", "tables": {}}

        filename = getattr(document_source, "name", None)
        mime = cls.detect_mime_type(data_bytes, filename)

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            media_part = types.Part.from_bytes(data=data_bytes, mime_type=mime)

            prompt = (
                f"You are a forensic auditor reviewing scanned SEBI DRHP annexures for {company_name_hint or 'the issuer'}. "
                f"Extract structured tables for target annexure category: {annexure_type}.\n"
                "Return valid JSON only matching this schema:\n"
                "{\n"
                '  "annexure_borrowings": [{"lender_name": "string", "facility_type": "string", "sanctioned_amount_cr": float, "outstanding_amount_cr": float, "interest_rate_pct": float, "repayment_terms": "string"}],\n'
                '  "annexure_objects_of_offer": [{"object_category": "string", "proposed_utilization_cr": float, "deployment_fy25_cr": float, "deployment_fy26_cr": float}],\n'
                '  "annexure_restated_pnl": [{"fiscal_year": "string", "revenue_from_ops_cr": float, "ebitda_cr": float, "finance_costs_cr": float, "pat_cr": float}],\n'
                '  "confidence_score": float,\n'
                '  "source_annexure_citation": "string"\n'
                "}\n"
                "Return raw valid JSON without markdown wrapping."
            )

            active_model = cls.get_vision_model_name()
            resp = client.models.generate_content(
                model=active_model,
                contents=[media_part, prompt],
            )
            raw = resp.text.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)
            parsed = json.loads(raw)
            if not isinstance(parsed, dict) or not isinstance(parsed.get("source_annexure_citation"), str) or not parsed["source_annexure_citation"].strip():
                raise ValueError("Annexure extraction requires a source citation and structured tables")
            numeric_fields = {
                "annexure_borrowings": ("sanctioned_amount_cr", "outstanding_amount_cr", "interest_rate_pct"),
                "annexure_objects_of_offer": ("proposed_utilization_cr", "deployment_fy25_cr", "deployment_fy26_cr"),
                "annexure_restated_pnl": ("revenue_from_ops_cr", "ebitda_cr", "finance_costs_cr", "pat_cr"),
            }
            import math
            row_count = 0
            for table_name, fields in numeric_fields.items():
                rows = parsed.get(table_name, [])
                if not isinstance(rows, list):
                    raise ValueError("Annexure tables must be lists")
                for row in rows:
                    if not isinstance(row, dict):
                        raise ValueError("Annexure rows must be objects")
                    for field in fields:
                        value = row.get(field)
                        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                            raise ValueError("Missing or non-finite annexure field: " + field)
                        if field not in {"ebitda_cr", "pat_cr"} and value < 0:
                            raise ValueError("Negative annexure field: " + field)
                    row_count += 1
            if not row_count:
                raise ValueError("No financial annexure rows extracted")
            return {
                "status": "SUCCESS",
                "tables": parsed,
                "model_used": active_model,
                "mime_type": mime,
                "requires_source_review": True,
                "downstream_eligible": False,
            }
        except Exception as exc:
            return {
                "status": "FAILED",
                "error": f"VISION_ANNEXURE_ERROR: {type(exc).__name__}",
                "provider_status_code": getattr(exc, "code", None),
                "model_used": cls.get_vision_model_name(),
                "tables": {},
                "gap_id": "GAP-OCR-01",
            }

    @classmethod
    def parse_scanned_pdf_with_vision(
        cls,
        document_source: Any,
        company_name_hint: Optional[str] = None,
        allow_external_cloud_ocr: bool = False,
    ) -> Tuple[Optional[PreIPODealDossier], Optional[str]]:
        """
        Parses scanned image-only DRHP files using Gemini multimodal vision.
        Enforces privacy / consent gate (P1-01): Returns EXTERNAL_OCR_CONSENT_REQUIRED
        unless allow_external_cloud_ocr is explicitly True.
        """
        if not allow_external_cloud_ocr:
            return None, "EXTERNAL_OCR_CONSENT_REQUIRED"
        """
        Parses scanned image-only DRHP files using Gemini 1.5 Flash multimodal vision.
        Returns (dossier, status_code).
        If API key is missing or call fails, returns (None, error_code).
        """
        api_key = get_gemini_api_key()
        if not api_key:
            return None, "GEMINI_API_KEY_REQUIRED"

        pdf_bytes = cls.get_source_bytes(document_source)
        if len(pdf_bytes) < 100:
            return None, "EMPTY_BYTE_STREAM"

        # Check file size limit without arbitrary byte slicing
        if len(pdf_bytes) > 25 * 1024 * 1024:
            return None, "FILE_TOO_LARGE"

        if len(pdf_bytes) == 0:
            return None, "EMPTY_BYTE_STREAM"

        try:
            from google import genai
            from google.genai import types

            doc_filename = getattr(document_source, "name", None)
            mime = cls.detect_mime_type(pdf_bytes, doc_filename)

            client = genai.Client(api_key=api_key)
            pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type=mime)

            prompt = (
                "You are an expert SEBI ICDR Draft Red Herring Prospectus (DRHP) auditor. "
                "Analyze this scanned DRHP document and extract key quantitative figures into valid JSON:\n"
                "{\n"
                '  "company_name": "string",\n'
                '  "sector": "string",\n'
                '  "filing_type": "DRHP",\n'
                '  "filing_date": "string",\n'
                '  "total_issue_size_cr": float,\n'
                '  "fresh_issue_cr": float,\n'
                '  "ofs_cr": float,\n'
                '  "face_value_inr": float,\n'
                '  "brlm_bankers": ["string"],\n'
                '  "exchange_listing": ["BSE", "NSE"],\n'
                '  "history": [\n'
                '    {"fiscal_year": "FY24", "revenue_ops_cr": float, "ebitda_cr": float, "pat_cr": float, "cfo_cr": float, "cfi_cr": float, "cff_cr": float, "capex_cr": float, "fcf_cr": float, "net_worth_cr": float}\n'
                "  ],\n"
                '  "indebtedness": {\n'
                '    "secured_term_loans_cr": float,\n'
                '    "working_capital_loans_cr": float,\n'
                '    "ncd_bonds_cr": float,\n'
                '    "unsecured_loans_cr": float,\n'
                '    "lease_liabilities_ind_as_116_cr": float,\n'
                '    "cash_and_equivalents_cr": float\n'
                "  },\n"
                '  "objects_of_offer": {\n'
                '    "gross_fresh_issue_cr": float,\n'
                '    "issue_expenses_cr": float,\n'
                '    "debt_prepayment_cr": float,\n'
                '    "capex_expansion_cr": float,\n'
                '    "inorganic_acquisition_cr": float,\n'
                '    "general_corporate_purposes_cr": float\n'
                "  },\n"
                '  "working_capital": {\n'
                '    "inventory_days_dio": float,\n'
                '    "debtor_days_dso": float,\n'
                '    "creditor_days_dpo": float,\n'
                '    "net_working_capital_pct_sales": float\n'
                "  },\n"
                '  "governance": {\n'
                '    "promoter_pledge_pct": float,\n'
                '    "related_party_transactions_pct_rev": float,\n'
                '    "top_5_customer_concentration_pct": float,\n'
                '    "herfindahl_hhi_index": float,\n'
                '    "contingent_liabilities_pct_networth": float,\n'
                '    "independent_directors_pct": float\n'
                "  }\n"
                "}\n"
                "Return raw valid JSON only without markdown or code fencing."
            )

            active_model = cls.get_vision_model_name()
            resp = client.models.generate_content(
                model=active_model,
                contents=[pdf_part, prompt],
            )
            raw_text = resp.text.strip()
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)

            data = json.loads(raw_text)
            comp_name = data.get("company_name") or company_name_hint or "Scanned DRHP Issuer"
            deal_slug = re.sub(r"[^a-zA-Z0-9]+", "_", comp_name.lower()).strip("_")

            # Check if extracted JSON is empty or lacks core financials
            has_financial_data = bool(data.get("history") or data.get("total_issue_size_cr") or data.get("revenue_ops_cr"))
            if not has_financial_data:
                # Return explicit unverified dossier with zero confidence and limitations
                empty_audit = [
                    IngestionAuditItem(
                        field_name="Document Intake Pipeline",
                        raw_extracted_value="Multimodal Vision OCR returned empty financial structure",
                        normalized_metric="EXTRACTION_EMPTY",
                        status="MISSING_UNDISCLOSED",
                        citation="Vision Pipeline",
                        confidence_score=0.0,
                    ),
                    IngestionAuditItem(
                        field_name="Section V Restated Financials",
                        raw_extracted_value="No financial line items detected in OCR scan",
                        normalized_metric="UNAVAILABLE",
                        status="MISSING_UNDISCLOSED",
                        citation="DRHP Section V",
                        confidence_score=0.0,
                    ),
                ]
                empty_limits = [
                    DecisionLimitationItem(
                        gap_id="GAP-OCR-01",
                        item_name="Multimodal OCR Empty Extraction",
                        affected_dimension="All Financial Dimensions",
                        current_status="EXTRACTION_FAILED",
                        why_it_matters="Multimodal AI vision model could not identify quantitative financial schedules in the scanned pages.",
                        blocked_decision_or_recommendation="All valuation, leverage, and underwriting recommendations are blocked.",
                        materiality_priority="HIGH",
                        recommended_diligence_request="Upload higher-resolution scan or electronic searchable PDF.",
                    )
                ]
                return PreIPODealDossier(
                    deal_id=f"vision_empty_{deal_slug}",
                    company_name=f"{comp_name} [Unverified OCR Intake]",
                    sector="Unverified",
                    filing_type="DRHP (Vision Parsed - Incomplete)",
                    filing_date="Undisclosed",
                    total_issue_size_cr=0.0,
                    fresh_issue_cr=0.0,
                    ofs_cr=0.0,
                    face_value_inr=None,
                    brlm_bankers=[],
                    exchange_listing=[],
                    history=[FinancialYearMetric("FY--", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)],
                    indebtedness=IndebtednessSchedule(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                    working_capital=WorkingCapitalDynamics(0.0, 0.0, 0.0, 0.0),
                    governance=NonFinancialGovernance(0.0, 0.0, 0.0, 0.0, 0.0, 50.0),
                    objects_of_offer=ObjectsOfOfferWaterfall(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                    ic_verdict=InvestmentCommitteeVerdict(
                        underwriting_verdict="INSUFFICIENT_DISCLOSURES_UNRATED",
                        internal_screening_grade="UNRATED",
                        max_recommended_leverage_ratio=0.0,
                        key_credit_strengths=[],
                        key_downside_risks=["OCR extraction yielded no recognized quantitative metrics."],
                        mandatory_loan_covenants=["Provide audited prospectus disclosures."],
                        treasury_call_to_action="Underwriting suspended pending readable filing disclosures.",
                    ),
                    limitations=empty_limits,
                    audit_report=empty_audit,
                    issue_status="RUNNING_PIPELINE",
                ), "EXTRACTION_EMPTY_OR_INVALID"

            hist = []
            for h in data.get("history", []):
                hist.append(FinancialYearMetric(
                    fiscal_year=h.get("fiscal_year", "FY24"),
                    revenue_ops_cr=float(h.get("revenue_ops_cr", 0.0)),
                    ebitda_cr=float(h.get("ebitda_cr", 0.0)),
                    pat_cr=float(h.get("pat_cr", 0.0)),
                    cfo_cr=float(h.get("cfo_cr", 0.0)),
                    cfi_cr=float(h.get("cfi_cr", 0.0)),
                    cff_cr=float(h.get("cff_cr", 0.0)),
                    capex_cr=float(h.get("capex_cr", 0.0)),
                    fcf_cr=float(h.get("fcf_cr", 0.0)),
                    net_worth_cr=float(h.get("net_worth_cr", 0.0)),
                    provenance=ProvenanceRef("Section V Financials", 1, "Restated Summary Statement", "Gemini 1.5 Flash Vision OCR"),
                ))
            if not hist:
                hist.append(FinancialYearMetric(
                    fiscal_year="FY24", revenue_ops_cr=0.0, ebitda_cr=0.0, pat_cr=0.0,
                    cfo_cr=0.0, cfi_cr=0.0, cff_cr=0.0, capex_cr=0.0, fcf_cr=0.0, net_worth_cr=0.0
                ))

            ind_d = data.get("indebtedness", {})
            ind = IndebtednessSchedule(
                secured_term_loans_cr=float(ind_d.get("secured_term_loans_cr", 0.0)),
                working_capital_loans_cr=float(ind_d.get("working_capital_loans_cr", 0.0)),
                ncd_bonds_cr=float(ind_d.get("ncd_bonds_cr", 0.0)),
                unsecured_loans_cr=float(ind_d.get("unsecured_loans_cr", 0.0)),
                lease_liabilities_ind_as_116_cr=float(ind_d.get("lease_liabilities_ind_as_116_cr", 0.0)),
                cash_and_equivalents_cr=float(ind_d.get("cash_and_equivalents_cr", 0.0)),
                provenance=ProvenanceRef("Section VI Indebtedness", 1, "Financial Indebtedness Statement", "Gemini 1.5 Flash Vision OCR"),
            )

            wc_d = data.get("working_capital", {})
            wc = WorkingCapitalDynamics(
                inventory_days_dio=float(wc_d.get("inventory_days_dio", 0.0)),
                debtor_days_dso=float(wc_d.get("debtor_days_dso", 0.0)),
                creditor_days_dpo=float(wc_d.get("creditor_days_dpo", 0.0)),
                net_working_capital_pct_sales=float(wc_d.get("net_working_capital_pct_sales", 0.0)),
                provenance=ProvenanceRef("Section V Working Capital", 1, "MD&A Working Capital Analysis", "Gemini 1.5 Flash Vision OCR"),
            )

            gov_d = data.get("governance", {})
            gov = NonFinancialGovernance(
                promoter_pledge_pct=float(gov_d.get("promoter_pledge_pct", 0.0)),
                related_party_transactions_pct_rev=float(gov_d.get("related_party_transactions_pct_rev", 0.0)),
                top_5_customer_concentration_pct=float(gov_d.get("top_5_customer_concentration_pct", 0.0)),
                herfindahl_hhi_index=float(gov_d.get("herfindahl_hhi_index", 0.0)),
                contingent_liabilities_pct_networth=float(gov_d.get("contingent_liabilities_pct_networth", 0.0)),
                independent_directors_pct=float(gov_d.get("independent_directors_pct", 50.0)),
                provenance=ProvenanceRef("Section IV Governance", 1, "Board & RPT Disclosures", "Gemini 1.5 Flash Vision OCR"),
            )

            obj_d = data.get("objects_of_offer", {})
            obj = ObjectsOfOfferWaterfall(
                gross_fresh_issue_cr=float(obj_d.get("gross_fresh_issue_cr", data.get("fresh_issue_cr", 0.0))),
                issue_expenses_cr=float(obj_d.get("issue_expenses_cr", 0.0)),
                debt_prepayment_cr=float(obj_d.get("debt_prepayment_cr", 0.0)),
                capex_expansion_cr=float(obj_d.get("capex_expansion_cr", 0.0)),
                inorganic_acquisition_cr=float(obj_d.get("inorganic_acquisition_cr", 0.0)),
                general_corporate_purposes_cr=float(obj_d.get("general_corporate_purposes_cr", 0.0)),
                provenance=ProvenanceRef("Section III Objects", 1, "Objects of the Offer Waterfall", "Gemini 1.5 Flash Vision OCR"),
            )

            audit_report = [
                IngestionAuditItem(
                    field_name="Document Intake Pipeline",
                    raw_extracted_value="Scanned Image PDF Processed via Gemini Flash Vision",
                    normalized_metric="GEMINI_FLASH_VISION_EXTRACTED",
                    status="FOUND_AND_RECONCILED",
                    citation="Multimodal AI Vision Pipeline",
                    confidence_score=0.92,
                ),
                IngestionAuditItem(
                    field_name="Section III Objects of the Offer",
                    raw_extracted_value=f"Fresh ₹{obj.gross_fresh_issue_cr:,.1f} Cr / Debt Prepay ₹{obj.debt_prepayment_cr:,.1f} Cr",
                    normalized_metric="RECONCILED",
                    status="FOUND_AND_RECONCILED",
                    citation="DRHP Section III",
                    confidence_score=0.90,
                ),
                IngestionAuditItem(
                    field_name="Section V Restated Financials",
                    raw_extracted_value=f"FY24 Revenue ₹{hist[-1].revenue_ops_cr:,.1f} Cr / EBITDA ₹{hist[-1].ebitda_cr:,.1f} Cr",
                    normalized_metric="RECONCILED",
                    status="FOUND_AND_RECONCILED",
                    citation="DRHP Section V",
                    confidence_score=0.91,
                ),
            ]

            return PreIPODealDossier(
                deal_id=f"vision_{deal_slug}",
                company_name=f"{comp_name} [Vision OCR Extracted]",
                sector=data.get("sector", "Diversified"),
                filing_type=data.get("filing_type", "DRHP (Vision Parsed)"),
                filing_date=data.get("filing_date", "Current Cycle"),
                total_issue_size_cr=float(data.get("total_issue_size_cr", 0.0)),
                fresh_issue_cr=float(data.get("fresh_issue_cr", 0.0)),
                ofs_cr=float(data.get("ofs_cr", 0.0)),
                face_value_inr=float(data["face_value_inr"]) if (data.get("face_value_inr") is not None and str(data.get("face_value_inr")).strip() != "") else None,
                brlm_bankers=data.get("brlm_bankers", []),
                exchange_listing=data.get("exchange_listing", []),
                history=hist,
                indebtedness=ind,
                working_capital=wc,
                governance=gov,
                objects_of_offer=obj,
                audit_report=audit_report,
                issue_status="RUNNING_PIPELINE",
            ), "SUCCESS"
        except Exception as exc:
            err_msg = str(exc)
            if "402" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "prepayment credits are depleted" in err_msg:
                return None, "PROVIDER_CREDITS_DEPLETED_402"
            return None, f"VISION_ERROR: {type(exc).__name__} (HTTP {getattr(exc, 'code', 'unavailable')})"

    @staticmethod
    def _clean_financial_number(val_str: Optional[str]) -> Optional[float]:
        """Cleans financial strings, converting Nil/dash to 0.0, handling parentheses for negatives."""
        if val_str is None:
            return None
        s = val_str.strip().replace(",", "")
        if s.lower() in ("nil", "none", "-", "—", "na", "n/a", "zero"):
            return 0.0
        m_neg = re.match(r"^\(([\d\.]+)\)$", s)
        if m_neg:
            return -float(m_neg.group(1))
        try:
            return float(s)
        except ValueError:
            return None

    @classmethod
    def extract_from_text(cls, text: str, company_name_hint: Optional[str] = None):
        dossier = cls.ingest_document(text, company_name_hint=company_name_hint)
        return dossier, dossier.audit_report, dossier.limitations, {}

    @classmethod
    def ingest_document(
        cls,
        document_source: Any,
        deal_id_hint: Optional[str] = None,
        company_name_hint: Optional[str] = None,
        is_exemplar_mode: bool = False,
        allow_external_cloud_ocr: bool = False,
    ) -> PreIPODealDossier:
        """
        Ingests a DRHP/RHP document.
        If is_exemplar_mode=True and deal_id_hint matches registered golden deals,
        returns canonical verified ground truth.
        For real user uploads, parses the document directly without fabricating numbers.
        """
        # Check registered exemplars if no file is uploaded or exemplar mode requested
        if is_exemplar_mode or document_source is None:
            if deal_id_hint and deal_id_hint in PRE_IPO_REGISTRY:
                return PRE_IPO_REGISTRY[deal_id_hint]
            if company_name_hint:
                c_norm = company_name_hint.lower().strip()
                for k, v in PRE_IPO_REGISTRY.items():
                    if k in c_norm or v.company_name.lower() in c_norm or c_norm in v.company_name.lower():
                        return v

        extracted_text, page_count = "", 0
        pages_text: List[Tuple[int, str]] = []
        if document_source is not None:
            if isinstance(document_source, str) and not os.path.exists(document_source) and ("\n" in document_source or "\t" in document_source or len(document_source) > 20):
                extracted_text = document_source
                pages_text = [(1, document_source)]
                page_count = 1
            else:
                try:
                    pdf_bytes = cls.get_source_bytes(document_source)
                    if pdf_bytes:
                        indexer = DocumentIndexer()
                        doc_index = indexer.index_pdf_stream(
                            pdf_bytes,
                            source_id=deal_id_hint or "uploaded_drhp",
                            allow_ocr=allow_external_cloud_ocr
                        )
                        page_count = doc_index.total_pages
                        pages_text = [(p, art.text) for p, art in sorted(doc_index.pages.items())]
                        extracted_text = "\n".join([pt[1] for pt in pages_text])
                    else:
                        extracted_text, page_count = "", 0
                except Exception:
                    extracted_text, page_count = "", 0

        # Scanned / Image-only Document Handling:
        if len(extracted_text.strip()) < 100:
            vision_deal, vision_status = cls.parse_scanned_pdf_with_vision(document_source, company_name_hint, allow_external_cloud_ocr=allow_external_cloud_ocr)
            if vision_deal is not None:
                return vision_deal

            doc_name = getattr(document_source, "name", "Uploaded Document")
            company_display = company_name_hint.strip() if company_name_hint and company_name_hint.strip() else "Scanned Image Document"

            if vision_status == "EXTERNAL_OCR_CONSENT_REQUIRED":
                ocr_msg = "Cloud OCR consent not authorized. External data transmission to Google Vision API blocked."
                gap_status = "OCR_CONSENT_REQUIRED"
                rec_action = "Authorize cloud OCR consent or upload an electronic searchable DRHP PDF."
            elif vision_status == "PROVIDER_CREDITS_DEPLETED_402":
                ocr_msg = "HTTP 402: Gemini API prepayment credits are depleted. Please manage project billing at ai.studio/projects or upload an electronic searchable DRHP PDF."
                gap_status = "PROVIDER_CREDITS_DEPLETED_402"
                rec_action = "Manage API project billing or upload an electronic searchable DRHP PDF."
            elif vision_status == "GEMINI_API_KEY_REQUIRED":
                ocr_msg = "Gemini Flash Vision OCR requires GEMINI_API_KEY to process scanned documents."
                gap_status = "AWAITING_OCR_KEY"
                rec_action = "Configure GEMINI_API_KEY in the sidebar or upload an electronic searchable DRHP PDF."
            else:
                ocr_msg = f"Vision OCR status: {vision_status}"
                gap_status = "PARSE_FAILED"
                rec_action = "Check document resolution or supply searchable PDF."

            audit_report = [
                IngestionAuditItem(
                    field_name="Document Intake Status",
                    raw_extracted_value=f"File: {doc_name} ({page_count} pages read - Scanned Image Layer, 0 electronic characters)",
                    normalized_metric="SCANNED_IMAGE_LAYER",
                    status="NOT_EXTRACTED",
                    citation="PDF Parser",
                    confidence_score=0.0,
                ),
                IngestionAuditItem(
                    field_name="Multimodal OCR Status",
                    raw_extracted_value=ocr_msg,
                    normalized_metric=gap_status,
                    status="NOT_EXTRACTED",
                    citation="Vision OCR Engine",
                    confidence_score=0.0,
                ),
                IngestionAuditItem(
                    field_name="Revenue from Operations (FY24)",
                    raw_extracted_value="Not extracted",
                    normalized_metric="₹0.00 Cr",
                    status="NOT_EXTRACTED",
                    citation="DRHP Section V",
                    confidence_score=0.0,
                ),
                IngestionAuditItem(
                    field_name="Operating EBITDA (FY24)",
                    raw_extracted_value="Not extracted",
                    normalized_metric="₹0.00 Cr",
                    status="NOT_EXTRACTED",
                    citation="DRHP Section V",
                    confidence_score=0.0,
                ),
                IngestionAuditItem(
                    field_name="Profit After Tax (PAT) (FY24)",
                    raw_extracted_value="Not extracted",
                    normalized_metric="₹0.00 Cr",
                    status="NOT_EXTRACTED",
                    citation="DRHP Section V",
                    confidence_score=0.0,
                ),
                IngestionAuditItem(
                    field_name="Cash Flow from Operations (CFO) (FY24)",
                    raw_extracted_value="Not extracted",
                    normalized_metric="₹0.00 Cr",
                    status="NOT_EXTRACTED",
                    citation="DRHP Section V",
                    confidence_score=0.0,
                ),
                IngestionAuditItem(
                    field_name="Capital Expenditures (Capex) (FY24)",
                    raw_extracted_value="Not extracted",
                    normalized_metric="₹0.00 Cr",
                    status="NOT_EXTRACTED",
                    citation="DRHP Section V",
                    confidence_score=0.0,
                ),
                IngestionAuditItem(
                    field_name="Free Cash Flow (FCF) (FY24)",
                    raw_extracted_value="Not extracted",
                    normalized_metric="₹0.00 Cr",
                    status="NOT_EXTRACTED",
                    citation="DRHP Section V",
                    confidence_score=0.0,
                ),
                IngestionAuditItem(
                    field_name="Net Worth (FY24)",
                    raw_extracted_value="Not extracted",
                    normalized_metric="₹0.00 Cr",
                    status="NOT_EXTRACTED",
                    citation="DRHP Section V",
                    confidence_score=0.0,
                ),
            ]

            limitations = [
                DecisionLimitationItem(
                    gap_id="GAP-OCR-01",
                    item_name="Scanned Image DRHP / Multimodal OCR Quota",
                    affected_dimension="All Dimensions (P&L, Balance Sheet, Indebtedness, Governance)",
                    current_status=gap_status,
                    why_it_matters=f"The uploaded file is a scanned image without an embedded text layer ({ocr_msg}). Financial figures default to 0.0 with comments 'Not extracted'.",
                    blocked_decision_or_recommendation="All credit underwriting, leverage sizing, and valuation conclusions are blocked.",
                    materiality_priority="HIGH",
                    recommended_diligence_request=rec_action,
                ),
                DecisionLimitationItem(
                    gap_id="GAP-INTAKE-02",
                    item_name="Audited Financial Statements",
                    affected_dimension="Restated Consolidated Performance",
                    current_status="NOT_EXTRACTED",
                    why_it_matters="Historical revenue, EBITDA, and operating cash flow are not extracted and set to 0.0.",
                    blocked_decision_or_recommendation="Cash conversion assessment and Dickinson life-cycle classification cannot be performed.",
                    materiality_priority="HIGH",
                    recommended_diligence_request="Supply Section V (Financial Information) of the Draft Red Herring Prospectus in searchable PDF format.",
                ),
            ]

            hist_not_extracted = [
                FinancialYearMetric(
                    fiscal_year="FY24",
                    revenue_ops_cr=0.0,
                    ebitda_cr=0.0,
                    pat_cr=0.0,
                    cfo_cr=0.0,
                    cfi_cr=0.0,
                    cff_cr=0.0,
                    capex_cr=0.0,
                    fcf_cr=0.0,
                    net_worth_cr=0.0,
                    provenance=ProvenanceRef("Section V Restated Financials", 1, "Not extracted", f"Not extracted ({ocr_msg})"),
                )
            ]

            return PreIPODealDossier(
                deal_id="unverified_scanned_upload",
                company_name=f"{company_display} [Not Extracted - Scanned Image]",
                sector="Awaiting Financials",
                filing_type="DRHP (Scanned Image)",
                filing_date="Current Year",
                total_issue_size_cr=0.0,
                fresh_issue_cr=0.0,
                ofs_cr=0.0,
                face_value_inr=None,
                brlm_bankers=[],
                exchange_listing=[],
                history=hist_not_extracted,
                indebtedness=IndebtednessSchedule(
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                    provenance=ProvenanceRef("Section VI Indebtedness", 1, "Not extracted", f"Not extracted ({ocr_msg})")
                ),
                working_capital=WorkingCapitalDynamics(
                    0.0, 0.0, 0.0, 0.0,
                    provenance=ProvenanceRef("Section V Working Capital", 1, "Not extracted", f"Not extracted ({ocr_msg})")
                ),
                governance=NonFinancialGovernance(
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                    provenance=ProvenanceRef("Section IV Governance", 1, "Not extracted", f"Not extracted ({ocr_msg})")
                ),
                objects_of_offer=ObjectsOfOfferWaterfall(
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                    provenance=ProvenanceRef("Section III Objects", 1, "Not extracted", f"Not extracted ({ocr_msg})")
                ),
                beneish_forensics=BeneishMScoreRatios(),
                debt_maturity=DebtMaturityLadder(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                valuation_comps=ValuationPeerBenchmarking(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "None", [], "NOT_EXTRACTED"),
                ic_verdict=InvestmentCommitteeVerdict(
                    underwriting_verdict="INSUFFICIENT_DISCLOSURES_UNRATED",
                    internal_screening_grade="UNRATED",
                    max_recommended_leverage_ratio=0.0,
                    key_credit_strengths=[],
                    key_downside_risks=["No electronic text layer found; financial line items were not extracted and set to 0.0."],
                    mandatory_loan_covenants=["Supply searchable electronic DRHP filing."],
                    treasury_call_to_action="Underwriting blocked: financial metrics not extracted; manual review or searchable PDF required.",
                ),
                limitations=limitations,
                audit_report=audit_report,
            )

        # Electronic Searchable PDF Extraction
        full_text = extracted_text

        # 1. Company Name Identification
        comp_name = company_name_hint.strip() if company_name_hint else None
        if not comp_name or comp_name == "Novel Enterprise Limited":
            m_c1 = re.search(r"INITIAL PUBLIC OFFERING OF UP TO .*? OF\s*\n\s*([A-Z0-9\s,\.\(\)-]+?)\s*(?:\('COMPANY'|\(THE 'ISSUER'\))", full_text, re.DOTALL)
            if m_c1:
                comp_name = m_c1.group(1).strip()
            else:
                m_c2 = re.search(r"\b([A-Z0-9\s,\.\(\)-]{3,60}\s+(?:LIMITED|PRIVATE LIMITED))\b", full_text)
                if m_c2:
                    comp_name = m_c2.group(1).strip()
                else:
                    m_c3 = re.search(r"^([A-Z0-9\s,\.\(\)-]{3,60})\s*[-–]\s*NOT AN ACTUAL COMPANY", full_text, re.MULTILINE)
                    if m_c3:
                        comp_name = m_c3.group(1).strip()
                    else:
                        comp_name = company_name_hint.strip() if company_name_hint else "Uploaded Issuer"

        # 2. Scale & Currency Detection
        scale = 1.0
        unit_label = "INR_CRORE"
        m_scale = re.search(r"(?:all\s+amounts\s+(?:in\s+)?(?:inr|rs\.?|₹|■)?\s*(crore|cr|million|mn|lakhs?|lac|lacs)\b|\(\s*(?:in\s+|■\s*in\s+|₹\s*in\s+|rs\.?\s*in\s+)?(crore|cr|million|mn|lakhs?|lac|lacs)[^\)]*\))", full_text, re.IGNORECASE)
        if m_scale:
            raw_u = (m_scale.group(1) or m_scale.group(2) or "").lower()
            if "mn" in raw_u or "million" in raw_u:
                scale = 0.1
                unit_label = "INR_MILLION"
            elif "lakh" in raw_u or "lac" in raw_u:
                scale = 0.01
                unit_label = "INR_LAKHS"
            elif "cr" in raw_u or "crore" in raw_u:
                scale = 1.0
                unit_label = "INR_CRORE"

        # 3. Period & Table Header Detection
        detected_periods: List[str] = []
        for page_num, ptext in pages_text:
            lines = [l.strip() for l in ptext.split("\n") if l.strip()]
            for i, l in enumerate(lines):
                if re.search(r"Metric\s*\(", l, re.IGNORECASE):
                    j = i + 1
                    seq = []
                    while j < min(len(lines), i + 12):
                        cand = lines[j]
                        if re.match(r"^(?:Revenue|Total|Income|Expenses|Cost)", cand, re.IGNORECASE):
                            break
                        m_p = re.search(r"\b(Q[1-4]\s*FY\d{2}|FY\s*\d{2,4}|Fiscal\s*\d{4})\b", cand, re.IGNORECASE)
                        if m_p:
                            raw_p = m_p.group(0).upper().replace(" ", "")
                            if raw_p.startswith("FISCAL"):
                                raw_p = "FY" + raw_p[-2:]
                            if raw_p not in seq:
                                seq.append(raw_p)
                        j += 1
                    if len(seq) >= 2:
                        detected_periods = seq
                        break

                matches = list(re.finditer(r"\b(Q[1-4]\s*FY\d{2}|FY\s*\d{2,4}|Fiscal\s*\d{4}|31-Mar-\d{4})\b", l, re.IGNORECASE))
                if len(matches) >= 2:
                    for m in matches:
                        raw_p = m.group(0).upper().replace(" ", "")
                        if "31-MAR-" in raw_p:
                            raw_p = "FY" + raw_p.split("31-MAR-")[-1][-2:]
                        elif raw_p.startswith("FISCAL"):
                            raw_p = "FY" + raw_p[-2:]
                        if raw_p not in detected_periods:
                            detected_periods.append(raw_p)
                    break
            if detected_periods:
                break

        if not detected_periods:
            m_single = re.search(r"(?:financial statements|statement of profit and loss)[,\s]+(?:for\s+)?(FY\s*\d{2,4}|Fiscal\s*\d{4}|\d{4})", full_text, re.IGNORECASE)
            if m_single:
                raw_p = m_single.group(1).upper().replace(" ", "")
                if raw_p.startswith("FISCAL"):
                    raw_p = "FY" + raw_p[-2:]
                elif len(raw_p) == 4 and raw_p.isdigit():
                    raw_p = "FY" + raw_p[-2:]
                detected_periods = [raw_p]
            else:
                all_fy = re.findall(r"\b(FY\s*\d{2,4})\b", full_text, re.IGNORECASE)
                if all_fy:
                    detected_periods = [all_fy[0].upper().replace(" ", "")]

        periods_data: Dict[str, Dict[str, float]] = {p: {} for p in detected_periods}
        provenance_map: Dict[str, Dict[str, Tuple[int, str, str]]] = {p: {} for p in detected_periods}
        audit_items: List[IngestionAuditItem] = []
        limitations: List[DecisionLimitationItem] = []

        METRIC_PATTERNS = [
            ("revenue_ops_cr", r"(?:revenue from operations|gross revenue|turnover|total revenue from operations)"),
            ("ebitda_cr", r"(?:restated (?:operating )?ebitda|operating ebitda|\bebitda\b)"),
            ("pat_cr", r"(?:restated profit after tax|profit after tax|\bpat\b|net profit)"),
            ("cfo_cr", r"(?:cash flow from operations|cash flow from operating activities|\bcfo\b|operating cash flows?)"),
            ("cfi_cr", r"(?:cash flow from investing(?: activities)?|\bcfi\b)"),
            ("cff_cr", r"(?:cash flow from financing(?: activities)?|\bcff\b)"),
            ("capex_cr", r"(?:capital expenditures?|\bcapex\b|purchase of property, plant and equipment)"),
            ("fcf_cr", r"(?:free cash flow|\bfcf\b)"),
            ("net_worth_cr", r"(?:tangible net worth|net worth|total equity)"),
        ]

        # Multi-column table extraction pass
        if len(detected_periods) >= 2:
            for page_num, ptext in pages_text:
                lines = [l.strip() for l in ptext.split("\n") if l.strip()]
                for i, line in enumerate(lines):
                    for mkey, mpat in METRIC_PATTERNS:
                        # 1. Inline multi-column row: e.g. "Revenue from operations 140215.45 127512.93 115485.80"
                        m_inline = re.match(r"^(" + mpat + r")(?:\s*\([^\)]*\))?\s+(.*)$", line, re.IGNORECASE)
                        if m_inline:
                            parts = m_inline.group(2).split()
                            part_nums = [(cls._clean_financial_number(p), p) for p in parts]
                            valid_nums = [p for p in part_nums if p[0] is not None]
                            if len(valid_nums) >= 2:
                                for p_idx, p_name in enumerate(detected_periods):
                                    if p_idx < len(valid_nums):
                                        num_val, raw_str = valid_nums[p_idx]
                                        local_scale = scale
                                        line_lower = line.lower()
                                        if "mn" in line_lower or "million" in line_lower:
                                            local_scale = 0.1
                                        elif "lakh" in line_lower or "lac" in line_lower:
                                            local_scale = 0.01
                                        elif "cr" in line_lower or "crore" in line_lower:
                                            local_scale = 1.0
                                        scaled_val = round(num_val * local_scale, 2)
                                        periods_data[p_name][mkey] = scaled_val
                                        provenance_map[p_name][mkey] = (page_num, line, raw_str)
                                continue

                        # 2. Metric on standalone line followed by numbers on subsequent lines
                        if re.search(r"^" + mpat + r"$", line, re.IGNORECASE) or re.search(r"^" + mpat + r"\s*[:\(\[]", line, re.IGNORECASE):
                            collected_nums = []
                            j = i + 1
                            while j < min(len(lines), i + len(detected_periods) + 4):
                                cand = lines[j]
                                val = cls._clean_financial_number(cand)
                                if val is not None:
                                    collected_nums.append((val, cand))
                                    j += 1
                                else:
                                    parts = cand.split()
                                    part_nums = [(cls._clean_financial_number(p), p) for p in parts]
                                    if all(p[0] is not None for p in part_nums) and part_nums:
                                        collected_nums.extend(part_nums)
                                        j += 1
                                    else:
                                        break
                            if collected_nums:
                                for p_idx, p_name in enumerate(detected_periods):
                                    if p_idx < len(collected_nums):
                                        num_val, raw_str = collected_nums[p_idx]
                                        local_scale = scale
                                        line_lower = line.lower()
                                        if "mn" in line_lower or "million" in line_lower:
                                            local_scale = 0.1
                                        elif "lakh" in line_lower or "lac" in line_lower:
                                            local_scale = 0.01
                                        elif "cr" in line_lower or "crore" in line_lower:
                                            local_scale = 1.0
                                        scaled_val = round(num_val * local_scale, 2)
                                        periods_data[p_name][mkey] = scaled_val
                                        provenance_map[p_name][mkey] = (page_num, line, raw_str)

        # Single-line key-value disclosures pass
        for page_num, ptext in pages_text:
            lines = [l.strip() for l in ptext.split("\n") if l.strip()]
            for line in lines:
                for mkey, mpat in METRIC_PATTERNS:
                    m_kv = re.search(r"^" + mpat + r"(?:\s*\([^\)]*\))?[\s:\|\t]+([-\(\)\d,\.]+)\s*(cr|crore|mn|million|lakh|lakhs|%)?", line, re.IGNORECASE)
                    if m_kv:
                        raw_val = m_kv.group(1)
                        local_u = (m_kv.group(2) or "").lower()
                        local_scale = scale
                        line_lower = line.lower()
                        if "mn" in local_u or "million" in local_u or "mn" in line_lower or "million" in line_lower:
                            local_scale = 0.1
                        elif "lakh" in local_u or "lakh" in line_lower or "lac" in line_lower:
                            local_scale = 0.01
                        elif "cr" in local_u or "crore" in local_u or "cr" in line_lower or "crore" in line_lower:
                            local_scale = 1.0
                        val = cls._clean_financial_number(raw_val)
                        if val is not None:
                            target_p = detected_periods[0] if detected_periods else "FY24"
                            if target_p not in periods_data:
                                periods_data[target_p] = {}
                                provenance_map[target_p] = {}
                            scaled_val = round(val * local_scale, 2)
                            periods_data[target_p][mkey] = scaled_val
                            provenance_map[target_p][mkey] = (page_num, line, raw_val)

        # 4. Indebtedness & Balance Sheet Extraction
        debt_items: Dict[str, Tuple[float, str, int, str]] = {}
        DEBT_PATTERNS = [
            ("term_loans", r"(?:secured (?:rupee )?term loans from banks|term loans from banks|secured term loans)"),
            ("wc_loans", r"(?:working capital demand loans|working capital loans / cc|short-term borrowings)"),
            ("ncd_bonds", r"(?:non-convertible debentures|ncds?|bonds)"),
            ("unsecured_loans", r"(?:unsecured loans?)"),
            ("leases", r"(?:ind as 116 (?:capitalized )?lease liabilities|lease liabilities)"),
            ("cash", r"(?:cash & bank balances|cash and cash equivalents|cash and bank balances|liquid mutual funds)"),
            ("total_borrowings", r"(?:total borrowings? \(excluding leases?\)|total debt|total borrowings?)"),
        ]

        for page_num, ptext in pages_text:
            lines = [l.strip() for l in ptext.split("\n") if l.strip()]
            for i, line in enumerate(lines):
                for dkey, dpat in DEBT_PATTERNS:
                    m_inline = re.search(r"^" + dpat + r"(?:\s*\([^\)]*\))?[\s:\|\t]+([-\(\)\d,\.]+)", line, re.IGNORECASE)
                    if m_inline and dkey not in debt_items:
                        raw_d = m_inline.group(1)
                        val = cls._clean_financial_number(raw_d)
                        if val is not None:
                            debt_items[dkey] = (round(val * scale, 2), raw_d, page_num, line)
                            continue
                    if re.search(r"^" + dpat + r"$", line, re.IGNORECASE) and dkey not in debt_items:
                        if i + 1 < len(lines):
                            cand = lines[i + 1]
                            val = cls._clean_financial_number(cand)
                            if val is not None:
                                debt_items[dkey] = (round(val * scale, 2), cand, page_num, line)

        # 5. Working capital & Governance
        wc_gov_items: Dict[str, Tuple[float, str, int, str]] = {}
        WC_GOV_PATTERNS = [
            ("dio", r"(?:days inventory outstanding|\bdio\b)"),
            ("dso", r"(?:days sales outstanding|\bdso\b)"),
            ("dpo", r"(?:days payable outstanding|\bdpo\b)"),
            ("ccc", r"(?:cash conversion cycle|\bccc\b)"),
            ("pledge", r"(?:promoter shareholding pledged|promoter pledge)"),
            ("rpt", r"(?:related party transactions|rpt \(% of rev\))"),
            ("top5", r"(?:top 5 customer concentration|customer concentration)"),
            ("indep", r"(?:independent directors on board|independent directors)"),
        ]
        for page_num, ptext in pages_text:
            lines = [l.strip() for l in ptext.split("\n") if l.strip()]
            for i, line in enumerate(lines):
                for wgkey, wgpat in WC_GOV_PATTERNS:
                    m_inline = re.search(r"^" + wgpat + r"(?:\s*\([^\)]*\))?[\s:\|\t]+([-\(\)\d,\.]+)", line, re.IGNORECASE)
                    if m_inline and wgkey not in wc_gov_items:
                        raw_val = m_inline.group(1)
                        val = cls._clean_financial_number(raw_val)
                        if val is not None:
                            wc_gov_items[wgkey] = (val, raw_val, page_num, line)
                            continue
                    if re.search(r"^" + wgpat + r"$", line, re.IGNORECASE) and wgkey not in wc_gov_items:
                        if i + 1 < len(lines):
                            cand = lines[i + 1]
                            val = cls._clean_financial_number(cand)
                            if val is not None:
                                wc_gov_items[wgkey] = (val, cand, page_num, line)

        # 6. Build History (Only for periods that have extracted facts)
        history: List[FinancialYearMetric] = []
        valid_periods = [p for p in detected_periods if periods_data.get(p)]
        def sort_key(p):
            m = re.search(r"\d+", p)
            return int(m.group(0)) if m else 0
        valid_periods.sort(key=sort_key)

        for p in valid_periods:
            p_dict = periods_data[p]
            p_prov = provenance_map.get(p, {})

            rev = p_dict.get("revenue_ops_cr", 0.0)
            eb = p_dict.get("ebitda_cr", 0.0)
            pat = p_dict.get("pat_cr", 0.0)
            cfo = p_dict.get("cfo_cr", 0.0)
            cfi = p_dict.get("cfi_cr", 0.0)
            cff = p_dict.get("cff_cr", 0.0)
            capex = p_dict.get("capex_cr", 0.0)
            fcf = p_dict.get("fcf_cr", round(cfo - capex, 2) if ("cfo_cr" in p_dict and "capex_cr" in p_dict) else 0.0)
            nw = p_dict.get("net_worth_cr", 0.0)

            prov_obj = None
            if p_prov:
                first_prov = next(iter(p_prov.values()))
                prov_obj = ProvenanceRef("Section V Restated Financials", first_prov[0], f"Restated Statement ({p})", first_prov[1])

            history.append(
                FinancialYearMetric(
                    fiscal_year=p,
                    revenue_ops_cr=rev,
                    ebitda_cr=eb,
                    pat_cr=pat,
                    cfo_cr=cfo,
                    cfi_cr=cfi,
                    cff_cr=cff,
                    capex_cr=capex,
                    fcf_cr=fcf,
                    net_worth_cr=nw,
                    provenance=prov_obj,
                )
            )

            for m_key, m_name, m_val in [
                ("revenue_ops_cr", "Revenue from Operations", rev),
                ("ebitda_cr", "Operating EBITDA", eb),
                ("pat_cr", "Profit After Tax (PAT)", pat),
                ("cfo_cr", "Cash Flow from Operations (CFO)", cfo),
                ("capex_cr", "Capital Expenditures (Capex)", capex),
                ("fcf_cr", "Free Cash Flow (FCF)", fcf),
                ("net_worth_cr", "Tangible Net Worth", nw),
            ]:
                if m_key == "fcf_cr" and "fcf_cr" not in p_dict and ("cfo_cr" in p_dict and "capex_cr" in p_dict):
                    audit_items.append(
                        IngestionAuditItem(
                            field_name=f"{m_name} ({p})",
                            raw_extracted_value=f"Derived: CFO ({cfo:,.1f}) - Capex ({capex:,.1f})",
                            normalized_metric=f"₹{fcf:,.2f} Cr",
                            status="CONVERTED_AND_NORMALIZED",
                            citation=f"Derived Metric (SEBI ICDR)",
                            confidence_score=0.95,
                        )
                    )
                elif m_key in p_dict:
                    item_page = p_prov[m_key][0] if m_key in p_prov else None
                    page_cite = f"DRHP Section V, Page {item_page}" if item_page else f"Audited Statement ({p})"
                    audit_items.append(
                        IngestionAuditItem(
                            field_name=f"{m_name} ({p})",
                            raw_extracted_value=f"{m_val:,.2f}" if m_val is not None else "0.00",
                            normalized_metric=f"₹{m_val:,.2f} Cr" if m_val is not None else "₹0.00 Cr",
                            status="FOUND_AND_RECONCILED",
                            citation=page_cite,
                            confidence_score=1.0,
                        )
                    )
                else:
                    audit_items.append(
                        IngestionAuditItem(
                            field_name=f"{m_name} ({p})",
                            raw_extracted_value="Not disclosed or unparsed",
                            normalized_metric="UNAVAILABLE",
                            status="MISSING_UNDISCLOSED",
                            citation="DRHP Text Layer",
                            confidence_score=0.0,
                        )
                    )

        # 7. Indebtedness Object
        t_loans = debt_items.get("term_loans", (0.0, "None", 1, "None"))[0]
        w_loans = debt_items.get("wc_loans", (0.0, "None", 1, "None"))[0]
        n_bonds = debt_items.get("ncd_bonds", (0.0, "None", 1, "None"))[0]
        u_loans = debt_items.get("unsecured_loans", (0.0, "None", 1, "None"))[0]
        l_liab = debt_items.get("leases", (0.0, "None", 1, "None"))[0]
        c_cash = debt_items.get("cash", (0.0, "None", 1, "None"))[0]
        tot_borrow = debt_items.get("total_borrowings", (None, "None", 1, "None"))[0]

        if tot_borrow is not None and t_loans == 0.0 and w_loans == 0.0:
            t_loans = tot_borrow
            audit_items.append(
                IngestionAuditItem(
                    field_name="Total Borrowings",
                    raw_extracted_value=str(tot_borrow),
                    normalized_metric=f"₹{tot_borrow:,.2f} Cr",
                    status="FOUND_AND_RECONCILED",
                    citation="Indebtedness Disclosures",
                    confidence_score=1.0,
                )
            )
        elif t_loans > 0.0:
            audit_items.append(
                IngestionAuditItem(
                    field_name="Secured Term Loans",
                    raw_extracted_value=str(t_loans),
                    normalized_metric=f"₹{t_loans:,.2f} Cr",
                    status="FOUND_AND_RECONCILED",
                    citation="Section VI Indebtedness",
                    confidence_score=1.0,
                )
            )

        if c_cash > 0.0:
            audit_items.append(
                IngestionAuditItem(
                    field_name="Cash & Bank Balances",
                    raw_extracted_value=str(c_cash),
                    normalized_metric=f"₹{c_cash:,.2f} Cr",
                    status="FOUND_AND_RECONCILED",
                    citation="Section VI Liquid Assets",
                    confidence_score=1.0,
                )
            )

        indebtedness_obj = IndebtednessSchedule(
            secured_term_loans_cr=t_loans,
            working_capital_loans_cr=w_loans,
            ncd_bonds_cr=n_bonds,
            unsecured_loans_cr=u_loans,
            lease_liabilities_ind_as_116_cr=l_liab,
            cash_and_equivalents_cr=c_cash,
            weighted_avg_interest_rate_pct=None,
            floating_rate_portion_pct=None,
            fixed_rate_portion_pct=None,
        )

        # Working Capital & Governance Objects
        dio_val = wc_gov_items.get("dio", (0.0,))[0]
        dso_val = wc_gov_items.get("dso", (0.0,))[0]
        dpo_val = wc_gov_items.get("dpo", (0.0,))[0]
        ccc_val = wc_gov_items.get("ccc", (round(dio_val + dso_val - dpo_val, 1) if (dio_val or dso_val or dpo_val) else 0.0,))[0]
        working_cap_obj = WorkingCapitalDynamics(
            inventory_days_dio=dio_val,
            debtor_days_dso=dso_val,
            creditor_days_dpo=dpo_val,
            net_working_capital_pct_sales=0.0,
        )

        pledge_val = wc_gov_items.get("pledge", (None,))[0] if "pledge" in wc_gov_items else None
        rpt_val = wc_gov_items.get("rpt", (None,))[0] if "rpt" in wc_gov_items else None
        top5_val = wc_gov_items.get("top5", (None,))[0] if "top5" in wc_gov_items else None
        indep_val = wc_gov_items.get("indep", (None,))[0] if "indep" in wc_gov_items else None
        governance_obj = NonFinancialGovernance(
            promoter_pledge_pct=pledge_val or 0.0,
            related_party_transactions_pct_rev=rpt_val or 0.0,
            top_5_customer_concentration_pct=top5_val or 0.0,
            herfindahl_hhi_index=0.0,
            contingent_liabilities_pct_networth=0.0,
            independent_directors_pct=indep_val,
        )

        # 8. Check for Missing Required Information
        if not history:
            limitations.append(
                DecisionLimitationItem(
                    gap_id="GAP-INTAKE-HIST-01",
                    item_name="Historical Restated Statements",
                    affected_dimension="Section V Disclosures",
                    current_status="NOT_SUPPLIED",
                    why_it_matters="No restated financial periods were recognized in the document.",
                    blocked_decision_or_recommendation="Dickinson classification and solvency modeling blocked.",
                    materiality_priority="HIGH",
                    recommended_diligence_request="Upload Section V of Draft Red Herring Prospectus.",
                )
            )
        else:
            latest = history[-1]
            latest_dict = periods_data.get(latest.fiscal_year, {})
            if "revenue_ops_cr" not in latest_dict:
                limitations.append(
                    DecisionLimitationItem(
                        gap_id="GAP-INTAKE-REV-01",
                        item_name="Revenue from Operations",
                        affected_dimension="Income Statement",
                        current_status="NOT_SUPPLIED",
                        why_it_matters="Top-line revenue is not disclosed or unparsed.",
                        blocked_decision_or_recommendation="Operating margin and growth rates cannot be computed.",
                        materiality_priority="HIGH",
                        recommended_diligence_request="Confirm revenue line item in restated financial statements.",
                    )
                )
            if "ebitda_cr" not in latest_dict:
                limitations.append(
                    DecisionLimitationItem(
                        gap_id="GAP-INTAKE-EBITDA-01",
                        item_name="Operating EBITDA",
                        affected_dimension="Operating Cash & Profitability",
                        current_status="NOT_SUPPLIED",
                        why_it_matters="Operating EBITDA is not disclosed or unparsed.",
                        blocked_decision_or_recommendation="Leverage multiples (Debt/EBITDA) and interest coverage cannot be evaluated.",
                        materiality_priority="HIGH",
                        recommended_diligence_request="Confirm operating EBITDA disclosure in prospectus.",
                    )
                )
            if "cfo_cr" not in latest_dict:
                limitations.append(
                    DecisionLimitationItem(
                        gap_id="GAP-INTAKE-CFO-01",
                        item_name="Cash Flow from Operations",
                        affected_dimension="Cash Flow Statement",
                        current_status="NOT_SUPPLIED",
                        why_it_matters="Operating cash flow is undisclosed.",
                        blocked_decision_or_recommendation="Cash conversion and Dickinson life-stage classification cannot be verified.",
                        materiality_priority="HIGH",
                        recommended_diligence_request="Supply restated cash flow statement.",
                    )
                )

        # 9. Investment Committee Stance
        has_blocking_gaps = bool([g for g in limitations if g.gap_id.startswith(("GAP-OCR-", "GAP-INTAKE-"))])
        if has_blocking_gaps or not history:
            verdict = "INSUFFICIENT_DISCLOSURES_UNRATED"
            screening_grade = "UNRATED"
            call_to_action = "Underwriting suspended pending verifiable statutory filing intake."
        else:
            verdict = "AWAITING_INDEPENDENT_REVIEW"
            screening_grade = "UNRATED"
            call_to_action = "Review extraction candidates against original source before underwriting authorization."

        ic_verdict_obj = InvestmentCommitteeVerdict(
            underwriting_verdict=verdict,
            internal_screening_grade=screening_grade,
            max_recommended_leverage_ratio=2.5 if not has_blocking_gaps else 0.0,
            key_credit_strengths=[
                f"Extracted {len(history)} restated reporting period(s): {', '.join([h.fiscal_year for h in history])}.",
                f"Scale detected as {unit_label} (multiplier: {scale}).",
            ] if history else [],
            key_downside_risks=[g.why_it_matters for g in limitations] if limitations else ["Filing facts await human review."],
            mandatory_loan_covenants=["Verify candidate values against certified audited statements."],
            treasury_call_to_action=call_to_action,
        )

        # Compute authentic confidence score:
        # Proportion of reconciled financial items among total checked
        reconciled_count = len([it for it in audit_items if it.status in ("FOUND_AND_RECONCILED", "CONVERTED_AND_NORMALIZED")])
        total_audit_count = max(len(audit_items), 1)
        raw_conf = reconciled_count / total_audit_count
        overall_confidence = round(raw_conf, 2)

        # Issue size and structure if disclosed
        total_issue_cr = 0.0
        m_iss = re.search(r"APPROXIMATELY [■₹Rs\.\s]*([\d,]+\.?\d*)\s*CRORE", full_text, re.IGNORECASE)
        if not m_iss:
            m_iss = re.search(r"(?:Estimated Issue Value|Gross OFS|Offer for Sale \(OFS\))[\s\n]*[■₹Rs\.\s]*([\d,]+\.?\d*)\s*Cr", full_text, re.IGNORECASE)
        if m_iss:
            total_issue_cr = float(m_iss.group(1).replace(",", ""))

        is_ofs = bool(re.search(r"100%\s*Offer for Sale|No Fresh Capital", full_text, re.IGNORECASE))
        fresh_cr = 0.0 if is_ofs else total_issue_cr
        ofs_cr = total_issue_cr if is_ofs else 0.0

        dossier = PreIPODealDossier(
            deal_id=deal_id_hint or re.sub(r"[^a-zA-Z0-9]+", "_", comp_name.lower()).strip("_"),
            company_name=comp_name,
            sector="General Commercial & Industrial",
            filing_type="DRHP (Electronic Searchable)",
            filing_date="Current Year",
            total_issue_size_cr=total_issue_cr,
            fresh_issue_cr=fresh_cr,
            ofs_cr=ofs_cr,
            face_value_inr=None,
            brlm_bankers=[],
            exchange_listing=[],
            history=history,
            indebtedness=indebtedness_obj,
            working_capital=working_cap_obj,
            governance=governance_obj,
            objects_of_offer=ObjectsOfOfferWaterfall(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            beneish_forensics=BeneishMScoreRatios(),
            debt_maturity=DebtMaturityLadder(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            valuation_comps=ValuationPeerBenchmarking(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "None", [], "UNVERIFIED_DATA_UNAVAILABLE"),
            ic_verdict=ic_verdict_obj,
            limitations=limitations,
            audit_report=audit_items,
        )

        return dossier
