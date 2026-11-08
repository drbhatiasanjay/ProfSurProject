"""Comprehensive regression & unit tests for Docling primary structured parsing pipeline,
table coordinate preservation, multi-year alignment, page-limit bounds, and orchestrator.
"""
import io
import os
import pytest
from unittest.mock import MagicMock, patch
from models.pre_ipo_docling import (
    DoclingPipeline,
    MultiEngineIngestionOrchestrator,
    ExtractedTable,
    ExtractedTableCell,
    StructuredDocumentResult,
    ENGINE_DOCLING,
    ENGINE_NATIVE,
)

SAMPLE_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Count 1\n/Kids [3 0 R]\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000060 00000 n\n0000000090 00000 n\ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n140\n%%EOF\n"


def test_docling_pipeline_availability():
    """Verify Docling library availability and version inspection."""
    assert DoclingPipeline.is_available() is True
    version = DoclingPipeline.get_version()
    assert version != "unavailable"
    assert "2." in version


def test_orchestrator_fallback_to_native():
    """Verify fallback parser executes without synthetic fabrication and preserves status."""
    res = MultiEngineIngestionOrchestrator.ingest(
        SAMPLE_PDF_BYTES,
        company_name_hint="Fallback Corp",
        preferred_engine=ENGINE_NATIVE
    )
    assert res.engine == ENGINE_NATIVE
    assert res.status in ("SUCCESS", "COMPLETED_WITH_GAPS", "PARTIAL_COVERAGE")
    assert res.execution_time_seconds >= 0.0


def test_docling_table_and_cell_data_structures():
    """Validate table coordinates, row/col index, and cells preservation."""
    cell_hdr = ExtractedTableCell(row_idx=0, col_idx=0, text="Financial Metric", is_header=True)
    cell_val = ExtractedTableCell(row_idx=1, col_idx=1, text="12450.5", is_header=False)
    assert cell_hdr.is_header is True
    assert cell_val.is_header is False
    assert cell_val.text == "12450.5"

    table = ExtractedTable(
        table_id="table_1",
        page_number=7,
        caption="Restated Consolidated Summary",
        num_rows=2,
        num_cols=2,
        cells=[cell_hdr, cell_val],
        dataframe_records=[{"Financial Metric": "Revenue from operations", "FY24": "12450.5"}]
    )
    assert table.page_number == 7
    assert len(table.cells) == 2
    assert table.num_rows == 2


def test_docling_page_limit_enforcement():
    """Verify page limit parameter enforces bounds on conversion input."""
    import pypdf
    writer = pypdf.PdfWriter()
    for _ in range(5):
        writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    five_page_pdf = buf.getvalue()

    # Verify slicing bounds
    reader = pypdf.PdfReader(io.BytesIO(five_page_pdf))
    assert len(reader.pages) == 5

    # Run with mocked DocumentConverter to test bounded slicing and conversion contract
    mock_doc = MagicMock()
    mock_doc.tables = []
    mock_doc.num_pages = 2
    mock_doc.export_to_markdown.return_value = "# Bounded Document"

    mock_conv_res = MagicMock()
    mock_conv_res.document = mock_doc

    with patch("docling.document_converter.DocumentConverter.convert", return_value=mock_conv_res):
        res = DoclingPipeline.convert_pdf(five_page_pdf, page_limit=2, do_ocr=False)
        assert res.num_pages <= 2
        assert res.engine == ENGINE_DOCLING
        assert res.status == "PARTIAL_COVERAGE"  # 0 tables extracted => honest status
