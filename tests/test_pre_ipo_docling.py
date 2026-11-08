"""Unit tests for Docling primary structured parsing pipeline and multi-engine orchestrator.
"""
import os
import pytest
from models.pre_ipo_docling import (
    DoclingPipeline,
    MultiEngineIngestionOrchestrator,
    ENGINE_DOCLING,
    ENGINE_NATIVE,
)

SAMPLE_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Count 1\n/Kids [3 0 R]\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000060 00000 n\n0000000090 00000 n\ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n140\n%%EOF\n"


def test_docling_pipeline_availability():
    # Docling was installed and verified in this environment
    assert DoclingPipeline.is_available() is True
    version = DoclingPipeline.get_version()
    assert version != "unavailable"
    assert "2." in version


def test_orchestrator_fallback_to_native():
    res = MultiEngineIngestionOrchestrator.ingest(
        SAMPLE_PDF_BYTES,
        company_name_hint="Fallback Corp",
        preferred_engine=ENGINE_NATIVE
    )
    assert res.engine == ENGINE_NATIVE
    assert res.status == "SUCCESS"
    assert res.execution_time_seconds >= 0.0
