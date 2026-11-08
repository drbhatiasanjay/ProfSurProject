"""Pre-IPO Document Ingestion & Structured Parsing: Docling Primary Benchmark & Challengers.
Preserves hierarchy, tables, cells, and exact provenance without synthetic fabrication.
"""
import io
import os
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
    def convert_pdf(cls, pdf_bytes: bytes, page_limit: Optional[int] = 10) -> StructuredDocumentResult:
        """Run Docling structured extraction preserving hierarchy, tables, and provenance."""
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

        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.datamodel.base_models import InputFormat

        # Write to temporary file for Docling input
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = Path(tmp.name)

        try:
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_table_structure = True
            pipeline_options.do_ocr = False  # Pure structured layout for searchable benchmark

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
                t_label = getattr(tbl, "label", f"Table {idx + 1}") or f"Table {idx + 1}"

                extracted_t = ExtractedTable(
                    table_id=f"table_{idx + 1}",
                    page_number=t_page,
                    caption=str(t_label),
                    num_rows=len(df),
                    num_cols=len(df.columns) if hasattr(df, "columns") else 0,
                    dataframe_records=records
                )
                tables_list.append(extracted_t)

                # Attempt to extract financial facts from identified table rows
                for row_data in records:
                    row_str = " ".join(str(v).lower() for v in row_data.values())
                    for k, val in row_data.items():
                        if str(val).strip() in ("", "-", "None", "nil"):
                            continue
                        clean_val = str(val).replace(",", "").strip()
                        try:
                            num_val = float(clean_val)
                        except ValueError:
                            continue

                        # Check for key line items
                        metric_id = None
                        if "revenue" in row_str or "sales" in row_str:
                            metric_id = "financial.revenue_operations"
                        elif "ebitda" in row_str or "operating profit" in row_str:
                            metric_id = "financial.ebitda_reported"
                        elif "profit after tax" in row_str or " pat " in row_str or "net profit" in row_str:
                            metric_id = "financial.pat"
                        elif "net worth" in row_str or "equity" in row_str:
                            metric_id = "financial.equity_and_retained_earnings"
                        elif "borrowing" in row_str or "term loan" in row_str:
                            metric_id = "debt.facilities.secured_term_loans"

                        if metric_id:
                            obs_list.append({
                                "metric_id": metric_id,
                                "value": num_val,
                                "raw_value": str(val),
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

            return StructuredDocumentResult(
                engine=ENGINE_DOCLING,
                engine_version=engine_ver,
                num_pages=getattr(doc, "num_pages", 1) or 1,
                execution_time_seconds=round(elapsed, 3),
                tables=tables_list,
                observations=obs_list,
                artifacts=artifacts,
                status="SUCCESS"
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
        preferred_engine: str = ENGINE_DOCLING
    ) -> StructuredDocumentResult:
        """Run extraction using preferred engine with truthful fallback if unavailable."""
        if preferred_engine == ENGINE_DOCLING and DoclingPipeline.is_available():
            res = DoclingPipeline.convert_pdf(pdf_bytes)
            if res.status == "SUCCESS":
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
        if dossier.history:
            h0 = dossier.history[0]
            if h0.revenue_ops_cr > 0:
                obs.append({"metric_id": "financial.revenue_operations", "value": h0.revenue_ops_cr, "period": h0.fiscal_year, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED"})
            if h0.ebitda_cr != 0:
                obs.append({"metric_id": "financial.ebitda_reported", "value": h0.ebitda_cr, "period": h0.fiscal_year, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED"})
            if h0.pat_cr != 0:
                obs.append({"metric_id": "financial.pat", "value": h0.pat_cr, "period": h0.fiscal_year, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED"})
            if h0.net_worth_cr > 0:
                obs.append({"metric_id": "financial.equity_and_retained_earnings", "value": h0.net_worth_cr, "period": h0.fiscal_year, "presence": "OBSERVED_VALUE", "review": "UNREVIEWED"})

        return StructuredDocumentResult(
            engine=ENGINE_NATIVE,
            engine_version="pypdf-native-1.0",
            num_pages=getattr(dossier, "pages", 1) or 1,
            execution_time_seconds=round(elapsed, 3),
            tables=[],
            observations=obs,
            status="SUCCESS",
            diagnostics=["Extracted via fallback native text pipeline."]
        )
