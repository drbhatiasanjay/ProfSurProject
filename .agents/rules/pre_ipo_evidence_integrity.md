# Pre-IPO Evidence Integrity & Diligence Authority Rules

This policy establishes immutable rules for data authority, automated extraction, human audit sign-off, and financial semantics across all Pre-IPO DRHP intelligence modules.

---

## 1. Hierarchy of Authority

| Level | Classification | Authority Role | Integrity Standard |
| :--- | :--- | :--- | :--- |
| **Level 1** | **Documentary Authority** | Official Filing Bytes | Primary ground-truth. SEBI-filed DRHP PDF bytes accompanied by verified cryptographic SHA-256 hash. |
| **Level 2** | **Application Authority** | Accepted Evidence Snapshot | Authoritative for application processing. Immutable snapshot where observations have been human-audited and transitioned to `ACCEPTED_FOR_ANALYSIS`. |
| **Level 3** | **Extraction Output** | Proposed Candidates | Untrusted machine proposals (`review_state = 'PROPOSED'`). Never authoritative without human review. |
| **Level 4** | **Persistence** | Database Storage | SQLite state cache (`pre_ipo_evidence_snapshots`, `pre_ipo_observations`). Storage medium, not primary documentary truth. |
| **Level 5** | **Legacy Registry** | Unverified Historical Input | `PRE_IPO_REGISTRY` in `models/pre_ipo_data.py`. Legacy sample data only; strictly prohibited as an oracle or production analytical authority. |

---

## 2. Extraction & Audit Lifecycle Invariants

The data lifecycle from raw PDF to downstream financial analysis must strictly follow this one-way progression:

```
PDF Bytes (Verified SHA-256)
      │
      ▼
Page & Layout Extraction
      │
      ▼
Table / Cell Candidate Parsing
      │
      ▼
Normalized Observation Candidates (review_state: PROPOSED)
      │
      ▼
Automated Validation & Consistency Rules
      │
      ▼
Human Auditor Diligence & Sign-Off (review_state: ACCEPTED)
      │
      ▼
Immutable Accepted Evidence Snapshot (status: ACCEPTED_FOR_ANALYSIS)
      │
      ▼
Downstream Financial Analysis, Ratios, DCF, and Board Deck Export
```

### Prohibited Extraction Patterns
1. **No Pseudo-Extraction Oracles:** An extractor must never combine issuer-specific substring matching with hardcoded expected numeric returns (e.g. searching for `"Coca-Cola"` and emitting hardcoded `3450.5 Cr`).
2. **No Auto-Acceptance by Extractors:** Extractors may only emit `review_state = 'PROPOSED'`. Under no circumstances may an automated parser or ingestion pipeline assign `review_state = 'ACCEPTED'`.
3. **No Execution Before Accepted Snapshot:** Downstream ratio calculations, stage classifications, WACC, and reverse DCF models must never execute if an accepted snapshot is absent (`st.stop()`).

---

## 3. Mandatory Provenance & Citation Fields

Every extracted observation candidate must record all fifteen mandatory provenance attributes:

1. `document_hash`: SHA-256 hash of the source PDF.
2. `document_identity`: Canonical filing identifier (e.g. `HCCH_DRHP_2024`).
3. `physical_page`: 1-based integer index in the PDF stream.
4. `printed_page`: Page number printed in the document header/footer (if available).
5. `table_section`: Name or title of the financial statement table or risk section.
6. `row_label`: Exact text label of the reported row.
7. `column_label`: Exact column header (e.g. `FY24 Restated`).
8. `raw_text`: Verbatim text content as extracted from the cell or sentence.
9. `parsed_value`: Extracted numerical or categorical value (typed float, int, or str).
10. `unit`: Reported unit of account (`INR_CRORE`, `INR_LAKH`, `PERCENT`, `SHARES`).
11. `scale`: Multiplicative scale factor (e.g. `10,000,000` for crore).
12. `extraction_method`: Parser method and version (e.g. `pdfplumber_table_v2`).
13. `confidence`: Calibrated confidence score between `0.0` and `1.0`.
14. `review_state`: Lifecycle status (`PROPOSED`, `ACCEPTED`, `REJECTED`, `FLAGGED`).
15. `reviewer_attribution`: User ID, timestamp, and review reason upon human auditor sign-off.

---

## 4. Financial Semantics: Absence vs. Zero

1. **Explicit Semantic Absence:** Undisclosed, unsearched, unpriced, or non-applicable values must be represented semantically as:
   ```json
   {
     "presence": "NOT_DISCLOSED",
     "value": null
   }
   ```
2. **Never Use Zero for Missing Data:** $0.0$, $0$, and $0\%$ are valid numeric quantities. A zero must never be substituted for missing or unestablished financial figures.
3. **No Domain-Plausible Fallbacks:** The UI and engine must never invent plausible benchmarks (such as defaulting debt spread to `"MCLR + 120 bps"`). If undisclosed, format explicitly as:
   `"Not established from reviewed filing evidence"`
4. **No Circular Tests:** Test fixtures must never be asserted against `PRE_IPO_REGISTRY` or other production dictionaries. All golden tests must validate against independently verified official filings.
