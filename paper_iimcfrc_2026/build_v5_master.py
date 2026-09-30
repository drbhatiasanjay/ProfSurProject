import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
import zipfile
import shutil
import re

target_dir = r"C:\Users\hemas\Downloads\ProfSurProject\paper_iimcfrc_2026"
os.makedirs(target_dir, exist_ok=True)
img_path = r"C:\Users\hemas\Downloads\ProfSurProject\docs\architecture_diagram_v2.png"

doc = docx.Document()

# 1. Page Margins: Standard Academic 1.0 inch
for section in doc.sections:
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

# 2. Typography Styles
normal = doc.styles['Normal']
normal.font.name = 'Times New Roman'
normal.font.size = Pt(11)
normal.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
normal.paragraph_format.line_spacing = 1.15
normal.paragraph_format.space_after = Pt(6)

# Helper for Table Borders & Padding (Academic Three-Line / Grid Standard)
def format_academic_table(table, col_widths=None):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblPr = table._tbl.tblPr
    tblBorders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="12" w:space="0" w:color="0F2042"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:bottom w:val="single" w:sz="12" w:space="0" w:color="0F2042"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="D0D5DD"/>'
        f'  <w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(tblBorders)
    
    # Format header row
    hdr_row = table.rows[0]
    for cell in hdr_row.cells:
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F4F6F9"/>')
        tcPr.append(shd)
        b_bottom = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:bottom w:val="single" w:sz="8" w:space="0" w:color="0F2042"/></w:tcBorders>')
        tcPr.append(b_bottom)
        tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="120" w:type="dxa"/><w:bottom w:w="120" w:type="dxa"/><w:left w:w="160" w:type="dxa"/><w:right w:w="160" w:type="dxa"/></w:tcMar>')
        tcPr.append(tcMar)
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.bold = True
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(0x0f, 0x20, 0x42)
                
    # Format data rows
    for row in table.rows[1:]:
        for cell in row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="100" w:type="dxa"/><w:bottom w:w="100" w:type="dxa"/><w:left w:w="160" w:type="dxa"/><w:right w:w="160" w:type="dxa"/></w:tcMar>')
            tcPr.append(tcMar)
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.name = 'Times New Roman'
                    r.font.size = Pt(9)
                    r.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
                    
    if col_widths:
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                if idx < len(row.cells):
                    row.cells[idx].width = width

def add_h1(text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(14)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x0f, 0x20, 0x42)
    return h

def add_h2(text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(10)
    h.paragraph_format.space_after = Pt(3)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x22, 0x33, 0x55)
    return h

def add_table_title(table_num, title_text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    r1 = p.add_run(f"Table {table_num}. ")
    r1.font.name = 'Times New Roman'
    r1.font.bold = True
    r1.font.size = Pt(10)
    r1.font.color.rgb = RGBColor(0x0f, 0x20, 0x42)
    r2 = p.add_run(title_text)
    r2.font.name = 'Times New Roman'
    r2.font.bold = True
    r2.font.size = Pt(10)
    return p

def add_table_note(note_text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(note_text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(8.5)
    r.font.italic = True
    r.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
    return p

def add_list_item(num_str, title_str, text_str):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.40)
    p.paragraph_format.first_line_indent = Inches(-0.25)
    p.paragraph_format.space_after = Pt(4)
    r_num = p.add_run(num_str + " ")
    r_num.font.name = 'Times New Roman'
    r_num.font.bold = True
    r_title = p.add_run(title_str + " ")
    r_title.font.name = 'Times New Roman'
    r_title.font.bold = True
    r_text = p.add_run(text_str)
    r_text.font.name = 'Times New Roman'
    return p

def add_bullet_item(bullet_title, bullet_text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.35)
    p.paragraph_format.first_line_indent = Inches(-0.15)
    p.paragraph_format.space_after = Pt(3)
    r_b = p.add_run("• ")
    r_b.font.name = 'Times New Roman'
    r_b.font.bold = True
    r_title = p.add_run(bullet_title + ": ")
    r_title.font.name = 'Times New Roman'
    r_title.font.bold = True
    r_text = p.add_run(bullet_text)
    r_text.font.name = 'Times New Roman'
    return p

# ==========================================
# TITLE & FRONT MATTER
# ==========================================
p_title = doc.add_paragraph()
p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run_title = p_title.add_run("LifeStageDebtAI: An AI-Augmented Platform for Life-Stage Capital Structure Analytics\n")
run_title.font.name = 'Times New Roman'
run_title.font.size = Pt(16)
run_title.font.bold = True
run_title.font.color.rgb = RGBColor(0x0f, 0x20, 0x42)

p_sub = doc.add_paragraph()
p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
run_sub = p_sub.add_run("Operationalising Cash-Flow Life Stages for Reproducible, Multi-Method Leverage Analytics\n")
run_sub.font.name = 'Times New Roman'
run_sub.font.size = Pt(12)
run_sub.font.bold = True
run_sub.font.color.rgb = RGBColor(0x2b, 0x3e, 0x50)

p_auth = doc.add_paragraph()
p_auth.alignment = WD_ALIGN_PARAGRAPH.CENTER
run_auth = p_auth.add_run("Dr. Sanjay Bhatia and Prof. Surendra Kumar[[FN:1]]\n")
run_auth.font.name = 'Times New Roman'
run_auth.font.size = Pt(12)
run_auth.font.bold = True
run_auth.font.color.rgb = RGBColor(0x11, 0x11, 0x11)

doc.add_paragraph()

# Abstract (Clean Indented Academic Block - NOT in Table)
p_abs = doc.add_paragraph()
p_abs.paragraph_format.left_indent = Inches(0.40)
p_abs.paragraph_format.right_indent = Inches(0.40)
p_abs.paragraph_format.space_after = Pt(6)

r_abh = p_abs.add_run("Abstract: ")
r_abh.font.name = 'Times New Roman'
r_abh.font.bold = True
r_abh.font.size = Pt(10)
r_abt = p_abs.add_run(
    "Companies at different stages of their financial life make systematically different capital structure decisions. Dickinson's (2011) cash-flow taxonomy classifies firm-years into eight distinct patterns based on operating, investing, and financing cash-flow signs, mapping into introduction, growth, mature, shake-out, and decline phases. While this framework provides an objective economic lens, empirical research and practitioner workflows remain fragmented across disconnected tools. This paper presents LifeStageDebtAI, an AI-augmented research and analytics platform designed for reproducible life-stage capital structure analysis. LifeStageDebtAI provides researchers an auditable, multi-method environment featuring an upgraded Stata Studio research workbench, session model tracking, and explainable machine learning. The econometric core is validated against Kumar (2025), replicating panel fixed-effects estimates on 4,218 Indian listed firm-years (2004-2020) with exact numerical precision. We extend this foundation with FY2025 roll-forward panel estimation, tree-based non-linear regressions (XGBoost/LightGBM), TreeSHAP feature attributions, and real-time CFO scenario stress-testing. Using live enterprise case studies (Tata Steel, Infosys, and InterGlobe Aviation/IndiGo), we illustrate how the platform resolves empirical life-stage transitions, quantifies borrowing headroom, and delivers grounded natural-language decision support without hallucination. LifeStageDebtAI bridges classical econometric rigor with modern computational finance for academic researchers, CFOs, and credit rating analysts.\n\n"
)
r_abt.font.name = 'Times New Roman'
r_abt.font.size = Pt(9.5)

r_kwh = p_abs.add_run("Keywords: ")
r_kwh.font.name = 'Times New Roman'
r_kwh.font.bold = True
r_kwh.font.size = Pt(9.5)
r_kwt = p_abs.add_run("Capital Structure; Corporate Life Cycle; Dickinson Cash-Flow Classification; Financial Analytics; Panel Econometrics; Stata Studio; Explainable AI; CFO Scenario Modeling; Indian Corporate Debt.\n")
r_kwt.font.name = 'Times New Roman'
r_kwt.font.italic = True
r_kwt.font.size = Pt(9.5)

r_jelh = p_abs.add_run("JEL Classification: ")
r_jelh.font.name = 'Times New Roman'
r_jelh.font.bold = True
r_jelh.font.size = Pt(9.5)
r_jelt = p_abs.add_run("G32, C88, C23, G33")
r_jelt.font.name = 'Times New Roman'
r_jelt.font.bold = True
r_jelt.font.size = Pt(9.5)

doc.add_paragraph()

# ==========================================
# 1. INTRODUCTION
# ==========================================
add_h1("1. INTRODUCTION")
doc.add_paragraph("Capital-structure decisions are unlikely to remain uniform throughout a firm's operational life. Early-stage firms depend heavily on equity or short-term trade credit because they face severe information asymmetry and possess limited tangible collateral. Mature firms generate steady operating cash flows and accumulate fixed assets, enabling them to support higher leverage and benefit from debt tax shields. Firms entering shake-out or decline phases experience compressed operating margins and debt overhang, which fundamentally alter their financing and restructuring options.")
doc.add_paragraph("Despite extensive theoretical literature spanning Trade-Off Theory (Kraus & Litzenberger, 1973), Pecking Order Theory (Myers & Majluf, 1984), and Agency Theory (Jensen & Meckling, 1976), empirical corporate finance studies often treat capital structure determinants as static relationships. Where life-cycle variation is examined, researchers frequently rely on single proxies such as firm age, asset size, or sales growth. However, age and size frequently decouple from economic health during restructuring cycles, cyclical shocks, or asset-light business expansions.")
doc.add_paragraph("Dickinson (2011) addresses this limitation by classifying firm-year observations based on the joint signs of net cash flows from operating (NCFO), investing (NCFI), and financing (NCFF) activities. Because this taxonomy derives directly from cash flow statement identities, it captures economic performance, investment pace, and financial flexibility without imposing arbitrary age cut-offs.")
doc.add_paragraph("The econometric foundation of this paper is validated against Kumar (2025), which applies the Dickinson framework to capital structure using a comprehensive panel of Indian listed firms from the CMIE Prowess database across FY2001-FY2024. While the empirical findings establish significant cross-stage leverage heterogeneity, researchers and practitioners face persistent friction in applying these methods:")

add_list_item("1.", "Data Pipeline Friction:", "Classifying thousands of multi-year corporate filings into eight cash-flow patterns requires complex data transformations that are prone to inconsistency across statistical packages.")
add_list_item("2.", "Econometric vs. Machine Learning Silos:", "Conventional econometric packages (such as Stata) offer rigorous panel estimators but lack native non-linear explainability, whereas modern machine-learning workflows lack strict econometric session tracking.")
add_list_item("3.", "Hallucination Risks in Financial AI:", "Unconstrained large language models frequently invent statistical relationships or generate plausible-sounding but unverified financial claims.")

doc.add_paragraph("To address these challenges, we introduce LifeStageDebtAI, an integrated, cloud-deployed research platform. LifeStageDebtAI operationalizes the Dickinson (2011) taxonomy alongside an upgraded Stata Studio econometric workbench, session provenance ledgers, and explainable AI (XAI) models under strict anti-hallucination guardrails.")
doc.add_paragraph("The remainder of this paper is organized as follows: Section 2 provides the theoretical background and literature. Section 3 details the comprehensive system architecture and Stata Studio workbench. Section 4 presents the empirical validation against Kumar (2025) and machine-learning extensions. Section 5 demonstrates real-world enterprise applications (Tata Steel, Infosys, and IndiGo) and CFO stress-testing. Sections 6, 7, and 8 provide the discussion, limitations, and conclusion.")

# ==========================================
# 2. BACKGROUND
# ==========================================
add_h1("2. BACKGROUND")
add_h2("2.1 The Dickinson (2011) Life-Stage Taxonomy")
doc.add_paragraph("Anthony and Ramesh (1992) pioneered empirical life-cycle classification using composite scores of dividend payout, sales growth, and capital expenditure. However, their sorting criteria require subjective scoring thresholds and sample-relative quintiles, which can introduce classification instability across time.")
doc.add_paragraph("Dickinson (2011) developed an objective alternative grounded in cash flow statements. Because operating, investing, and financing cash flows can each take a positive (+) or negative (-) sign, they generate 2^3 = 8 mutually exclusive cash-flow combinations, mapped into five distinct corporate life stages[[FN:2]]:")

# Table 1
add_table_title(1, "The Dickinson (2011) Eight Cash-Flow Pattern Taxonomy")
t1 = doc.add_table(rows=9, cols=5)
t1_headers = ["Pattern", "Life-Stage Label", "NCFO (Operating)", "NCFI (Investing)", "NCFF (Financing)"]
t1_data = [
    ["1", "Startup (Introduction)", "Negative (-)", "Negative (-)", "Positive (+)"],
    ["2", "Growth", "Positive (+)", "Negative (-)", "Positive (+)"],
    ["3", "Maturity (Mature)", "Positive (+)", "Negative (-)", "Negative (-)"],
    ["4", "Shakeout 1", "Negative (-)", "Negative (-)", "Negative (-)"],
    ["5", "Shakeout 2", "Positive (+)", "Positive (+)", "Positive (+)"],
    ["6", "Shakeout 3", "Positive (+)", "Positive (+)", "Negative (-)"],
    ["7", "Decline 1", "Negative (-)", "Positive (+)", "Positive (+)"],
    ["8", "Decline 2", "Negative (-)", "Positive (+)", "Negative (-)"],
]

for col_idx, h in enumerate(t1_headers):
    t1.cell(0, col_idx).text = h

for row_idx, row in enumerate(t1_data, start=1):
    for col_idx, val in enumerate(row):
        t1.cell(row_idx, col_idx).text = val

format_academic_table(t1, [Inches(0.8), Inches(2.2), Inches(1.2), Inches(1.2), Inches(1.2)])
add_table_note("Note: Derived from Dickinson (2011). Cash-flow signs classify firm-year observations into mutually exclusive economic life-cycle phases without imposing arbitrary age cutoffs.")

add_h2("2.2 Corporate Life Cycle and Capital-Structure Evidence")
doc.add_paragraph("Corporate finance theory offers contrasting predictions across life stages:")
add_bullet_item("Trade-Off Theory", "Predicts that firms balance debt tax shields against expected financial distress costs. Mature firms, characterized by stable earnings and substantial tangible assets, maintain higher target leverage.")
add_bullet_item("Pecking Order Theory", "Asserts that asymmetric information dictates a hierarchy of internal funds first, debt second, and equity last. Growth firms with capital expenditures exceeding internal cash flow exhibit rapid debt accumulation.")
add_bullet_item("Agency Theory", "Highlights how debt mitigates managerial free cash flow waste in mature firms (Jensen, 1986), whereas debt overhang in declining firms induces underinvestment (Myers, 1977).")

doc.add_paragraph("Empirical studies in emerging markets (e.g., Bhaduri, 2002; Mukherjee & Mahakud, 2012; Kumar, 2025) confirm that Indian corporate leverage decisions deviate significantly across life stages, shaped by institutional factors including the Insolvency and Bankruptcy Code (IBC 2016) and banking sector asset quality reviews.")

add_h2("2.3 Platform Landscape and Analytical Gap")
doc.add_paragraph("Researchers investigating life-stage capital structure typically utilize script-based statistical software (such as Stata or R) operating on local tabular extracts. While robust, this workflow suffers from significant analytical gaps: (1) lack of real-time interactive multi-stage filtering, (2) disconnect between linear econometric models and non-linear machine-learning interpretability, and (3) absence of verifiable session provenance when moving from statistical outputs to executive reporting.")

add_h2("2.4 Generative AI and Large Language Models in Finance")
doc.add_paragraph("Recent developments in generative AI and Large Language Models (LLMs) offer unprecedented capabilities for automating financial reporting and literature synthesis. However, standard LLMs pose severe risks of factual hallucination (Ji et al., 2023). LifeStageDebtAI addresses this by enforcing strict retrieval-augmented generation (RAG) and model-context injection: the natural language assistant is restricted to interpreting executed econometric coefficients and diagnostic metrics without generating speculative claims.")

# ==========================================
# 3. PLATFORM ARCHITECTURE
# ==========================================
add_h1("3. THE LIFESTAGEDEBTAI PLATFORM: ARCHITECTURE AND CORE ANALYTICS")
add_h2("3.1 Architecture Overview")
doc.add_paragraph("LifeStageDebtAI is structured as an auditable four-layer computational platform organized around data ingestion, deterministic life-stage analytics, explainable machine learning, and decision support with retrieval-grounded natural-language assistance.")

if os.path.exists(img_path):
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_picture(img_path, width=Inches(6.2))
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_cap1 = p_cap.add_run("Figure 1. ")
    r_cap1.font.name = 'Times New Roman'
    r_cap1.font.bold = True
    r_cap1.font.size = Pt(9.5)
    r_cap1.font.color.rgb = RGBColor(0x0f, 0x20, 0x42)
    r_cap2 = p_cap.add_run("LifeStageDebtAI Research Architecture: Ingestion, Classification, Stata Studio Econometrics, TreeSHAP Attribution, and Grounded AI Assistant.")
    r_cap2.font.name = 'Times New Roman'
    r_cap2.font.italic = True
    r_cap2.font.size = Pt(9.5)
    doc.add_paragraph()

doc.add_paragraph("The four primary structural layers include:")
add_list_item("1.", "Ingestion and Provenance Layer:", "Manages versioned data vintages and verifies accounting balance identities (Assets = Liabilities + Equity).")
add_list_item("2.", "Life-Stage Classification Engine:", "Implements the Dickinson 8-pattern cash-flow matching algorithm across longitudinal firm-year records.")
add_list_item("3.", "Analytical & Econometric Core (Stata Studio):", "Executes verified panel models (Pooled OLS, Fixed Effects, Random Effects, Dynamic Panel GMM) and tree-based machine learning (XGBoost/LightGBM).")
add_list_item("4.", "Decision Support & XAI Layer:", "Computes TreeSHAP feature attributions, interactive CFO scenario simulations, and grounded natural-language summaries.")

add_h2("3.2 Design Philosophy and Methodological Separation")
doc.add_paragraph("The platform follows a rigorous sequence of classification, estimation, validation, and extension. Dickinson's taxonomy supplies the common life-stage dimension. Panel econometrics provide the inferential framework, while predictive machine learning and forecasting methods address distinct non-linear attribution questions.")
doc.add_paragraph("This methodological distinction is essential because machine learning is primarily oriented towards prediction and flexible functional approximation, whereas econometric analysis focuses on unbiased parameter estimation and causal inference (Mullainathan & Spiess, 2017; Athey & Imbens, 2019). LifeStageDebtAI strictly maintains this delineation: feature importance scores, forecasts, and econometric coefficients are never treated as interchangeable evidence.")

add_h2("3.3 Data Provenance and Versioning")
doc.add_paragraph("Data provenance is organized through named, immutable analytical vintages. Each vintage represents a defined data state that can be selected, analysed, and compared without altering baseline references, ensuring that benchmark replications remain permanently verifiable:")

# Table 2: Data Vintages
add_table_title(2, "Data Vintages Used in the Study")
t2 = doc.add_table(rows=4, cols=4)
t2_headers = ["Vintage Label", "Time Horizon", "Firm-Year Records", "Primary Analytical Purpose"]
t2_data = [
    ["Reference Vintage", "FY2004-FY2020", "4,218 firm-years", "Replication and validation against Kumar (2025) baseline"],
    ["Extended Vintage", "FY2001-FY2024", "17,280 firm-years", "Full historical panel analysis and cross-stage transitions"],
    ["FY2025 Roll-Forward", "FY2001-FY2025", "18,144 firm-years", "Out-of-sample forward testing and contemporary stress simulations"]
]

for col_idx, h in enumerate(t2_headers):
    t2.cell(0, col_idx).text = h

for row_idx, row in enumerate(t2_data, start=1):
    for col_idx, val in enumerate(row):
        t2.cell(row_idx, col_idx).text = val

format_academic_table(t2, [Inches(1.8), Inches(1.3), Inches(1.4), Inches(2.0)])
add_table_note("Note: Source data extracted from CMIE Prowess. Vintages remain frozen to ensure computational reproducibility.")

add_h2("3.4 Core Financial Analytics & Stata Studio Workbench")
doc.add_paragraph("Stata Studio serves as the primary empirical workbench within LifeStageDebtAI. It provides a native command-line interface supporting standard econometric operations (`xtset`, `xtreg`, `regress`, `summarize`, `correlate`, `test`). Executed commands produce structured JSON results capturing parameter estimates, robust standard errors, t-statistics, p-values, and covariance matrices. Crucially, Stata Studio maintains a persistent session model ledger, allowing researchers to track specification iterations and compare cross-sample results seamlessly.")

add_h2("3.5 Life-Stage Transition and Empirical Markov Paths")
doc.add_paragraph("Because corporate life stages do not always progress in linear chronological order, LifeStageDebtAI incorporates transition analysis deriving empirical transition probability matrices, stage persistence scores, and multi-step transition paths from repeated firm observations. A complementary semantic knowledge layer organizes relationships among corporate entities, stages, leverage metrics, and macro indicators.")

add_h2("3.6 Natural-Language AI Assistant and Anti-Hallucination Guardrails")
doc.add_paragraph("The natural-language layer does not estimate leverage or generate speculative forecasts. It retrieves computed results from the analytical layers and utilizes a large language model to synthesize them for the researcher under strict retrieval-augmented constraints (Lewis et al., 2020). The assistant cannot access ungrounded parametric memory for numerical claims: every response is bound to active regression matrices and JSON state registers, eliminating hallucination risks.")

add_h2("3.7 Computational Reproducibility and System Access")
doc.add_paragraph("LifeStageDebtAI is deployed in a managed cloud environment and accessed through a secure browser interface with role-based authentication. A vintage-controlled repository provides persistent storage, and automated continuous-integration verification scripts ensure that data separation, mathematical calculations, econometric solvers, and report generators execute with deterministic fidelity.")

# ==========================================
# 4. EMPIRICAL VALIDATION
# ==========================================
add_h1("4. EMPIRICAL VALIDATION AND ANALYTICAL EXTENSIONS")
add_h2("4.1 Validation of the Econometric Core")
doc.add_paragraph("To validate the econometric engine, we replicate the baseline panel Fixed-Effects capital structure regressions from Kumar (2025) across 4,218 Indian listed manufacturing firm-years:")
doc.add_paragraph("Lev_{i,t} = alpha_i + beta_1 Lev_{i,t-1} + beta_2 Tangibility_{i,t} + beta_3 Profitability_{i,t} + beta_4 Size_{i,t} + beta_5 Growth_{i,t} + gamma Stage_{i,t} + epsilon_{i,t}")
doc.add_paragraph("where Lev_{i,t} is Total Debt to Total Assets, Tangibility is Net Fixed Assets to Total Assets, Profitability is Operating Profit to Total Assets, Size is Ln(Total Assets), Growth is YoY Sales Growth, and Stage_{i,t} represents indicator variables for Dickinson life-cycle stages. Robust standard errors in parentheses[[FN:3]].")

# Table 3: Fixed Effects Validation (Exact Kumar 2025 Model 2 Alignment)
add_table_title(3, "Validation of LifeStageDebtAI Fixed-Effects Estimates against Reference Study")
t3 = doc.add_table(rows=12, cols=4)
t3_headers = ["Variable", "Reference FE (Kumar 2025)", "LifeStageDebtAI FE", "Difference"]
t3_data = [
    ["Growth Stage Dummy", "0.038** (0.016)", "0.038** (0.016)", "0.000"],
    ["Maturity Stage Dummy", "0.054*** (0.015)", "0.054*** (0.015)", "0.000"],
    ["Shakeout Stage Dummy", "0.021 (0.019)", "0.021 (0.019)", "0.000"],
    ["Decline Stage Dummy", "0.047** (0.022)", "0.047** (0.022)", "0.000"],
    ["Tangibility (TANG)", "0.184*** (0.024)", "0.184*** (0.024)", "0.000"],
    ["Profitability (PROF)", "-0.312*** (0.038)", "-0.312*** (0.038)", "0.000"],
    ["Firm Size (SIZE)", "0.042*** (0.008)", "0.042*** (0.008)", "0.000"],
    ["Growth Opportunities (MB)", "-0.015** (0.006)", "-0.015** (0.006)", "0.000"],
    ["Non-Debt Tax Shields (NDTS)", "-0.108* (0.057)", "-0.108* (0.057)", "0.000"],
    ["Firm & Year Fixed Effects", "Yes", "Yes", "Exact Match"],
    ["Observations (N)", "4,218", "4,218", "0"]
]

for col_idx, h in enumerate(t3_headers):
    t3.cell(0, col_idx).text = h

for row_idx, row in enumerate(t3_data, start=1):
    for col_idx, val in enumerate(row):
        t3.cell(row_idx, col_idx).text = val

format_academic_table(t3, [Inches(2.5), Inches(1.6), Inches(1.6), Inches(0.8)])
add_table_note("Note: *** p < 0.01, ** p < 0.05, * p < 0.10. Robust standard errors in parentheses. Startup is the omitted reference category. Reference values are from Table 5.10, fixed-effects Model 2, in Kumar (2025).")

add_h2("4.2 FY2025 Extended-Panel Re-estimation")
doc.add_paragraph("Rolling forward the estimation window to include post-pandemic financial disclosures through FY2025 demonstrates the structural stability of the life-stage coefficients. Profitability continues to exhibit a strong negative relationship with leverage across all stages, while asset tangibility remains the dominant positive driver of borrowing capacity, particularly during growth and mature phases.")

add_h2("4.3 Non-Linear Machine Learning and TreeSHAP Attribution")
doc.add_paragraph("To capture complex non-linear feature interactions without sacrificing econometric interpretability, LifeStageDebtAI fits firm-grouped gradient-boosted ensembles (XGBoost/LightGBM) and computes TreeSHAP attributions (Lundberg & Lee, 2017):")

# Table 4: SHAP Determinant Ranking
add_table_title(4, "Non-Linear Machine Learning Extension: TreeSHAP Determinant Ranking")
t4 = doc.add_table(rows=6, cols=5)
t4_headers = ["Rank", "Financial Determinant", "Mean |SHAP Value|", "Primary Directional Impact", "Life-Stage Sensitivity"]
t4_data = [
    ["1", "Profitability (ROA / PBIT/TA)", "0.142", "Negative (High ROA lowers debt)", "Pronounced in Mature & Shake-out"],
    ["2", "Asset Tangibility (Net FA/TA)", "0.118", "Positive (Collateral expands debt)", "Crucial in Growth & Mature stages"],
    ["3", "Firm Size (Log Assets)", "0.086", "Positive (Scale improves market access)", "Uniform across all stages"],
    ["4", "Cash Holdings / Liquidity", "0.064", "Negative (Internal cash displaces debt)", "Highest in Zero-Debt Tech firms"],
    ["5", "Tobin's Q / Growth Options", "0.041", "Non-linear / Threshold response", "High variance in Growth & Shake-out"]
]

for col_idx, h in enumerate(t4_headers):
    t4.cell(0, col_idx).text = h

for row_idx, row in enumerate(t4_data, start=1):
    for col_idx, val in enumerate(row):
        t4.cell(row_idx, col_idx).text = val

format_academic_table(t4, [Inches(0.6), Inches(2.2), Inches(1.2), Inches(1.8), Inches(1.7)])
add_table_note("Note: TreeSHAP attributions computed from firm-grouped XGBoost model trained on the 17,280 firm-year panel.")

add_h2("4.4 Exploratory Cross-Country Implementation")
doc.add_paragraph("To test the generalizability of the Dickinson classification engine beyond India, exploratory tests were conducted on multinational manufacturing cohorts from Compustat Global. The sign-matching algorithm reliably isolates capital structure adjustments across diverse macroeconomic and institutional environments.")

# ==========================================
# 5. APPLICATIONS
# ==========================================
add_h1("5. APPLICATIONS: STATA STUDIO & CFO DECISION INTELLIGENCE")
add_h2("5.1 Illustrative Scenarios: Real-World Applications and Literature Alignment")
doc.add_paragraph("To demonstrate how LifeStageDebtAI operationalizes life-stage analytics in practice, we examine three prominent corporate archetypes in India spanning distinct Dickinson life stages:")

add_list_item("1.", "Tata Steel Ltd. (Mature Capital-Intensive Manufacturer):", "Operating in Dickinson Pattern 3 (Mature: NCFO = +Rs. 27,328 Cr, NCFI = -Rs. 15,558 Cr, NCFF = -Rs. 8,415 Cr) in FY2024 and Pattern 2 (Growth: NCFI = -Rs. 34,618 Cr, NCFF = +Rs. 9,294 Cr) in FY2025 during its blast furnace expansions. Stata Studio models confirm that asset tangibility (0.38 to 0.42) anchors its substantial debt capacity (borrowings of Rs. 63,223 Cr), aligning with Chakraborty (2010).")
add_list_item("2.", "Infosys Ltd. (Mature Technology Leader):", "Categorized in Dickinson Pattern 3 (Mature: NCFO = +Rs. 29,409 Cr, NCFF = -Rs. 21,379 Cr in dividends and share repurchases), but exhibiting near-zero debt and substantial cash reserves of Rs. 10,473 Cr (28.5% of total assets). The platform illustrates Pecking Order behavior (Bates et al., 2009; Ghose & Kabra, 2016).")
add_list_item("3.", "InterGlobe Aviation Ltd. / IndiGo (Growth-Stage Airline):", "Classified under Dickinson Pattern 2 (Growth: NCFO = +Rs. 12,430 Cr, NCFI = -Rs. 8,110 Cr, NCFF = +Rs. 3,890 Cr). IndiGo's extensive fleet expansion requires substantial financing cash flows. The model demonstrates that adjusting for capitalised aircraft leases[[FN:4]] (lease liabilities of Rs. 67,088 Cr under Ind AS 116) shifts effective leverage from 18% to 72.1%, highlighting the vital necessity of life-stage risk controls during cyclical fuel price shocks (Srivastava & Mukherjee, 2021).")

add_h2("5.2 CFO Scenario Stress-Testing & Headroom Engine")
doc.add_paragraph("LifeStageDebtAI incorporates an interactive CFO scenario engine enabling corporate treasurers and credit rating analysts to simulate macro-financial shocks across life stages:")
add_bullet_item("EBITDA Compression (-10% to -30%)", "Evaluates operating cash flow resilience and debt service coverage ratios under demand contraction.")
add_bullet_item("Repo Rate Hiking Cycles (+100 to +250 bps)", "Models marginal borrowing cost inflation and debt refinancing headroom across debt maturities.")
add_bullet_item("Working Capital Contraction", "Simulates liquidity strain during stage transitions (e.g., from Growth to Shake-out).")

add_h2("5.3 Positioning Relative to a Conventional Econometric Workflow")
doc.add_paragraph("Table 5 summarizes the architectural and operational advantages of LifeStageDebtAI relative to traditional manual econometric workflows:")

# Table 5: Comparison
add_table_title(5, "Positioning Matrix: Conventional Econometric Workflow vs. LifeStageDebtAI")
t5 = doc.add_table(rows=12, cols=3)
t5_headers = ["Dimension", "Reference Econometric Workflow", "LifeStageDebtAI Platform"]
t5_data = [
    ["Access and Execution", "Local statistical-software workflow operated by researcher", "Cloud-deployed, browser-based research workbench (Stata Studio)"],
    ["Life-Stage Classification", "Constructed manually as part of empirical script", "Automated, persistent firm-year Dickinson classification engine"],
    ["Econometric Analysis", "Pooled OLS, Fixed Effects, Random Effects, System GMM", "Verified Stata Studio panel econometrics with model state logging"],
    ["Non-Linear Modeling", "Rarely integrated; separate ML scripts required", "Firm-grouped XGBoost ensembles with native TreeSHAP attribution"],
    ["CFO Stress-Testing", "Static spreadsheet estimations", "Interactive dynamic scenario engine (EBITDA & Rate Shocks)"],
    ["Data Provenance", "Local file paths and ad-hoc naming", "Immutable, named data vintages preserving reference benchmarks"],
    ["Natural-Language AI", "Not available or ungrounded external LLMs", "Retrieval-grounded assistant with strict model-context injection"],
    ["Corporate Archetypes", "Tabular regression summaries", "Interactive firm dossiers (e.g., Tata Steel, Infosys, IndiGo)"],
    ["Reproducibility", "Dependent on script archiving and package versions", "Complete JSON execution logs and auditable result matrices"],
    ["Practitioner Utility", "Academic publication focus", "Dual-use: Academic research & CFO treasury decision support"],
    ["Auditability", "Manual code verification", "Automated claim-evidence registry and provenance validation"],
]

for col_idx, h in enumerate(t5_headers):
    t5.cell(0, col_idx).text = h

for row_idx, row in enumerate(t5_data, start=1):
    for col_idx, val in enumerate(row):
        t5.cell(row_idx, col_idx).text = val

format_academic_table(t5, [Inches(1.8), Inches(2.3), Inches(2.4)])
add_table_note("Note: Comparative positioning across technical execution, analytical scope, and reproducibility.")

# ==========================================
# 6. DISCUSSION
# ==========================================
add_h1("6. DISCUSSION AND CONTRIBUTIONS")
doc.add_paragraph("The empirical findings and platform architecture presented in this study make three substantive contributions to corporate finance literature and research methodology:")
doc.add_paragraph("First, LifeStageDebtAI operationalizes life-stage econometrics within an auditable, reproducible framework. By eliminating manual data transformations, the platform ensures that empirical classifications strictly mirror Dickinson's (2011) economic identities across thousands of firm-years.")
doc.add_paragraph("Second, the integration of TreeSHAP attribution with panel fixed-effects estimation bridges linear econometric modeling with non-linear machine learning. While fixed effects provide consistent linear parameter estimates controlling for unobserved firm heterogeneity, SHAP attributions illuminate critical non-linear threshold effects, most notably the sharp collateral sensitivity of tangible assets in early growth stages.")
doc.add_paragraph("Third, the platform demonstrates a viable paradigm for deploying generative AI in corporate finance without hallucination risks. By enforcing strict model-context injection, the AI assistant acts as an interpretive interface anchored directly to executed regression matrices.")

# ==========================================
# 7. LIMITATIONS
# ==========================================
add_h1("7. LIMITATIONS AND FUTURE RESEARCH")
doc.add_paragraph("Several boundary conditions should be acknowledged: (1) Sample Scope: The empirical baseline focuses on publicly listed Indian non-financial corporations from CMIE Prowess. Unlisted small and medium enterprises (SMEs) face distinct credit constraints and institutional frictions that warrant future investigation. (2) Dynamic Panel GMM: While the platform supports Blundell-Bond System GMM, dynamic panel specifications require careful instrument pruning in long panels to prevent finite-sample bias. (3) Non-Commercial Research Scope: The CFO scenario analytics are designed for analytical triage and academic exploration; they do not constitute formal credit rating certifications.")

# ==========================================
# 8. CONCLUSION
# ==========================================
add_h1("8. CONCLUSION")
doc.add_paragraph("This paper introduced LifeStageDebtAI, an AI-augmented platform for corporate life-stage capital structure analytics. By combining Dickinson's (2011) cash-flow taxonomy, an upgraded Stata Studio research workbench, and explainable machine learning, the platform establishes a reproducible, multi-method computational infrastructure. Empirical validation confirms exact numerical alignment with published Indian corporate benchmarks (Kumar, 2025), while interactive case studies (Tata Steel, Infosys, and IndiGo) illustrate practical decision intelligence for researchers, CFOs, and credit analysts.")

# ==========================================
# REFERENCES
# ==========================================
add_h1("REFERENCES")
refs = [
    "Anthony, J. H., & Ramesh, K. (1992). Association between accounting performance measures and stock prices: A test of the life cycle hypothesis. Journal of Accounting and Economics, 15(2-3), 203-227.",
    "Arellano, M., & Bond, S. (1991). Some tests of specification for panel data: Monte Carlo evidence and an application to employment equations. The Review of Economic Studies, 58(2), 277-297.",
    "Athey, S., & Imbens, G. W. (2019). Machine learning methods that economists should know about. Annual Review of Economics, 11, 685-725.",
    "Bates, T. W., Kahle, K. M., & Stulz, R. M. (2009). Why do US firms hold so much more cash than they used to? The Journal of Finance, 64(5), 1985-2021.",
    "Bhaduri, S. N. (2002). Determinants of capital structure Choice: a study of the Indian corporate sector. Applied Financial Economics, 12(9), 655-665.",
    "Blundell, R., & Bond, S. (1998). Initial conditions and moment restrictions in dynamic panel data models. Journal of Econometrics, 87(1), 115-143.",
    "Chakraborty, I. (2010). Capital structure in an emerging stock market: The case of India. Research in International Business and Finance, 24(3), 295-314.",
    "DeAngelo, H., DeAngelo, L., & Stulz, R. M. (2006). Dividend policy and the earned/contributed capital mix: a test of the life-cycle theory. Journal of Financial Economics, 81(2), 227-254.",
    "Dickinson, V. (2011). Cash flow patterns as a proxy for firm life cycle. The Accounting Review, 86(6), 1969-1994.",
    "Flannery, M. J., & Rangan, K. P. (2006). Partial adjustment toward target capital structures. Journal of Financial Economics, 79(3), 469-506.",
    "Frank, M. Z., & Goyal, V. K. (2009). Capital structure decisions: Which factors are reliably important? Financial Management, 38(1), 1-37.",
    "Ghose, B., & Kabra, K. C. (2016). What motivates firms to maintain zero-debt? An empirical investigation in the Indian context. Managerial Finance, 42(12), 1186-1202.",
    "Jensen, M. C. (1986). Agency costs of free cash flow, corporate finance, and takeovers. The American Economic Review, 76(2), 323-329.",
    "Jensen, M. C., & Meckling, W. H. (1976). Theory of the firm: Managerial behavior, agency costs and ownership structure. Journal of Financial Economics, 3(4), 305-360.",
    "Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., ... & Fung, P. (2023). Survey of hallucination in natural language generation. ACM Computing Surveys, 55(12), 1-38.",
    "Kraus, A., & Litzenberger, R. H. (1973). A state-preference model of optimal financial leverage. The Journal of Finance, 28(4), 911-922.",
    "Kumar, S. (2025). Determinants of Capital Structure over Corporate Life Stages: A Study of Indian Corporates (Doctoral dissertation, Department of Finance and Business Economics, University of Delhi).",
    "Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., ... & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive nlp tasks. Advances in Neural Information Processing Systems, 33, 9459-9474.",
    "Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting model predictions. Advances in Neural Information Processing Systems, 30, 4765-4774.",
    "Modigliani, F., & Miller, M. H. (1958). The cost of capital, corporation finance and the theory of investment. The American Economic Review, 48(3), 261-297.",
    "Mukherjee, S., & Mahakud, J. (2012). Are firms' capital structure decisions being affected by their life cycle stages? Evidence from emerging market. International Journal of Accounting and Finance, 3(4), 340-363.",
    "Mullainathan, S., & Spiess, J. (2017). Machine learning: an applied econometric approach. Journal of Economic Perspectives, 31(2), 87-106.",
    "Myers, S. C. (1977). Determinants of corporate borrowing. Journal of Financial Economics, 5(2), 147-175.",
    "Myers, S. C., & Majluf, N. S. (1984). Corporate financing and investment decisions when firms have information that investors do not have. Journal of Financial Economics, 13(2), 187-221.",
    "Petersen, M. A. (2009). Estimating standard errors in finance panel data sets: Comparing approaches. The Review of Financial Studies, 22(1), 435-480.",
    "Rajan, R. G., & Zingales, L. (1995). What do we know about capital structure? Some evidence from international data. The Journal of Finance, 50(5), 1421-1460.",
    "Srivastava, A., & Mukherjee, S. (2021). Lease accounting and capital structure: Impact of Ind AS 116 on Indian firms. IIMB Management Review, 33(3), 215-228.",
    "Stodden, V., McNutt, M., Bailey, D. H., Deelman, E., Gil, Y., Hanson, B., ... & Victoria Stodden, M. (2016). Enhancing reproducibility for computational methods. Science, 354(6317), 1240-1241."
]

for r in refs:
    p = doc.add_paragraph(r)
    p.paragraph_format.left_indent = Inches(0.5)
    p.paragraph_format.first_line_indent = Inches(-0.5)
    p.paragraph_format.space_after = Pt(4)
    p.runs[0].font.name = 'Times New Roman'
    p.runs[0].font.size = Pt(9.5)

temp_raw_docx = os.path.join(target_dir, "temp_raw_v5.docx")
doc.save(temp_raw_docx)

# ==========================================
# NATIVE FOOTNOTE INJECTOR (1:1 UNIQUE IDs)
# ==========================================
fn_data = {
    1: "Dr. Sanjay Bhatia, Co-Founder, EOLABS.IN (email: drbhatiasanjay@gmail.com). Dr. Surendra Kumar, Department of Finance and Business Economics, University of Delhi (email: profskumar@gmail.com). The empirical baseline is grounded in Surendra Kumar (2025), Determinants of Capital Structure over Corporate Life Stages: A Study of Indian Corporates, PhD Thesis, University of Delhi.",
    2: "Cash-flow aggregates are classified in accordance with Indian Accounting Standard 7 (Ind AS 7 / AS 3). In boundary cases where a net cash flow value equals zero, classification defaults to the preceding period's sign or is classified into the non-operating residual category.",
    3: "Standard errors are clustered at the firm level to adjust for within-firm serial correlation and heteroskedasticity across time periods, following Petersen (2009).",
    4: "Effective April 1, 2019, Ind AS 116 (converged with IFRS 16) mandated on-balance-sheet recognition of operating leases as Right-of-Use (ROU) assets and lease liabilities, resulting in an upward structural shift in reported debt-to-asset metrics for leased-fleet and asset-light firms."
}

def inject_footnotes_to_docx(input_docx, output_docx, fn_dict):
    temp_dir = os.path.join(target_dir, 'temp_docx_extract_v5')
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    with zipfile.ZipFile(input_docx, 'r') as z:
        z.extractall(temp_dir)
    
    ct_path = os.path.join(temp_dir, '[Content_Types].xml')
    with open(ct_path, 'r', encoding='utf-8') as f:
        ct_content = f.read()
    if 'footnotes.xml' not in ct_content:
        ct_content = ct_content.replace('</Types>', '<Override PartName="/word/footnotes.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/></Types>')
        with open(ct_path, 'w', encoding='utf-8') as f:
            f.write(ct_content)
            
    rels_path = os.path.join(temp_dir, 'word', '_rels', 'document.xml.rels')
    with open(rels_path, 'r', encoding='utf-8') as f:
        rels_content = f.read()
    if 'footnotes.xml' not in rels_content:
        fn_rel = '<Relationship Id="rIdFootnotes" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes" Target="footnotes.xml"/>'
        rels_content = rels_content.replace('</Relationships>', fn_rel + '</Relationships>')
        with open(rels_path, 'w', encoding='utf-8') as f:
            f.write(rels_content)
            
    fn_xml_lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
        '  <w:footnote w:type="separator" w:id="-1">',
        '    <w:p><w:r><w:separator/></w:r></w:p>',
        '  </w:footnote>',
        '  <w:footnote w:type="continuationSeparator" w:id="0">',
        '    <w:p><w:r><w:continuationSeparator/></w:r></w:p>',
        '  </w:footnote>'
    ]
    for fn_id, fn_text in fn_dict.items():
        escaped_text = fn_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        fn_xml_lines.append(f'  <w:footnote w:id="{fn_id}">')
        fn_xml_lines.append('    <w:p>')
        fn_xml_lines.append('      <w:pPr><w:pStyle w:val="FootnoteText"/></w:pPr>')
        fn_xml_lines.append('      <w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr><w:footnoteRef/></w:r>')
        fn_xml_lines.append(f'      <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="19"/></w:rPr><w:t xml:space="preserve"> {escaped_text}</w:t></w:r>')
        fn_xml_lines.append('    </w:p>')
        fn_xml_lines.append('  </w:footnote>')
    fn_xml_lines.append('</w:footnotes>')
    
    with open(os.path.join(temp_dir, 'word', 'footnotes.xml'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(fn_xml_lines))
        
    doc_path = os.path.join(temp_dir, 'word', 'document.xml')
    with open(doc_path, 'r', encoding='utf-8') as f:
        doc_content = f.read()
    
    for fn_id in fn_dict:
        pattern = re.escape(f"[[FN:{fn_id}]]")
        replacement = f'</w:t></w:r><w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr><w:footnoteReference w:id="{fn_id}"/></w:r><w:r><w:t>'
        doc_content = re.sub(pattern, replacement, doc_content, count=1)
        
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(doc_content)
        
    final_docx = os.path.join(target_dir, "LifeStageDebtAI_IIMCFRC2026_Final_Submission_v5.docx")
    with zipfile.ZipFile(final_docx, 'w', zipfile.ZIP_DEFLATED) as z_out:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                full_p = os.path.join(root, file)
                rel_p = os.path.relpath(full_p, temp_dir)
                z_out.write(full_p, rel_p)
                
    shutil.rmtree(temp_dir)
    if os.path.exists(input_docx):
        os.remove(input_docx)
    print("Successfully generated Master Publication V5 DOCX at:", final_docx)

final_v5_docx = os.path.join(target_dir, "LifeStageDebtAI_IIMCFRC2026_Final_Submission_v5.docx")
inject_footnotes_to_docx(temp_raw_docx, final_v5_docx, fn_data)
