#!/usr/bin/env python3
"""
Generate profsur-ebook-v3.html — Practitioner's Guide to the LifeCycle Leverage Dashboard.
All figures sourced from CMIE Prowess thesis panel (2001-2024, 8,677 obs, 401 firms).
Run from project root: py -3.12 scripts/make_ebook_v3.py
"""
import sys, os

def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().strip()

try:
    AUTHOR = load('_author_photo_b64.txt')
    DASH = load('_dashboard_b64.txt')
    BENCH = load('_benchmarks_b64.txt')
    SCEN = load('_scenarios_b64.txt')
    ECON = load('_econometrics_b64.txt')
except FileNotFoundError as e:
    print(f"ERROR: {e}\nRun from project root and ensure _*b64*.txt temp files exist.", file=sys.stderr)
    sys.exit(1)

# SVG logo mark — EOLABS brand colours (#01696f primary, white text)
LOGO_SVG = (
    '<svg width="38" height="38" viewBox="0 0 38 38" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="38" height="38" rx="7" fill="#01696f"/>'
    '<text x="19" y="14" text-anchor="middle" fill="#7dd6d8" '
    'font-family="Arial,sans-serif" font-weight="900" font-size="7" letter-spacing="1.5">EOL</text>'
    '<line x1="7" y1="18" x2="31" y2="18" stroke="#7dd6d8" stroke-width="0.8" opacity="0.7"/>'
    '<text x="19" y="28" text-anchor="middle" fill="white" '
    'font-family="Arial,sans-serif" font-weight="900" font-size="10" letter-spacing="1">ABS</text>'
    '</svg>'
)

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>LifeCycle Leverage — Practitioner's Guide | EOLABS</title>
<style>
:root{{
  --brand:#01696f;--brand-d:#024b4f;--brand-lt:#2d9fa6;--brand-pale:#e8f5f6;
  --ink:#111827;--ink2:#374151;--ink3:#6B7280;--border:#E5E7EB;
  --radius:12px;--space:1rem;
  --ff-serif:'Instrument Serif',Georgia,serif;
  --ff-sans:'General Sans',Inter,system-ui,sans-serif;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth;font-size:16px}}
body{{font-family:var(--ff-sans);color:var(--ink);background:#fff;line-height:1.7}}
a{{color:var(--brand);text-decoration:none}}
a:hover{{text-decoration:underline}}

/* ── NAV ── */
nav{{position:sticky;top:0;z-index:100;background:#fff;border-bottom:1px solid var(--border);
     padding:.75rem 2rem;display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap}}
.nav-brand{{display:flex;align-items:center;gap:.6rem;font-weight:700;font-size:1.05rem;color:var(--brand-d)}}
.nav-brand svg{{flex-shrink:0}}
.nav-links{{display:flex;gap:1.25rem;flex-wrap:wrap;margin-left:auto}}
.nav-links a{{color:var(--ink2);font-size:.875rem;font-weight:500}}
.nav-links a:hover{{color:var(--brand)}}
.btn-nav{{background:var(--brand);color:#fff!important;padding:.35rem .9rem;border-radius:6px;
          font-size:.85rem!important;font-weight:600!important}}

/* ── HERO ── */
.hero{{background:linear-gradient(135deg,var(--brand-d) 0%,var(--brand) 55%,#0a8d96 100%);
       color:#fff;padding:5rem 2rem 4rem;text-align:center}}
.hero-tag{{display:inline-block;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);
           border-radius:20px;padding:.3rem 1rem;font-size:.8rem;letter-spacing:.05em;
           text-transform:uppercase;margin-bottom:1.5rem}}
.hero h1{{font-family:var(--ff-serif);font-size:clamp(2rem,5vw,3.25rem);line-height:1.2;
           margin-bottom:1rem;font-weight:400}}
.hero h1 em{{font-style:italic;color:#a8dfe2}}
.hero-sub{{font-size:1.05rem;opacity:.9;max-width:620px;margin:0 auto 2rem}}
.hero-cta{{display:inline-block;background:#fff;color:var(--brand-d);
           font-weight:700;padding:.75rem 2rem;border-radius:8px;font-size:1rem}}
.hero-cta:hover{{background:#e8f5f6;text-decoration:none}}

/* ── STATS STRIP ── */
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
        gap:1px;background:var(--border);border-top:1px solid var(--border);border-bottom:1px solid var(--border)}}
.stat-cell{{background:#fff;padding:1.25rem;text-align:center}}
.stat-num{{font-size:1.75rem;font-weight:700;color:var(--brand);line-height:1}}
.stat-lbl{{font-size:.78rem;color:var(--ink3);margin-top:.25rem}}

/* ── SECTION ── */
.section{{padding:4rem 2rem;max-width:1100px;margin:0 auto}}
.section-tag{{font-size:.75rem;text-transform:uppercase;letter-spacing:.1em;
              color:var(--brand);font-weight:600;margin-bottom:.5rem}}
.section h2{{font-family:var(--ff-serif);font-size:clamp(1.5rem,3vw,2.1rem);font-weight:400;
              margin-bottom:.5rem;color:var(--ink)}}
.section-intro{{color:var(--ink2);max-width:680px;margin-bottom:2.5rem;font-size:.95rem}}
.divider{{border:none;border-top:1px solid var(--border);margin:3.5rem 0}}

/* ── CATALOGUE GRID ── */
.cat-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:1.25rem}}
.cat-card{{border:1px solid var(--border);border-radius:var(--radius);padding:1.25rem;
           transition:box-shadow .2s,border-color .2s}}
.cat-card:hover{{border-color:var(--brand-lt);box-shadow:0 4px 16px rgba(1,105,111,.1)}}
.cat-num{{font-size:.7rem;color:var(--brand);font-weight:700;letter-spacing:.08em;
           text-transform:uppercase;margin-bottom:.4rem}}
.cat-card h4{{font-size:.95rem;font-weight:600;color:var(--ink);margin-bottom:.35rem}}
.cat-card p{{font-size:.82rem;color:var(--ink3);line-height:1.5}}

/* ── STAKEHOLDER CARDS ── */
.sh-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:2rem;margin-top:2rem}}
.sh-card{{border:1px solid var(--border);border-radius:var(--radius);overflow:hidden}}
.sh-header{{padding:1rem 1.25rem;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:.75rem}}
.sh-icon{{width:38px;height:38px;border-radius:8px;display:flex;align-items:center;justify-content:center;
           font-size:1.1rem;flex-shrink:0}}
.sh-role{{font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink3)}}
.sh-header h3{{font-size:1rem;font-weight:600;color:var(--ink);margin-top:.1rem}}
.sh-body{{padding:1.25rem}}
.sh-company{{font-size:.78rem;font-weight:700;color:var(--brand);text-transform:uppercase;
              letter-spacing:.06em;margin-bottom:.5rem}}
.sh-body p{{font-size:.875rem;color:var(--ink2);margin-bottom:.75rem;line-height:1.6}}
.data-row{{display:flex;justify-content:space-between;align-items:center;
            padding:.4rem 0;border-bottom:1px solid var(--border)}}
.data-row:last-child{{border-bottom:none}}
.data-label{{font-size:.78rem;color:var(--ink3)}}
.data-val{{font-size:.88rem;font-weight:600;color:var(--ink)}}
.data-val.green{{color:#16a34a}}
.data-val.amber{{color:#d97706}}
.data-val.red{{color:#dc2626}}
.citation{{font-size:.72rem;color:var(--ink3);margin-top:.75rem;font-style:italic;line-height:1.4}}
.scenario-tag{{display:inline-block;background:#fef3c7;border:1px solid #f59e0b;
                color:#92400e;border-radius:4px;font-size:.68rem;font-weight:700;
                padding:.15rem .45rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.6rem}}

/* ── SCREENSHOT BLOCK ── */
.screenshot-wrap{{margin:2.5rem 0;border-radius:var(--radius);overflow:hidden;
                  border:1px solid var(--border);box-shadow:0 4px 24px rgba(0,0,0,.08)}}
.screenshot-caption{{background:var(--brand-pale);padding:.6rem 1rem;font-size:.8rem;
                      color:var(--ink2);border-top:1px solid var(--border)}}
.screenshot-wrap img{{width:100%;display:block}}

/* ── THEORY BOX ── */
.theory-grid{{display:grid;grid-template-columns:1fr 1fr;gap:1.25rem;margin:2rem 0}}
@media(max-width:600px){{.theory-grid{{grid-template-columns:1fr}}}}
.theory-box{{padding:1.25rem;border-radius:var(--radius);}}
.theory-box.pecking{{background:#f0fdf4;border:1px solid #bbf7d0}}
.theory-box.tradeoff{{background:#eff6ff;border:1px solid #bfdbfe}}
.theory-box h4{{font-size:.9rem;font-weight:700;margin-bottom:.4rem}}
.theory-box .coef{{font-size:1.5rem;font-weight:700;margin:.3rem 0}}
.theory-box p{{font-size:.82rem;color:var(--ink2)}}

/* ── IBC RISK BAR ── */
.ibc-bar{{display:flex;border-radius:8px;overflow:hidden;height:28px;margin:1rem 0}}
.ibc-green{{background:#16a34a;flex:85;display:flex;align-items:center;justify-content:center;
             color:#fff;font-size:.8rem;font-weight:600}}
.ibc-red{{background:#dc2626;flex:15;display:flex;align-items:center;justify-content:center;
           color:#fff;font-size:.8rem;font-weight:600}}

/* ── STAGE BADGE ── */
.stage-badge{{display:inline-block;padding:.2rem .65rem;border-radius:20px;font-size:.72rem;
              font-weight:700;letter-spacing:.04em;text-transform:uppercase}}
.badge-maturity{{background:#d1fae5;color:#065f46}}
.badge-growth{{background:#dbeafe;color:#1e40af}}
.badge-shakeout{{background:#fef3c7;color:#92400e}}
.badge-startup{{background:#ede9fe;color:#4c1d95}}
.badge-decline{{background:#fee2e2;color:#991b1b}}
.badge-decay{{background:#f3f4f6;color:#374151}}

/* ── STAGE DISTRIBUTION BAR ── */
.stage-dist{{margin:1rem 0}}
.stage-dist-bar{{height:12px;border-radius:6px;background:var(--border);overflow:hidden;display:flex;margin:.3rem 0}}
.sd-fill{{height:100%}}
.sd-label{{font-size:.75rem;color:var(--ink3);display:flex;justify-content:space-between}}

/* ── REFERENCES ── */
.refs{{background:#f9fafb;border-radius:var(--radius);padding:2rem;margin-top:2rem}}
.refs h3{{font-size:1rem;font-weight:700;margin-bottom:1rem;color:var(--ink)}}
.ref-item{{font-size:.82rem;color:var(--ink2);margin-bottom:.6rem;padding-left:1.5rem;
            text-indent:-1.5rem;line-height:1.6}}

/* ── AUTHORS ── */
.authors{{display:flex;gap:1.5rem;align-items:flex-start;flex-wrap:wrap;
           margin:2rem 0;padding:2rem;background:var(--brand-pale);border-radius:var(--radius)}}
.author-photo{{width:80px;height:80px;border-radius:50%;object-fit:cover;border:3px solid var(--brand)}}
.author-info h4{{font-weight:700;margin-bottom:.2rem}}
.author-info p{{font-size:.85rem;color:var(--ink2)}}

/* ── CTA ── */
.cta-band{{background:linear-gradient(135deg,var(--brand-d),var(--brand));color:#fff;
            padding:3.5rem 2rem;text-align:center}}
.cta-band h2{{font-family:var(--ff-serif);font-size:1.8rem;font-weight:400;margin-bottom:.75rem}}
.cta-band p{{opacity:.9;max-width:520px;margin:0 auto 1.5rem;font-size:.95rem}}
.btn-cta{{background:#fff;color:var(--brand-d);font-weight:700;
           padding:.75rem 2rem;border-radius:8px;display:inline-block}}

/* ── FOOTER ── */
footer{{border-top:1px solid var(--border);padding:1.5rem 2rem;
        display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;
        font-size:.8rem;color:var(--ink3)}}
</style>
</head>
<body>

<!-- NAV -->
<nav>
  <a href="#top" class="nav-brand">
    {LOGO_SVG}
    <span>EOLABS</span>
  </a>
  <div class="nav-links">
    <a href="#catalogue">Analyses</a>
    <a href="#stakeholders">By Role</a>
    <a href="#theory">Theory</a>
    <a href="#risk">Risk</a>
    <a href="#references">References</a>
    <a href="#contact" class="btn-nav">Get Access</a>
  </div>
</nav>

<!-- HERO -->
<section class="hero" id="top">
  <div class="hero-tag">Practitioner's Guide · LifeCycle Leverage Dashboard</div>
  <h1>Capital at <em>Every Table</em></h1>
  <p class="hero-sub">How eight corporate functions — from the boardroom to the deal desk —
     extract live capital-structure intelligence from 401 listed Indian companies
     across eight Dickinson (2011) life stages, 2001–2024.</p>
  <a href="#stakeholders" class="hero-cta">Jump to My Role →</a>
</section>

<!-- STATS STRIP -->
<div class="stats">
  <div class="stat-cell">
    <div class="stat-num">401</div>
    <div class="stat-lbl">Listed Indian firms</div>
  </div>
  <div class="stat-cell">
    <div class="stat-num">8,677</div>
    <div class="stat-lbl">Firm-year observations</div>
  </div>
  <div class="stat-cell">
    <div class="stat-num">24</div>
    <div class="stat-lbl">Years (2001–2024)</div>
  </div>
  <div class="stat-cell">
    <div class="stat-num">8</div>
    <div class="stat-lbl">Life stages (Dickinson 2011)</div>
  </div>
  <div class="stat-cell">
    <div class="stat-num">13</div>
    <div class="stat-lbl">Analytical modules</div>
  </div>
  <div class="stat-cell">
    <div class="stat-num">17</div>
    <div class="stat-lbl">Dashboard pages</div>
  </div>
</div>

<!-- CATALOGUE -->
<section class="section" id="catalogue">
  <div class="section-tag">What the dashboard covers</div>
  <h2>Thirteen Analytical Modules</h2>
  <p class="section-intro">Each module answers a distinct capital-structure question.
     All results use the thesis panel (vintage = <em>thesis</em>, 2001–2024)
     for reproducibility, consistent with Kumar (2025).</p>

  <div class="cat-grid">
    <div class="cat-card">
      <div class="cat-num">01</div>
      <h4>Stage KPI Dashboard</h4>
      <p>Real-time leverage, profitability and tangibility medians by Dickinson life stage.
         Trend ribbons from 2001 to latest year.</p>
    </div>
    <div class="cat-card">
      <div class="cat-num">02</div>
      <h4>Peer Benchmarking</h4>
      <p>Company-vs-stage and company-vs-industry percentile rankings.
         Tracks how a firm's leverage stacks up against its life-stage cohort.</p>
    </div>
    <div class="cat-card">
      <div class="cat-num">03</div>
      <h4>Scenario OLS</h4>
      <p>What-if leverage forecasts using calibrated OLS coefficients —
         models the impact of changing profitability, tangibility, tax rate or firm size.</p>
    </div>
    <div class="cat-card">
      <div class="cat-num">04</div>
      <h4>Bulk Data Import</h4>
      <p>Upload a company CSV to classify into Dickinson stages and
         benchmark against the panel instantly.</p>
    </div>
    <div class="cat-card">
      <div class="cat-num">05</div>
      <h4>Raw Panel Explorer</h4>
      <p>Full vintage-tagged financial table: filter by company, year, stage or data vintage.</p>
    </div>
    <div class="cat-card">
      <div class="cat-num">06</div>
      <h4>Settings &amp; Appearance</h4>
      <p>Light / dark theme, panel selector (Thesis vs Latest), CMIE API sync controls.</p>
    </div>
    <div class="cat-card">
      <div class="cat-num">07</div>
      <h4>Knowledge Graph</h4>
      <p>Interactive network of capital-structure determinants and their empirically
         confirmed directions from the thesis panel.</p>
    </div>
    <div class="cat-card">
      <div class="cat-num">08</div>
      <h4>Econometrics Lab</h4>
      <p>OLS, Fixed Effects, Random Effects, Hausman test, ANOVA and GMM —
         panel regression with HC1 robust standard errors.</p>
    </div>
    <div class="cat-card">
      <div class="cat-num">09</div>
      <h4>ML Prediction Engine</h4>
      <p>Random Forest, XGBoost and LightGBM leverage forecasts with
         SHAP feature-importance decomposition.</p>
    </div>
    <div class="cat-card">
      <div class="cat-num">10</div>
      <h4>Time-Series Forecasting</h4>
      <p>LSTM/GRU sequence models projecting leverage trends for individual firms.</p>
    </div>
    <div class="cat-card">
      <div class="cat-num">11</div>
      <h4>Lifecycle Clustering</h4>
      <p>K-Means clustering vs Dickinson (2011) classification — tests
         how closely financial-signal clusters align with rule-based life stages.</p>
    </div>
    <div class="cat-card">
      <div class="cat-num">12</div>
      <h4>Stage Transition Matrices</h4>
      <p>Year-on-year transition probabilities between the eight life stages,
         revealing how frequently firms migrate, stabilise or exit.</p>
    </div>
    <div class="cat-card">
      <div class="cat-num">13</div>
      <h4>Interaction Effects</h4>
      <p>Cross-term (Profitability × Tangibility) OLS and stage-moderation model —
         delta-method standard errors reveal per-stage marginal effects.</p>
    </div>
  </div>
</section>

<!-- SCREENSHOT: DASHBOARD OVERVIEW -->
<div style="max-width:1100px;margin:0 auto;padding:0 2rem">
  <div class="screenshot-wrap">
    <img src="data:image/png;base64,{DASH}" alt="LifeCycle Leverage Dashboard — Stage KPI Overview"/>
    <div class="screenshot-caption">
      <strong>Dashboard overview</strong> — Stage KPI tiles, leverage trend ribbon and Dickinson stage distribution
      across 401 firms, 2001–2024 (thesis panel). Source: LifeCycle Leverage Dashboard, Kumar (2025).
    </div>
  </div>
</div>

<hr class="divider" style="max-width:1100px;margin:2rem auto"/>

<!-- STAKEHOLDERS -->
<section class="section" id="stakeholders">
  <div class="section-tag">Use Cases by Role</div>
  <h2>Capital Intelligence for Every Seat at the Table</h2>
  <p class="section-intro">Eight corporate functions, eight distinct questions —
     all answered from a single, data-consistent source
     (CMIE Prowess thesis panel, Kumar 2025).</p>

  <div class="sh-grid">

    <!-- 1. BOARD -->
    <div class="sh-card">
      <div class="sh-header">
        <div class="sh-icon" style="background:#f0fdf4;font-size:1.3rem">📊</div>
        <div>
          <div class="sh-role">Use Case 1</div>
          <h3>Board of Directors</h3>
        </div>
      </div>
      <div class="sh-body">
        <div class="sh-company">Asian Paints Ltd · NSE: ASIANPAINT</div>
        <p>Asian Paints spent all <strong>24 years</strong> (2001–2024) classified in the
           <span class="stage-badge badge-maturity">Maturity</span> stage —
           the only firm in the 401-company panel with an unbroken Maturity record.
           The Stage KPI Dashboard and Stage Transition module confirm this perpetual classification.
           Leverage fell from <strong>25.66%</strong> (2001) to a trough of <strong>0.10%</strong>
           (2018), then rose modestly to <strong>4.44%</strong> (2024), far below the
           Maturity-stage median of <strong>18.96%</strong> measured across the thesis panel.</p>
        <div class="data-row"><span class="data-label">Leverage (2001)</span><span class="data-val">25.66%</span></div>
        <div class="data-row"><span class="data-label">Leverage (2018 trough)</span><span class="data-val green">0.10%</span></div>
        <div class="data-row"><span class="data-label">Leverage (2024)</span><span class="data-val">4.44%</span></div>
        <div class="data-row"><span class="data-label">Maturity-stage median (panel)</span><span class="data-val">18.96%</span></div>
        <div class="data-row"><span class="data-label">Consecutive years in Maturity</span><span class="data-val green">24 / 24</span></div>
        <p style="margin-top:.75rem">The board uses the <em>Peer Benchmarking</em> module
           to verify that Asian Paints stays well below stage-median leverage year after year —
           confirming balance-sheet conservatism as a durable strategic posture.</p>
        <p class="citation">Source: CMIE Prowess, thesis panel (vintage = <em>thesis</em>), 2001–2024;
           Dickinson (2011) classification; Kumar (2025, Ch. 5).</p>
      </div>
    </div>

    <!-- 2. CFO -->
    <div class="sh-card">
      <div class="sh-header">
        <div class="sh-icon" style="background:#eff6ff;font-size:1.3rem">💼</div>
        <div>
          <div class="sh-role">Use Case 2</div>
          <h3>Chief Financial Officer</h3>
        </div>
      </div>
      <div class="sh-body">
        <div class="sh-company">Tata Motors Ltd · NSE: TATAMOTORS</div>
        <p>In 2024, Tata Motors is classified as
           <span class="stage-badge badge-shakeout">Shakeout 3</span>
           with leverage of <strong>20.29%</strong> —
           placing it at the <strong>86th percentile</strong> among its 56 Shakeout-3 stage-peers
           in the same year (Peer Benchmarking module).
           Profitability of <strong>18.12%</strong> ranks at the 62nd percentile.
           Interest coverage recovered to <strong>5.00×</strong> (2024) after a
           severe distress episode: coverage fell to <strong>−0.08×</strong> (2021)
           and <strong>0.45×</strong> (2022). CFOs use the Econometrics Lab OLS model
           to estimate the leverage reduction achievable through retained-earnings
           accumulation, given the panel coefficient on profitability.</p>
        <div class="data-row"><span class="data-label">Leverage (2024)</span><span class="data-val amber">20.29%</span></div>
        <div class="data-row"><span class="data-label">Leverage pct-rank (vs 56 peers)</span><span class="data-val amber">86th pct</span></div>
        <div class="data-row"><span class="data-label">Profitability (2024)</span><span class="data-val">18.12%</span></div>
        <div class="data-row"><span class="data-label">Interest coverage (2021 trough)</span><span class="data-val red">−0.08×</span></div>
        <div class="data-row"><span class="data-label">Interest coverage (2024)</span><span class="data-val green">5.00×</span></div>
        <p class="citation">Source: CMIE Prowess, thesis panel, 2001–2024; Kumar (2025, Ch. 5–6);
           Rajan &amp; Zingales (1995) leverage determinants framework.</p>
      </div>
    </div>

    <!-- 3. TREASURER -->
    <div class="sh-card">
      <div class="sh-header">
        <div class="sh-icon" style="background:#fef3c7;font-size:1.3rem">🏦</div>
        <div>
          <div class="sh-role">Use Case 3</div>
          <h3>Group Treasurer</h3>
        </div>
      </div>
      <div class="sh-body">
        <div class="sh-company">Bajaj Auto Ltd · NSE: BAJAJ-AUTO</div>
        <p>Bajaj Auto sits in
           <span class="stage-badge badge-maturity">Maturity</span>
           (2024) with leverage of only <strong>2.79%</strong> —
           the <strong>39th leverage percentile</strong> among 244 Maturity-stage
           firm-years (many near-zero-debt firms populate this cohort).
           Headroom to stage median: <strong>16.17 percentage points</strong>.
           Interest coverage at <strong>141.09×</strong> signals exceptional
           debt-servicing capacity. The Treasurer uses the
           <em>Scenario OLS</em> module to model how much NCD or commercial-paper
           issuance could be absorbed before leverage reaches the stage median —
           while maintaining investment-grade headroom.</p>
        <div class="scenario-tag">⚠ Scenario Illustration Below</div>
        <p style="font-size:.82rem;color:var(--ink2);background:#fef9c3;border-radius:6px;
                  padding:.6rem .8rem;border:1px solid #fde68a">
           <em>Illustrative scenario (not observed data):</em> If Bajaj Auto were to issue
           ₹5,000 Cr of NCDs, leverage would rise from 2.79% to approximately 7–9%
           (depending on total assets), remaining below the Maturity-stage median of 18.96%.
           The Scenario OLS module computes this estimate using
           β(tangibility) = +0.142 and β(profitability) = −0.187 (both p &lt; 0.01).
        </p>
        <div class="data-row"><span class="data-label">Leverage (2024)</span><span class="data-val green">2.79%</span></div>
        <div class="data-row"><span class="data-label">Leverage pct-rank (244 Maturity peers)</span><span class="data-val">39th pct</span></div>
        <div class="data-row"><span class="data-label">Headroom to stage median</span><span class="data-val green">16.17 pp</span></div>
        <div class="data-row"><span class="data-label">Interest coverage (2024)</span><span class="data-val green">141.09×</span></div>
        <div class="data-row"><span class="data-label">Profitability (2024)</span><span class="data-val green">29.85%</span></div>
        <p class="citation">Source: CMIE Prowess, thesis panel, 2001–2024; Myers (1984) Pecking Order;
           Scenario OLS coefficients from Kumar (2025, Ch. 6).</p>
      </div>
    </div>

    <!-- 4. RISK -->
    <div class="sh-card">
      <div class="sh-header">
        <div class="sh-icon" style="background:#fee2e2;font-size:1.3rem">🛡️</div>
        <div>
          <div class="sh-role">Use Case 4</div>
          <h3>Chief Risk Officer</h3>
        </div>
      </div>
      <div class="sh-body">
        <div class="sh-company">IBC Stress Cohort · Panel-wide (2016–2021)</div>
        <p>The Econometrics Lab flags firms where interest coverage falls below the
           IBC-linked thresholds: <strong>amber (≤ 1.5×)</strong> or
           <strong>red (≤ 1.0×)</strong>.
           Across the thesis panel, <strong>120 firms</strong> triggered amber or red
           alerts in at least one year during 2016–2021.
           Of these, <strong>102 firms (85%)</strong> recovered to above-threshold
           coverage by 2024; <strong>18 firms (15%)</strong> did not.</p>

        <div class="ibc-bar">
          <div class="ibc-green">102 firms recovered (85%)</div>
          <div class="ibc-red">18 did not (15%)</div>
        </div>

        <p>Additionally, the Stage Transition module reveals that a firm in
           Shakeout-3 transitions to <strong>Maturity 48.5%</strong> of the time in the
           next year, but migrates to <strong>Decline only 2.0%</strong> of the time —
           allowing risk teams to quantify tail risk at each life stage.</p>
        <div class="data-row"><span class="data-label">Firms entering amber/red (2016–2021)</span><span class="data-val">120</span></div>
        <div class="data-row"><span class="data-label">Recovered by 2024</span><span class="data-val green">102 (85%)</span></div>
        <div class="data-row"><span class="data-label">Did not recover</span><span class="data-val red">18 (15%)</span></div>
        <div class="data-row"><span class="data-label">Shakeout-3 → Maturity (1-yr prob.)</span><span class="data-val green">48.5%</span></div>
        <div class="data-row"><span class="data-label">Shakeout-3 → Decline (1-yr prob.)</span><span class="data-val">2.0%</span></div>
        <p class="citation">Source: CMIE Prowess, thesis panel, 2001–2024;
           Dickinson (2011) stage classification; Kumar (2025, Ch. 7);
           IBC threshold benchmarks per RBI/IBC frameworks.</p>
      </div>
    </div>

    <!-- 5. COMPLIANCE -->
    <div class="sh-card">
      <div class="sh-header">
        <div class="sh-icon" style="background:#f0f9ff;font-size:1.3rem">⚖️</div>
        <div>
          <div class="sh-role">Use Case 5</div>
          <h3>Compliance &amp; Governance</h3>
        </div>
      </div>
      <div class="sh-body">
        <div class="sh-company">Panel OLS — Capital Structure Theory Benchmarks</div>
        <p>The Econometrics Lab OLS regression (HC1 robust SEs, Fixed Effects, Hausman test)
           provides the empirically calibrated relationship between capital structure
           determinants and leverage across the full thesis panel.
           Two headline coefficients act as governance benchmarks:</p>

        <div class="theory-grid">
          <div class="theory-box pecking">
            <h4>Pecking Order Theory</h4>
            <div class="coef" style="color:#166534">β = −0.187</div>
            <p>Profitability → Leverage (p &lt; 0.01).
               Higher retained earnings substitute for debt — firms self-fund first.</p>
          </div>
          <div class="theory-box tradeoff">
            <h4>Trade-Off Theory</h4>
            <div class="coef" style="color:#1e40af">β = +0.142</div>
            <p>Tangibility → Leverage (p &lt; 0.01).
               Asset-rich firms borrow more — collateral unlocks the debt channel.</p>
          </div>
        </div>

        <p>Compliance teams use these coefficients as reference benchmarks to challenge
           whether a company's stated debt-reduction plan is consistent with its
           profitability trajectory and asset composition, relative to panel norms.</p>
        <div class="data-row"><span class="data-label">β(Profitability) — Pecking Order</span><span class="data-val">−0.187***</span></div>
        <div class="data-row"><span class="data-label">β(Tangibility) — Trade-Off</span><span class="data-val">+0.142***</span></div>
        <div class="data-row"><span class="data-label">Panel R² (Fixed Effects)</span><span class="data-val">0.412</span></div>
        <div class="data-row"><span class="data-label">Hausman test (FE preferred)</span><span class="data-val">p &lt; 0.01</span></div>
        <p class="citation">Source: Kumar (2025, Ch. 6 Table 6.2); Myers (1984);
           Modigliani &amp; Miller (1963); Rajan &amp; Zingales (1995).</p>
      </div>
    </div>

    <!-- 6. IR -->
    <div class="sh-card">
      <div class="sh-header">
        <div class="sh-icon" style="background:#f5f3ff;font-size:1.3rem">📣</div>
        <div>
          <div class="sh-role">Use Case 6</div>
          <h3>Investor Relations</h3>
        </div>
      </div>
      <div class="sh-body">
        <div class="sh-company">Infosys Ltd · NSE: INFY</div>
        <p>Infosys has spent <strong>18 of 24 years</strong> (2001–2024) in
           <span class="stage-badge badge-maturity">Maturity</span>,
           <strong>5 years</strong> in
           <span class="stage-badge badge-shakeout">Shakeout 3</span>,
           and <strong>1 year</strong> in
           <span class="stage-badge badge-growth">Growth</span>,
           per the Dickinson (2011) cash-flow classification
           (Stage Transition module). In 2024, leverage stands at just
           <strong>3.20%</strong> (40th percentile vs 244 Maturity peers),
           while profitability of <strong>34.22%</strong> ranks at the
           <strong>95th percentile</strong>. Interest coverage of <strong>134.09×</strong>
           provides exceptional headroom. IR teams use the Knowledge Graph and
           Scenario OLS modules to narrate this structural advantage to debt and
           equity investors in quarterly calls and credit-rating presentations.</p>

        <div class="stage-dist">
          <div class="sd-label"><span>Maturity (18 yrs)</span><span>Shakeout-3 (5 yrs)</span><span>Growth (1 yr)</span></div>
          <div class="stage-dist-bar">
            <div class="sd-fill" style="width:75%;background:#16a34a"></div>
            <div class="sd-fill" style="width:20.8%;background:#d97706"></div>
            <div class="sd-fill" style="width:4.2%;background:#2563eb"></div>
          </div>
        </div>

        <div class="data-row"><span class="data-label">Leverage (2024)</span><span class="data-val green">3.20%</span></div>
        <div class="data-row"><span class="data-label">Leverage pct-rank (244 Maturity peers)</span><span class="data-val">40th pct</span></div>
        <div class="data-row"><span class="data-label">Profitability (2024)</span><span class="data-val green">34.22%</span></div>
        <div class="data-row"><span class="data-label">Profitability pct-rank</span><span class="data-val green">95th pct</span></div>
        <div class="data-row"><span class="data-label">Interest coverage (2024)</span><span class="data-val green">134.09×</span></div>
        <p class="citation">Source: CMIE Prowess, thesis panel, 2001–2024;
           Dickinson (2011); Kumar (2025, Ch. 5).</p>
      </div>
    </div>

    <!-- 7. STRATEGY -->
    <div class="sh-card">
      <div class="sh-header">
        <div class="sh-icon" style="background:#fff7ed;font-size:1.3rem">🔭</div>
        <div>
          <div class="sh-role">Use Case 7</div>
          <h3>Corporate Strategy</h3>
        </div>
      </div>
      <div class="sh-body">
        <div class="sh-company">Reliance Industries Ltd · NSE: RELIANCE</div>
        <p>Reliance's Jio-era capital cycle is visible in the Dickinson
           cash-flow classification (Stage Transition module).
           The company transitioned through three distinct stages in four years —
           one of the most dramatic lifecycle shifts in the panel:</p>
        <div class="data-row">
          <span class="data-label">2019</span>
          <span class="data-val"><span class="stage-badge badge-growth">Growth</span> NCFI: −₹53,949 Cr</span>
        </div>
        <div class="data-row">
          <span class="data-label">2020</span>
          <span class="data-val"><span class="stage-badge badge-growth">Growth</span> NCFI: −₹1,43,625 Cr</span>
        </div>
        <div class="data-row">
          <span class="data-label">2021</span>
          <span class="data-val"><span class="stage-badge badge-decay">Decay</span> NCFO: −₹512 Cr</span>
        </div>
        <div class="data-row">
          <span class="data-label">2022–2024</span>
          <span class="data-val"><span class="stage-badge badge-maturity">Maturity</span> ~22% leverage</span>
        </div>
        <p style="margin-top:.75rem">Strategy teams use the Stage Transition module to
           identify when a firm's cash-flow signature shifts, and overlay the OLS
           Scenario module to project how leverage tracks capital-allocation decisions.
           The ₹1.43 Lakh Cr NCFI outflow in 2020 — the largest single-year investing
           cash drain in the panel — is directly observable in the Raw Panel Explorer.</p>
        <p class="citation">Source: CMIE Prowess, thesis panel, 2001–2024;
           Dickinson (2011) cash-flow classification; Kumar (2025, Ch. 5 Table 5.9).</p>
      </div>
    </div>

    <!-- 8. BANKER -->
    <div class="sh-card">
      <div class="sh-header">
        <div class="sh-icon" style="background:#f0fdfa;font-size:1.3rem">🤝</div>
        <div>
          <div class="sh-role">Use Case 8</div>
          <h3>Investment Banker / Lender</h3>
        </div>
      </div>
      <div class="sh-body">
        <div class="sh-company">Maruti Suzuki vs Wipro · Maturity Cohort (2023)</div>
        <p>Both firms sit in
           <span class="stage-badge badge-maturity">Maturity</span> (2023),
           yet their leverage and coverage profiles differ sharply —
           illustrating why stage-peer comparison (Peer Benchmarking module)
           matters more than aggregate averages for underwriting decisions.
           The Interaction Effects module further reveals that tangibility's
           marginal effect on leverage differs across life stages
           (delta-method SE, stage moderation OLS).</p>

        <div class="data-row"><span class="data-label">Maruti leverage (2023)</span><span class="data-val green">1.53%</span></div>
        <div class="data-row"><span class="data-label">Maruti tangibility (2023)</span><span class="data-val">21.30%</span></div>
        <div class="data-row"><span class="data-label">Maruti interest coverage (2023)</span><span class="data-val green">55.92×</span></div>
        <div class="data-row"><span class="data-label">Wipro leverage (2023)</span><span class="data-val">7.36%</span></div>
        <div class="data-row"><span class="data-label">Wipro tangibility (2023)</span><span class="data-val">10.21%</span></div>
        <div class="data-row"><span class="data-label">Wipro interest coverage (2023)</span><span class="data-val">12.71×</span></div>
        <div class="data-row"><span class="data-label">Maturity-stage median leverage (panel)</span><span class="data-val">18.96%</span></div>
        <p style="margin-top:.75rem">Both firms are well below the Maturity-stage median
           leverage of 18.96%, suggesting strong capacity to issue new debt —
           but Maruti's 21.30% tangibility (collateral base) gives it
           a structural advantage per the Trade-Off Theory coefficient
           β(tangibility) = +0.142 (Econometrics Lab).</p>
        <p class="citation">Source: CMIE Prowess, thesis panel, 2001–2024;
           Rajan &amp; Zingales (1995); Modigliani &amp; Miller (1963);
           Kumar (2025, Ch. 6); Interaction Effects module (delta-method SEs).</p>
      </div>
    </div>

  </div><!-- /sh-grid -->
</section>

<!-- SCREENSHOT: PEER BENCHMARKS -->
<div style="max-width:1100px;margin:0 auto;padding:0 2rem">
  <div class="screenshot-wrap">
    <img src="data:image/png;base64,{BENCH}" alt="Peer Benchmarking — Tata Motors vs Shakeout-3 stage peers"/>
    <div class="screenshot-caption">
      <strong>Peer Benchmarking module</strong> — Tata Motors leverage and profitability percentile rankings
      versus its 56 Shakeout-3 stage-peers (2024). Source: LifeCycle Leverage Dashboard, Kumar (2025).
    </div>
  </div>
</div>

<hr class="divider" style="max-width:1100px;margin:2rem auto"/>

<!-- THEORY SECTION -->
<section class="section" id="theory">
  <div class="section-tag">Theoretical Foundation</div>
  <h2>Two Theories, One Framework</h2>
  <p class="section-intro">The panel regression results (Econometrics Lab, HC1 robust SEs,
     Fixed Effects preferred by Hausman test) support both major capital-structure theories
     simultaneously — Pecking Order dominates for profitable firms;
     Trade-Off dominates for asset-rich firms.</p>

  <div class="theory-grid">
    <div class="theory-box pecking">
      <h4>Pecking Order Theory — Myers (1984)</h4>
      <div class="coef" style="color:#166534">β(Profitability) = −0.187***</div>
      <p>Firms with higher profitability accumulate retained earnings and use
         less external debt. Consistent with the Pecking Order hierarchy:
         internal funds → debt → equity. Significant at p &lt; 0.01 across
         OLS, Fixed Effects and GMM specifications.</p>
    </div>
    <div class="theory-box tradeoff">
      <h4>Trade-Off Theory — Modigliani &amp; Miller (1963)</h4>
      <div class="coef" style="color:#1e40af">β(Tangibility) = +0.142***</div>
      <p>Firms with more fixed assets (collateral) carry higher leverage —
         collateral reduces lender risk and unlocks the debt channel.
         Significant at p &lt; 0.01. Consistent with Rajan &amp; Zingales (1995)
         international evidence.</p>
    </div>
  </div>

  <p style="margin-top:1.5rem;font-size:.9rem;color:var(--ink2)">
    The Interaction Effects module tests whether these two forces interact:
    a significant negative β₃ (Profitability × Tangibility cross-term) would imply
    firms that are <em>both</em> highly profitable <em>and</em> highly tangible
    reduce leverage more aggressively than either characteristic alone predicts —
    Pecking Order and Trade-Off operating simultaneously.
    The Stage Moderation OLS further reveals how these marginal effects shift
    across the eight Dickinson life stages (delta-method standard errors).
  </p>
</section>

<!-- SCREENSHOTS: SCENARIOS + ECONOMETRICS -->
<div style="max-width:1100px;margin:0 auto;padding:0 2rem;display:grid;grid-template-columns:1fr 1fr;gap:1.5rem">
  <div class="screenshot-wrap">
    <img src="data:image/png;base64,{SCEN}" alt="Scenario OLS module"/>
    <div class="screenshot-caption">
      <strong>Scenario OLS module</strong> — what-if leverage forecasts using calibrated panel coefficients.
      Scenario outputs are illustrative projections, not observed data.
      Source: LifeCycle Leverage Dashboard, Kumar (2025).
    </div>
  </div>
  <div class="screenshot-wrap">
    <img src="data:image/png;base64,{ECON}" alt="Econometrics Lab"/>
    <div class="screenshot-caption">
      <strong>Econometrics Lab</strong> — OLS, Fixed Effects, Random Effects, Hausman test and GMM
      with HC1 robust standard errors. Source: LifeCycle Leverage Dashboard, Kumar (2025).
    </div>
  </div>
</div>

<hr class="divider" style="max-width:1100px;margin:2rem auto"/>

<!-- RISK SECTION -->
<section class="section" id="risk">
  <div class="section-tag">Financial Stress &amp; IBC Risk</div>
  <h2>Early-Warning Framework for Distress</h2>
  <p class="section-intro">The Econometrics Lab computes interest coverage ratios
     (PBIT / Interest) for every firm-year and applies IBC-linked thresholds.
     Results below are sourced from the thesis panel (CMIE Prowess, 2001–2024).</p>

  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.25rem;margin:1.5rem 0">
    <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:var(--radius);padding:1.25rem;text-align:center">
      <div style="font-size:2rem;font-weight:700;color:#dc2626">120</div>
      <div style="font-size:.85rem;color:#7f1d1d;margin-top:.3rem">
        Firms with amber or red coverage alerts<br/>in at least one year, 2016–2021
      </div>
    </div>
    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:var(--radius);padding:1.25rem;text-align:center">
      <div style="font-size:2rem;font-weight:700;color:#16a34a">102</div>
      <div style="font-size:.85rem;color:#14532d;margin-top:.3rem">
        Firms recovered to above threshold<br/>by 2024 <strong>(85%)</strong>
      </div>
    </div>
    <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:var(--radius);padding:1.25rem;text-align:center">
      <div style="font-size:2rem;font-weight:700;color:#dc2626">18</div>
      <div style="font-size:.85rem;color:#7f1d1d;margin-top:.3rem">
        Firms did not recover<br/><strong>(15%)</strong>
      </div>
    </div>
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:var(--radius);padding:1.25rem;text-align:center">
      <div style="font-size:2rem;font-weight:700;color:#1d4ed8">1.5×</div>
      <div style="font-size:.85rem;color:#1e3a8a;margin-top:.3rem">
        Amber threshold<br/>(coverage ≤ 1.5×)
      </div>
    </div>
  </div>

  <p style="font-size:.88rem;color:var(--ink2);margin-top:1rem">
    <strong>Thresholds:</strong> Amber = interest coverage ≤ 1.5× (PBIT/interest);
    Red = coverage ≤ 1.0×. Formula: <em>pbit / interest_amt</em> from CMIE Prowess financials.
    Stage Transition probabilities (Shakeout-3 → Maturity: 48.5%; → Decline: 2.0%)
    derived from the year-on-year Dickinson classification transitions in the thesis panel.
  </p>
  <p class="citation" style="font-size:.78rem;color:var(--ink3);margin-top:.75rem">
    Source: CMIE Prowess, thesis panel (vintage = <em>thesis</em>), 2001–2024;
    Kumar (2025, Ch. 7); Dickinson (2011); IBC framework benchmarks.
  </p>
</section>

<hr class="divider" style="max-width:1100px;margin:2rem auto"/>

<!-- STAGE AVERAGES -->
<section class="section">
  <div class="section-tag">Stage-level leverage norms</div>
  <h2>Leverage Medians by Life Stage — Thesis Panel</h2>
  <p class="section-intro">Stage-average leverage (% of total assets) across all
     8,677 firm-year observations, thesis panel, 2001–2024.
     These norms are the baseline for all peer-benchmarking percentile calculations.</p>

  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:1rem;margin:1.5rem 0">
    <div style="border:1px solid #fecaca;border-radius:var(--radius);padding:1rem;background:#fef2f2">
      <span class="stage-badge badge-decline">Decline</span>
      <div style="font-size:1.6rem;font-weight:700;color:#dc2626;margin:.4rem 0">37.77%</div>
      <div style="font-size:.75rem;color:var(--ink3)">Highest leverage stage</div>
    </div>
    <div style="border:1px solid #ede9fe;border-radius:var(--radius);padding:1rem;background:#f5f3ff">
      <span class="stage-badge badge-startup">Startup</span>
      <div style="font-size:1.6rem;font-weight:700;color:#7c3aed;margin:.4rem 0">34.20%</div>
      <div style="font-size:.75rem;color:var(--ink3)">External financing dependent</div>
    </div>
    <div style="border:1px solid #fef3c7;border-radius:var(--radius);padding:1rem;background:#fffbeb">
      <span class="stage-badge badge-shakeout">Shakeout 2</span>
      <div style="font-size:1.6rem;font-weight:700;color:#d97706;margin:.4rem 0">32.50%</div>
      <div style="font-size:.75rem;color:var(--ink3)">Contraction phase</div>
    </div>
    <div style="border:1px solid #bfdbfe;border-radius:var(--radius);padding:1rem;background:#eff6ff">
      <span class="stage-badge badge-growth">Growth</span>
      <div style="font-size:1.6rem;font-weight:700;color:#2563eb;margin:.4rem 0">29.68%</div>
      <div style="font-size:.75rem;color:var(--ink3)">Investment-driven leverage</div>
    </div>
    <div style="border:1px solid #e5e7eb;border-radius:var(--radius);padding:1rem;background:#f9fafb">
      <span class="stage-badge badge-decay">Decay</span>
      <div style="font-size:1.6rem;font-weight:700;color:#374151;margin:.4rem 0">24.19%</div>
      <div style="font-size:.75rem;color:var(--ink3)">All CF negative</div>
    </div>
    <div style="border:1px solid #bbf7d0;border-radius:var(--radius);padding:1rem;background:#f0fdf4">
      <span class="stage-badge badge-maturity">Maturity</span>
      <div style="font-size:1.6rem;font-weight:700;color:#16a34a;margin:.4rem 0">18.96%</div>
      <div style="font-size:.75rem;color:var(--ink3)">Steady-state — reference stage</div>
    </div>
    <div style="border:1px solid #fef3c7;border-radius:var(--radius);padding:1rem;background:#fffbeb">
      <span class="stage-badge badge-shakeout">Shakeout 3</span>
      <div style="font-size:1.6rem;font-weight:700;color:#d97706;margin:.4rem 0">16.45%</div>
      <div style="font-size:.75rem;color:var(--ink3)">Selective contraction</div>
    </div>
    <div style="border:1px solid #fef3c7;border-radius:var(--radius);padding:1rem;background:#fffbeb">
      <span class="stage-badge badge-shakeout">Shakeout 1</span>
      <div style="font-size:1.6rem;font-weight:700;color:#d97706;margin:.4rem 0">15.20%</div>
      <div style="font-size:.75rem;color:var(--ink3)">Lowest leverage stage</div>
    </div>
  </div>
  <p class="citation">Source: CMIE Prowess, thesis panel (vintage = <em>thesis</em>), 401 firms,
     8,677 firm-year obs, 2001–2024; Dickinson (2011) stage classification;
     Kumar (2025, Ch. 5, Table 5.5).</p>
</section>

<hr class="divider" style="max-width:1100px;margin:2rem auto"/>

<!-- REFERENCES -->
<section class="section" id="references">
  <div class="section-tag">Data &amp; Literature Sources</div>
  <h2>References</h2>
  <div class="refs">
    <h3>Data Sources</h3>
    <p class="ref-item">CMIE (2025). <em>Prowess company financial database</em>.
       Centre for Monitoring Indian Economy Pvt Ltd, Mumbai. Thesis panel:
       401 firms, 8,677 firm-year observations, 2001–2024 (vintage = <em>thesis</em>).</p>
    <p class="ref-item">Kumar, S. (2025). <em>Capital structure determinants and corporate life cycle:
       Evidence from Indian listed firms</em>. PhD thesis, University of Delhi.
       [All analytical outputs reproduced using the thesis-vintage panel.]</p>
  </div>
  <div class="refs" style="margin-top:1rem">
    <h3>Academic Literature</h3>
    <p class="ref-item">Dickinson, V. (2011). Cash flow patterns as a proxy for firm life cycle.
       <em>The Accounting Review</em>, 86(6), 1969–1994.
       [Life-stage classification scheme used throughout the dashboard.]</p>
    <p class="ref-item">Myers, S. C. (1984). The capital structure puzzle.
       <em>The Journal of Finance</em>, 39(3), 574–592.
       [Pecking Order Theory — β(profitability) = −0.187, p &lt; 0.01.]</p>
    <p class="ref-item">Modigliani, F., &amp; Miller, M. H. (1963). Corporate income taxes and
       the cost of capital: A correction. <em>The American Economic Review</em>, 53(3), 433–443.
       [Tax shield rationale for the Trade-Off Theory.]</p>
    <p class="ref-item">Rajan, R. G., &amp; Zingales, L. (1995). What do we know about capital structure?
       Some evidence from international data. <em>The Journal of Finance</em>, 50(5), 1421–1460.
       [Tangibility as a leverage determinant — β(tangibility) = +0.142, p &lt; 0.01.]</p>
    <p class="ref-item">Frank, M. Z., &amp; Goyal, V. K. (2009). Capital structure decisions: Which factors
       are reliably important? <em>Financial Management</em>, 38(1), 1–37.
       [Comprehensive survey of leverage determinants used in variable selection.]</p>
    <p class="ref-item">DeAngelo, H., &amp; Roll, R. (2015). How stable are corporate capital structures?
       <em>The Journal of Finance</em>, 70(1), 373–418.
       [Stage-persistence and mean-reversion in leverage — motivation for transition matrices.]</p>
  </div>
</section>

<!-- CTA -->
<section class="cta-band" id="contact">
  <h2>Ready to Put Your Data to Work?</h2>
  <p>The LifeCycle Leverage Dashboard is available to institutional subscribers.
     Contact the research team for a live demonstration or panel access.</p>
  <a href="mailto:drbhatiasanjay@gmail.com" class="btn-cta">Request Access →</a>
</section>

<!-- AUTHORS -->
<section class="section" style="padding-top:3rem">
  <div class="authors">
    <img src="data:image/webp;base64,{AUTHOR}" alt="Dr Sanjay Bhatia" class="author-photo"/>
    <div class="author-info">
      <h4>Dr Sanjay K. Bhatia</h4>
      <p>Co-founder, EOLABS · Research Collaborator<br/>
         Dashboard architecture, data engineering, CMIE integration,
         econometric modelling and ML pipeline.
         Contact: <a href="mailto:drbhatiasanjay@gmail.com">drbhatiasanjay@gmail.com</a></p>
    </div>
    <div class="author-info" style="margin-left:2rem">
      <h4>Prof Surendra Kumar</h4>
      <p>Principal Investigator<br/>
         Faculty of Management Studies, University of Delhi<br/>
         PhD thesis: <em>Capital Structure Determinants and Corporate Life Cycle:
         Evidence from Indian Listed Firms</em> (2025). Nifty 500 panel, 401 companies.</p>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <div style="display:flex;align-items:center;gap:.6rem">
    {LOGO_SVG}
    <span><strong>EOLABS</strong> · LifeCycle Leverage Dashboard</span>
  </div>
  <div>All figures sourced from CMIE Prowess thesis panel (2001–2024) unless marked <em>Scenario Illustration</em>.</div>
  <div>© 2025 EOLABS. Academic use only.</div>
</footer>

</body>
</html>"""

out = 'profsur-ebook-v3.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(HTML)

size_kb = len(HTML.encode('utf-8')) / 1024
print(f"Written: {out}  ({size_kb:.1f} KB)")
