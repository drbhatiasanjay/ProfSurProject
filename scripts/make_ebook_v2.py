"""Transform profsur-ebook-v1.html -> profsur-ebook-v2.html"""
import re
import pathlib

SRC = pathlib.Path(r"c:\Users\hemas\Downloads\ProfSurProject\profsur-ebook-v1.html")
DST = pathlib.Path(r"c:\Users\hemas\Downloads\ProfSurProject\profsur-ebook-v2.html")

html = SRC.read_text(encoding="utf-8")

# ─── 1. CSS additions (research-grid, research-card) ──────────────────────────
EXTRA_CSS = (
    ".research-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));"
    "gap:var(--space-6);margin-top:var(--space-8)}"
    ".research-card{background:var(--color-surface);border:1px solid var(--color-border);"
    "border-radius:var(--radius-xl);padding:var(--space-8)}"
    ".research-num{font-size:var(--text-2xl);font-weight:600;color:var(--color-primary);"
    "line-height:1;margin-bottom:var(--space-3)}"
    ".research-name{font-size:var(--text-sm);font-weight:600;letter-spacing:.04em;"
    "color:var(--color-text);margin-bottom:var(--space-3)}"
    ".research-desc{font-size:var(--text-sm);color:var(--color-text-muted);line-height:1.6}"
)
# Insert before the media query
html = html.replace(
    "@media(max-width:640px){.hero h1{font-size:clamp(2rem,8vw,2.75rem)}"
    ".stats-grid{grid-template-columns:repeat(2,1fr)}"
    ".authors-grid,.det-grid,.audience-grid,.dash-pages{grid-template-columns:1fr}"
    ".leverage-table{font-size:.8rem}}",
    EXTRA_CSS
    + "@media(max-width:640px){.hero h1{font-size:clamp(2rem,8vw,2.75rem)}"
    ".stats-grid{grid-template-columns:repeat(2,1fr)}"
    ".authors-grid,.det-grid,.audience-grid,.dash-pages,.research-grid{grid-template-columns:1fr}"
    ".leverage-table{font-size:.8rem}}",
)

# ─── 2. Stats strip: 14 → 15 pages ───────────────────────────────────────────
html = html.replace(
    '<span class="stat-number">14</span><span class="stat-label">Analytical<br>Dashboard Pages</span>',
    '<span class="stat-number">15</span><span class="stat-label">Analytical<br>Dashboard Pages</span>',
)

# ─── 3. Chapter 2: 3 Panels → 4 Panels ───────────────────────────────────────
html = html.replace(
    ">3 Panels</div>"
    '<div style="font-size:var(--text-xs);color:var(--color-text-muted)">'
    "Thesis · CMIE 2025 · Run 3 Stata — each independently reproducible</div></div>",
    ">4 Panels</div>"
    '<div style="font-size:var(--text-xs);color:var(--color-text-muted)">'
    "Thesis · CMIE 2025 · Run 3 Stata · US S&amp;P Sample — four independently reproducible datasets</div></div>",
)

# ─── 4. Chapter 6 lead: 14 → 15 pages, 101 → 219 tests ──────────────────────
html = html.replace(
    "through 14 analytical pages — backed by a production-grade SQLite panel "
    "with vintage management and 101 automated tests.",
    "through 15 analytical pages — backed by a production-grade SQLite panel "
    "with vintage management and 219 automated tests.",
)

# ─── 5. Page 15 Interaction Effects card (after Workbench) ───────────────────
html = html.replace(
    '<div class="dash-page"><span class="dash-num">14</span>'
    "<div class=\"dash-info\"><strong>Workbench</strong>"
    "<span>Open scratchpad for custom queries and ad hoc analysis</span></div></div>",
    '<div class="dash-page"><span class="dash-num">14</span>'
    "<div class=\"dash-info\"><strong>Workbench</strong>"
    "<span>Open scratchpad for custom queries and ad hoc analysis</span></div></div>\n"
    '      <div class="dash-page"><span class="dash-num">15</span>'
    "<div class=\"dash-info\"><strong>Interaction Effects</strong>"
    "<span>Profitability × Tangibility cross-term OLS + stage moderation analysis with delta-method marginal effects</span></div></div>",
)

# ─── 6. US S&P panel card (after Run 3) ──────────────────────────────────────
# Extract the Run 3 card from the html at runtime to avoid encoding issues with
# embedded em-dash/en-dash/middle-dot in Python string literals.
_anchor = """<div class="panel-card"><strong>Run 3"""
_idx_s = html.find(_anchor)
assert _idx_s >= 0, "Run 3 panel card start not found"
_idx_e = html.find("</div>", _idx_s) + len("</div>")
_run3_card = html[_idx_s:_idx_e]
_us_card = (
    "\n      <div class=\"panel-card\"><strong>US S&amp;P Sample</strong>"
    "<span>2006–2025 · Alpha Vantage · 25 DJIA firms<br>"
    "Cross-country comparison using identical Dickinson lifecycle methodology.</span></div>"
)
html = html.replace(_run3_card, _run3_card + _us_card)

# ─── 7. Expand Chapter 5: add 5 audience cards before closing audience-grid ──
NEW_AUDIENCE_CARDS = """\
      <div class="audience-card">
        <div class="audience-title">For PE / VC Investors</div>
        <ul class="audience-list">
          <li><span class="audience-arrow">▶</span><span>Entry timing: Growth-stage firms with positive operating and negative investing cash flows are at the phase where leverage is normal and collateral is building — the optimal entry point for growth capital</span></li>
          <li><span class="audience-arrow">▶</span><span>Exit signals: a portfolio company transitioning from Maturity to Shakeout or Decline is a structural trigger to review covenant headroom before the next liquidity event</span></li>
          <li><span class="audience-arrow">▶</span><span>Debt structuring by stage: Startup and Growth firms need asset-backed facilities; Maturity firms can support cash-flow covenants — one-size covenant packages are structurally suboptimal</span></li>
          <li><span class="audience-arrow">▶</span><span>Use the US S&amp;P panel to benchmark Indian portfolio leverage against global DJIA-component comparables at equivalent lifecycle stages</span></li>
        </ul>
      </div>
      <div class="audience-card">
        <div class="audience-title">For Credit Rating Agencies</div>
        <ul class="audience-list">
          <li><span class="audience-arrow">▶</span><span>Lifecycle stage is a missing variable in most rating methodologies — Decline firms at 38% leverage carry structurally different credit risk than Growth firms at 28%, even at the same headline ratio</span></li>
          <li><span class="audience-arrow">▶</span><span>Stage-adjusted default probability: stratify PD estimates using Dickinson classification and validate against post-IBC NPA data for listed corporates — the lifecycle lens materially improves PD calibration</span></li>
          <li><span class="audience-arrow">▶</span><span>The Profitability × Tangibility interaction is non-linear — high profitability does not reduce credit risk uniformly; the lifecycle stage modulates the relationship (Page 15, Interaction Effects)</span></li>
          <li><span class="audience-arrow">▶</span><span>Tukey HSD pairwise results (Table 5.9) provide statistically validated stage-pair separation — useful for calibrating rating migration boundaries between adjacent lifecycle stages</span></li>
        </ul>
      </div>
      <div class="audience-card">
        <div class="audience-title">For Regulators — SEBI / RBI / IBBI</div>
        <ul class="audience-list">
          <li><span class="audience-arrow">▶</span><span>The IBC structural break (2016) is empirically visible in the leverage panel — the regulation demonstrably changed corporate borrowing behaviour, with effects that differ by lifecycle stage</span></li>
          <li><span class="audience-arrow">▶</span><span>Systemic risk monitoring: a sector-level concentration of Decline-stage firms is an early stress indicator that appears in lifecycle data before it surfaces in earnings reports or market prices</span></li>
          <li><span class="audience-arrow">▶</span><span>Post-COVID recovery was faster than post-GFC — partly attributable to IBC-enforced balance sheet discipline. The panel data quantifies this difference across all eight lifecycle stages</span></li>
          <li><span class="audience-arrow">▶</span><span>Stage-aware disclosure requirements: mandating Dickinson lifecycle classification in regulatory filings would enable systemic monitoring at a granularity that sector-level data cannot provide</span></li>
        </ul>
      </div>
      <div class="audience-card">
        <div class="audience-title">For Investment Bankers</div>
        <ul class="audience-list">
          <li><span class="audience-arrow">▶</span><span>IPO timing: firms transitioning from Growth to Maturity — operating and investing cash flows stabilising — are at the structural inflection point where public-market leverage is most accessible and credibly priced</span></li>
          <li><span class="audience-arrow">▶</span><span>M&amp;A valuation: acquiring a Maturity firm at 17% leverage is a fundamentally different risk proposition than a Decline firm at 38% leverage even at the same EBITDA multiple — stage-adjust your comparable set</span></li>
          <li><span class="audience-arrow">▶</span><span>Debt capital markets: lifecycle stage predicts optimal instrument type — Startup / Growth firms suit asset-backed or convertible structures; Maturity firms support plain-vanilla term loans and NCDs</span></li>
          <li><span class="audience-arrow">▶</span><span>Restructuring: use stage transition probabilities from the Survival Analysis page to model how long a Decline-stage client can sustain current leverage before a covenant breach or rating downgrade</span></li>
        </ul>
      </div>
      <div class="audience-card">
        <div class="audience-title">For Academic Researchers</div>
        <ul class="audience-list">
          <li><span class="audience-arrow">▶</span><span>The full 401-company thesis panel (2001–2024) is reproducible bit-for-bit from the dashboard — a transparent, citable baseline for capital structure studies of Indian listed firms</span></li>
          <li><span class="audience-arrow">▶</span><span>The Interaction Effects page (Page 15) provides a direct foundation for extending interaction modelling to other determinant pairs: Size × Profitability, Tax × Stage, Dividend × Tangibility</span></li>
          <li><span class="audience-arrow">▶</span><span>The US S&amp;P Sample panel (25 DJIA components, 2006–2025) enables preliminary cross-country comparison using identical Dickinson lifecycle classification methodology</span></li>
          <li><span class="audience-arrow">▶</span><span>Eight further research directions are explicitly documented in this report — cross-country extension, SME generalisation, ESG moderators, and ML-based stage prediction each represent tractable PhD-level contributions</span></li>
        </ul>
      </div>"""

# Anchor on the unique text of the last li in Lenders card
LENDERS_TAIL = (
    "          <li><span class=\"audience-arrow\">▶</span>"
    "<span>Asset tangibility remains the most robust positive determinant across all stages — "
    "quality and realisability of collateral is the strongest cross-stage lending signal</span></li>\n"
    "        </ul>\n"
    "      </div>\n"
    "    </div>\n"
    "  </div>\n"
    "</section>"
)
LENDERS_REPLACEMENT = (
    "          <li><span class=\"audience-arrow\">▶</span>"
    "<span>Asset tangibility remains the most robust positive determinant across all stages — "
    "quality and realisability of collateral is the strongest cross-stage lending signal</span></li>\n"
    "        </ul>\n"
    "      </div>\n"
    + NEW_AUDIENCE_CARDS + "\n"
    "    </div>\n"
    "  </div>\n"
    "</section>"
)
assert LENDERS_TAIL in html, "Lenders tail anchor not found — check text"
html = html.replace(LENDERS_TAIL, LENDERS_REPLACEMENT)

# ─── 8. Insert Analytical Innovations + Further Research before CTA dark ──────
ANALYTICAL_INNOVATIONS_CHAPTER = """
<!-- CHAPTER: ANALYTICAL INNOVATIONS -->
<section class="chapter chapter--alt" id="innovations">
  <div class="container--narrow">
    <span class="section-label">Analytical Innovations</span>
    <h2>From data to insight — new tools built into the dashboard</h2>
    <p class="chapter-lead">Four major analytical modules were added to the dashboard, translating thesis results into interactive visualisations that replicate — and extend — the published findings.</p>
    <div class="det-grid">
      <div class="det-card">
        <div class="det-name">Figure 5.1 — Life Stage Profiles</div>
        <div class="det-desc">Leverage, Profitability, Tangibility, and Dividend plotted simultaneously across all 8 life stages. A normalised overlay chart and a 2×2 subplot grid allow cross-variable comparison in a single view. Replicates thesis Figure 5.1 (p. 92).</div>
        <div class="det-theory">Dashboard Page: 01 — Dashboard</div>
      </div>
      <div class="det-card">
        <div class="det-name">Figure 5.2 — Year-wise Trend Analysis</div>
        <div class="det-desc">24-year trends (2001–2025) for all four capital structure determinants with GFC, IBC, and COVID event bands overlaid. Auto-computed start-to-end change in percentage points and peak year per variable. Replicates thesis Figure 5.2 (p. 93).</div>
        <div class="det-theory">Dashboard Page: 01 — Dashboard</div>
      </div>
      <div class="det-card">
        <div class="det-name">Table 5.9 — Pairwise Significance Matrix</div>
        <div class="det-desc">Tukey HSD post-hoc test results displayed as an 8×8 heatmap. Each cell indicates whether leverage differs significantly between that pair of lifecycle stages (red ✓ = significant, p &lt; 0.05). Identifies exactly which stage pairs drive the ANOVA result. Replicates thesis Table 5.9 (p. 107).</div>
        <div class="det-theory">Dashboard Page: 01 — Dashboard</div>
      </div>
      <div class="det-card">
        <div class="det-name">Page 15 — Interaction Effects</div>
        <div class="det-desc">Two-tab analysis: (1) Profitability × Tangibility cross-term OLS with mean-centred variables and HC1 robust standard errors — tests whether the two determinants jointly amplify or dampen leverage; (2) Stage moderation model — 8 lifecycle stages × 2 variables, 28 parameters, delta-method marginal effects, and an annotated significance heatmap.</div>
        <div class="det-theory">Dashboard Page: 15 — Interaction Effects</div>
      </div>
    </div>
  </div>
</section>

<!-- CHAPTER: FURTHER RESEARCH -->
<section class="chapter" id="research">
  <div class="container--narrow">
    <span class="section-label">Further Research Directions</span>
    <h2>Eight open questions the data raises</h2>
    <p class="chapter-lead">The lifecycle–leverage framework opens empirical questions this study was not designed to answer. Each direction below has a clear hypothesis and a tractable methodology within the PhD scope established here.</p>
    <div class="research-grid">
      <div class="research-card">
        <div class="research-num">01</div>
        <div class="research-name">Cross-Country Comparison</div>
        <div class="research-desc">Does Pecking Order dominance persist across other emerging markets — China, Brazil, Indonesia? Or is it India-specific, driven by banking structure, IBC-type insolvency regimes, and promoter ownership patterns? Applying identical Dickinson classification would allow direct coefficient comparison.</div>
      </div>
      <div class="research-card">
        <div class="research-num">02</div>
        <div class="research-name">Dynamic Lifecycle Optimisation</div>
        <div class="research-desc">Build a real-time model that predicts life-stage transitions from quarterly financial signals and prescribes an optimal debt target for the forecast stage — bridging the gap between descriptive empirics and actionable CFO guidance.</div>
      </div>
      <div class="research-card">
        <div class="research-num">03</div>
        <div class="research-name">ESG Factors as Leverage Moderators</div>
        <div class="research-desc">Do high-ESG firms within each lifecycle stage carry structurally different leverage? Does ESG strength mediate the Profitability–Leverage relationship, or are ESG scores and capital structure decisions largely independent paths to investor signalling?</div>
      </div>
      <div class="research-card">
        <div class="research-num">04</div>
        <div class="research-name">SME Extension</div>
        <div class="research-desc">The Dickinson typology was validated on BSE/NSE-listed firms with audited financials. Applying it to unlisted SMEs — using estimated or imputed cash flows from GST and MCA data — could extend the lifecycle lens to a far larger population of Indian corporates.</div>
      </div>
      <div class="research-card">
        <div class="research-num">05</div>
        <div class="research-name">ML-based Life Stage Classification</div>
        <div class="research-desc">Replace the rule-based Dickinson cash-flow sign classifier with a probabilistic sequence model (XGBoost or LSTM trained on multi-year patterns). Does a learned classifier outperform the theoretical typology on out-of-sample leverage prediction?</div>
      </div>
      <div class="research-card">
        <div class="research-num">06</div>
        <div class="research-name">Post-IBC Credit Market Dynamics</div>
        <div class="research-desc">The IBC structural break is visible in the panel. A focused study on how credit access changed differently across lifecycle stages post-2016 — separating the supply-side lender response from the demand-side borrower adjustment — has direct policy implications for IBBI and RBI.</div>
      </div>
      <div class="research-card">
        <div class="research-num">07</div>
        <div class="research-name">Quarterly Panel Analysis</div>
        <div class="research-desc">Annual observations compress within-year dynamics. A quarterly panel would capture short-cycle leverage adjustments — seasonal credit demand, intra-year stage transitions, and the speed of corporate response to policy shocks such as rate changes or regulatory announcements.</div>
      </div>
      <div class="research-card">
        <div class="research-num">08</div>
        <div class="research-name">Sector-Specific Lifecycle Patterns</div>
        <div class="research-desc">The full-sample results mask sector heterogeneity. Running the lifecycle × determinants model separately for Industrials, Financials, IT, and FMCG would test whether the Trade-off vs Pecking Order balance holds uniformly across industries or is itself sector-contingent.</div>
      </div>
    </div>
  </div>
</section>
"""

html = html.replace("\n<!-- CTA DARK -->", ANALYTICAL_INNOVATIONS_CHAPTER + "\n<!-- CTA DARK -->")

# ─── 9. Write V2 ──────────────────────────────────────────────────────────────
DST.write_text(html, encoding="utf-8")
print(f"Written: {DST}")
print(f"Size: {DST.stat().st_size / 1024:.0f} KB")
