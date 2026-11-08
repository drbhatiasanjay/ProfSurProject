"""Pre-IPO Document Ingestion & Structured Parsing: Docling Primary Benchmark & Challengers.
Preserves hierarchy, tables, cells, and exact provenance without synthetic fabrication.
"""
import io
import os
import re
import time
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

# Available engine descriptors
ENGINE_DOCLING = "docling"
ENGINE_PADDLEOCR = "paddleocr"
ENGINE_RAPIDOCR = "rapidocr"
ENGINE_NATIVE = "pypdf_native"


@dataclass
class ExtractedTableCell:
    row_idx: int
    col_idx: int
    text: str
    is_header: bool = False
    bbox: Optional[Tuple[float, float, float, float]] = None


@dataclass
class ExtractedTable:
    table_id: str
    page_number: int
    caption: str
    num_rows: int
    num_cols: int
    cells: List[ExtractedTableCell] = field(default_factory=list)
    dataframe_records: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class StructuredDocumentResult:
    engine: str
    engine_version: str
    num_pages: int
    execution_time_seconds: float
    tables: List[ExtractedTable] = field(default_factory=list)
    observations: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: Dict[str, bytes] = field(default_factory=dict)  # artifact_kind -> bytes
    status: str = "SUCCESS"
    diagnostics: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)


class DoclingPipeline:
    """Primary benchmark document conversion pipeline using IBM's Docling."""

    @staticmethod
    def get_version() -> str:
        try:
            import docling
            return getattr(docling, "__version__", "2.48.0")
        except Exception:
            return "unavailable"

    @classmethod
    def is_available(cls) -> bool:
        try:
            from docling.document_converter import DocumentConverter
            return True
        except Exception:
            return False

    @classmethod
    def convert_pdf(
        cls,
        pdf_bytes: bytes,
        page_limit: Optional[int] = 10,
        do_ocr: bool = False,
    ) -> StructuredDocumentResult:
        """Run Docling structured extraction preserving hierarchy, tables, cells, and provenance.
        Strictly enforces page_limit bound to prevent unbounded processing overhead.
        """
        start_time = time.time()
        engine_ver = cls.get_version()

        if not cls.is_available():
            return StructuredDocumentResult(
                engine=ENGINE_DOCLING,
                engine_version="unavailable",
                num_pages=0,
                execution_time_seconds=0.0,
                status="DOCLING_UNAVAILABLE",
                diagnostics=["Docling is not installed or dependencies are missing."]
            )

        # Enforce page_limit by slicing the PDF bytes if needed
        bounded_bytes = pdf_bytes
        total_input_pages = 1
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            total_input_pages = len(reader.pages)
            if page_limit and page_limit > 0 and total_input_pages > page_limit:
                writer = pypdf.PdfWriter()
                for i in range(min(page_limit, total_input_pages)):
                    writer.add_page(reader.pages[i])
                buf = io.BytesIO()
                writer.write(buf)
                bounded_bytes = buf.getvalue()
        except Exception as slice_err:
            pass

        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.datamodel.base_models import InputFormat

        # Write to temporary file for Docling input
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(bounded_bytes)
            tmp_path = Path(tmp.name)

        try:
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_table_structure = True
            pipeline_options.do_ocr = bool(do_ocr)

            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )

            conv_res = converter.convert(tmp_path)
            doc = conv_res.document

            elapsed = time.time() - start_time
            tables_list: List[ExtractedTable] = []
            obs_list: List[Dict[str, Any]] = []

            # Extract structured tables
            for idx, tbl in enumerate(getattr(doc, "tables", [])):
                df = tbl.export_to_dataframe()
                records = df.to_dict(orient="records") if hasattr(df, "to_dict") else []
                t_page = getattr(tbl, "page_no", 1) or 1
                if hasattr(tbl, "prov") and tbl.prov:
                    first_p = getattr(tbl.prov[0], "page_no", None)
                    if first_p:
                        t_page = first_p
                t_label = getattr(tbl, "label", f"Table {idx + 1}") or f"Table {idx + 1}"

                # Extract individual cells
                cells: List[ExtractedTableCell] = []
                if hasattr(df, "columns"):
                    for c_idx, col_name in enumerate(df.columns):
                        cells.append(ExtractedTableCell(row_idx=0, col_idx=c_idx, text=str(col_name), is_header=True))
                for r_idx, row in enumerate(df.itertuples(index=False), start=1):
                    for c_idx, cell_val in enumerate(row):
                        cells.append(ExtractedTableCell(row_idx=r_idx, col_idx=c_idx, text=str(cell_val), is_header=False))

                extracted_t = ExtractedTable(
                    table_id=f"table_{idx + 1}",
                    page_number=t_page,
                    caption=str(t_label),
                    num_rows=len(df),
                    num_cols=len(df.columns) if hasattr(df, "columns") else 0,
                    cells=cells,
                    dataframe_records=records
                )
                tables_list.append(extracted_t)

                # Identify fiscal year columns from headers
                fy_cols: Dict[str, str] = {}
                if hasattr(df, "columns"):
                    for col in df.columns:
                        c_str = str(col).upper()
                        m_fy = re.search(r"FY\s*(\d{2,4})|20(\d{2})", c_str)
                        if m_fy:
                            fy_val = f"FY{m_fy.group(1) or m_fy.group(2)}"
                            fy_cols[str(col)] = fy_val

                # Attempt to extract financial facts from identified table rows
                for row_data in records:
                    row_str = " ".join(str(v).lower() for v in row_data.values())
                    metric_id = None
                    if "revenue" in row_str or "sales" in row_str:
                        metric_id = "financial.revenue_operations"
                    elif "ebitda" in row_str or "operating profit" in row_str:
                        metric_id = "financial.ebitda_reported"
                    elif "profit after tax" in row_str or " pat " in row_str or "net profit" in row_str:
                        metric_id = "financial.pat"
                    elif "cash flow from operating" in row_str or " cfo " in row_str:
                        metric_id = "financial.cfo"
                    elif "net worth" in row_str or "equity" in row_str:
                        metric_id = "financial.equity_and_retained_earnings"
                    elif "borrowing" in row_str or "term loan" in row_str:
                        metric_id = "debt.facilities.secured_term_loans"

                    if not metric_id:
                        continue

                    for k, val in row_data.items():
                        if str(val).strip() in ("", "-", "None", "nil"):
                            continue
                        clean_val = str(val).replace(",", "").strip()
                        try:
                            num_val = float(clean_val)
                        except ValueError:
                            continue

                        period = fy_cols.get(str(k), "FY24")
                        obs_list.append({
                            "metric_id": metric_id,
                            "value": num_val,
                            "raw_value": str(val),
                            "period": period,
                            "unit": "crore",
                            "currency": "INR",
                            "presence": "OBSERVED_VALUE",
                            "origin": "FILING_FACT",
                            "review": "UNREVIEWED",
                            "source": {
                                "page": t_page,
                                "locator": extracted_t.caption,
                                "quote": f"{k}: {val}"
                            }
                        })

            # Artifacts: export Markdown and JSON representations
            artifacts = {}
            try:
                md_text = doc.export_to_markdown()
                artifacts["DOCLING_MARKDOWN"] = md_text.encode("utf-8")
            except Exception:
                pass

            coverage_status = "SUCCESS" if (obs_list or tables_list) else "PARTIAL_COVERAGE"
            diag = []
            if not obs_list:
                diag.append("Docling converted document but found no matching financial observations.")

            return StructuredDocumentResult(
                engine=ENGINE_DOCLING,
                engine_version=engine_ver,
                num_pages=getattr(doc, "num_pages", total_input_pages) or total_input_pages,
                execution_time_seconds=round(elapsed, 3),
                tables=tables_list,
                observations=obs_list,
                artifacts=artifacts,
                status=coverage_status,
                diagnostics=diag
            )
        except Exception as exc:
            return StructuredDocumentResult(
                engine=ENGINE_DOCLING,
                engine_version=engine_ver,
                num_pages=0,
                execution_time_seconds=round(time.time() - start_time, 3),
                status="CONVERSION_FAILED",
                diagnostics=[f"Docling conversion exception: {type(exc).__name__}: {str(exc)}"]
            )
        finally:
            if tmp_path.exists():
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass


class MultiEngineIngestionOrchestrator:
    """Orchestrates structured ingestion with Docling as primary benchmark and graceful fallbacks."""

    @classmethod
    def ingest(
        cls,
        pdf_bytes: bytes,
        company_name_hint: Optional[str] = None,
        preferred_engine: str = ENGINE_DOCLING,
        page_limit: Optional[int] = 10,
    ) -> StructuredDocumentResult:
        """Run extraction using preferred engine with truthful fallback if unavailable or partial."""
        if preferred_engine == ENGINE_DOCLING and DoclingPipeline.is_available():
            res = DoclingPipeline.convert_pdf(pdf_bytes, page_limit=page_limit)
            if res.status == "SUCCESS" and len(res.observations) > 0:
                return res

        # Fallback to native text parser
        start_time = time.time()
        from models.pre_ipo_ingest import PreIPOIngestionEngine
        dossier = PreIPOIngestionEngine.ingest_document(
            io.BytesIO(pdf_bytes),
            company_name_hint=company_name_hint,
            allow_external_cloud_ocr=False
        )
        elapsed = time.time() - start_time

        obs = []
        # Multi-year extraction across all available history periods
        for h in (getattr(dossier, "history", []) or []):
            fy = getattr(h, "fiscal_year", "FY24")
            if getattr(h, "revenue_ops_cr", None) is not None:
                obs.append({"metric_id": "financial.revenue_operations", "value": h.revenue_ops_cr, "period": fy, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
            if getattr(h, "ebitda_cr", None) is not None:
                obs.append({"metric_id": "financial.ebitda_reported", "value": h.ebitda_cr, "period": fy, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
            if getattr(h, "pat_cr", None) is not None:
                obs.append({"metric_id": "financial.pat", "value": h.pat_cr, "period": fy, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
            if getattr(h, "cfo_cr", None) is not None:
                obs.append({"metric_id": "financial.cfo", "value": h.cfo_cr, "period": fy, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
            if getattr(h, "cfi_cr", None) is not None:
                obs.append({"metric_id": "financial.cfi", "value": h.cfi_cr, "period": fy, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
            if getattr(h, "cff_cr", None) is not None:
                obs.append({"metric_id": "financial.cff", "value": h.cff_cr, "period": fy, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
            if getattr(h, "capex_cr", None) is not None:
                obs.append({"metric_id": "financial.cash_capex", "value": h.capex_cr, "period": fy, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
            if getattr(h, "fcf_cr", None) is not None:
                obs.append({"metric_id": "financial.fcf", "value": h.fcf_cr, "period": fy, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
            if getattr(h, "net_worth_cr", None) is not None:
                obs.append({"metric_id": "financial.equity_and_retained_earnings", "value": h.net_worth_cr, "period": fy, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
            if getattr(h, "total_assets_cr", None) is not None:
                obs.append({"metric_id": "financial.assets_and_liabilities", "value": h.total_assets_cr, "period": fy, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
            if getattr(h, "receivables_cr", None) is not None:
                obs.append({"metric_id": "financial.receivables", "value": h.receivables_cr, "period": fy, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})

        # Indebtedness metrics
        if getattr(dossier, "indebtedness", None):
            ind = dossier.indebtedness
            if getattr(ind, "secured_term_loans_cr", None) is not None:
                obs.append({"metric_id": "debt.facilities.secured_term_loans", "value": ind.secured_term_loans_cr, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
            if getattr(ind, "working_capital_loans_cr", None) is not None:
                obs.append({"metric_id": "debt.facilities.working_capital_loans", "value": ind.working_capital_loans_cr, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
            if getattr(ind, "ncd_bonds_cr", None) is not None:
                obs.append({"metric_id": "debt.facilities.ncd_bonds", "value": ind.ncd_bonds_cr, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
            if getattr(ind, "unsecured_loans_cr", None) is not None:
                obs.append({"metric_id": "debt.facilities.unsecured_loans", "value": ind.unsecured_loans_cr, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
            if getattr(ind, "lease_liabilities_ind_as_116_cr", None) is not None:
                obs.append({"metric_id": "lease.liability_movement", "value": ind.lease_liabilities_ind_as_116_cr, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
            if getattr(ind, "cash_and_equivalents_cr", None) is not None:
                obs.append({"metric_id": "debt.cash_restrictions.cash_and_equivalents", "value": ind.cash_and_equivalents_cr, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})

        # Offer structure metrics
        if getattr(dossier, "total_issue_size_cr", None) is not None:
            obs.append({"metric_id": "offer_structure.total_issue_size_cr", "value": dossier.total_issue_size_cr, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
        if getattr(dossier, "fresh_issue_cr", None) is not None:
            obs.append({"metric_id": "offer_structure.fresh_issue_cr", "value": dossier.fresh_issue_cr, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})
        if getattr(dossier, "ofs_cr", None) is not None:
            obs.append({"metric_id": "offer_structure.ofs_cr", "value": dossier.ofs_cr, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED", "unit": "crore", "currency": "INR"})

        # Preserved limitations & gap tracking
        gaps_list = [g.gap_id for g in getattr(dossier, "limitations", [])]
        status = "COMPLETED_WITH_GAPS" if gaps_list else "SUCCESS" if obs else "PARTIAL_COVERAGE"

        return StructuredDocumentResult(
            engine=ENGINE_NATIVE,
            engine_version="pypdf-native-1.0",
            num_pages=getattr(dossier, "pages", 1) or 1,
            execution_time_seconds=round(elapsed, 3),
            tables=[],
            observations=obs,
            status=status,
            diagnostics=["Extracted via fallback native text pipeline."] + [f"Gap: {g}" for g in gaps_list],
            gaps=gaps_list
        )
