#!/usr/bin/env python3
"""
Generate profsur-ebook-v3.1.html — Stakeholder's Practical Guide to the LifeCycle Leverage Dashboard.
Same chapter/ebook format as profsur-ebook-v2.html, stakeholder-focused content,
all figures from CMIE Prowess thesis panel (2001-2024, 8,677 obs, 401 firms).
Run from project root: py -3.12 scripts/make_ebook_v3_1.py
"""
import sys

def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().strip()

try:
    AUTHOR = load('_author_photo_b64.txt')
except FileNotFoundError as e:
    print(f"ERROR: {e}\nRun from project root.", file=sys.stderr)
    sys.exit(1)

# Same logo extracted from v2.html (the original PNG)
V2_LOGO_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAZAAAAGQCAIAAAAP3aGbAAAJyklEQVR42u3dPXbexhIEUBKHKyCZaI8KtQyF2qO24cChrXNsAhhMdd2bPz25ZrrQ"
    "+Pij18+P9xeABIcIAIUFoLAAhQWgsAAUFqCwABQWgMICFBaAwgJQWIDCAlBYAAoLUFgACgtAYQEKC0BhAQoLQGEBKCwAhQUoLACFBaCwAIUFoLAA"
    "FBaAsAAUFqCwABQWgMICFBaAwgJQWIDCAlBYgMICUFgACgtAYQEKC0BhASgsQGEBKCwAhQUoLACFBSgsAIUFoLAAFBaAsAAUFoDCAhQWgMICFBaA"
    "wgJQWIDCAlBYgMICUFgACgtAYQEKC0BhASgsQGEBKCwAhQUoLACFBaCwAIUFoLAAFBaAwgJQWAAKC0BhASgsQGEBKCwAhQWgsAAUFoDCAlBYgMIC"
    "UFgACgtAYQEKC0BhASgsQGEBKCwAhQWgsAAUFoDCAlBYgMICUFgACgtAYQEKC0BhASgsQGEBKCwAhQWgsAAUFoDCAlBYgMICUFgACgtAYQEKC0Bh"
    "ASgsQGEBKCwAhQWgsAAUFoDCAlBYgMICUFgACgtAYQEKC0BhASgsQGEBKCwAhQWgsAA="
)

HTML = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Capital at Every Table — Practitioner's Guide | EOLABS</title>
<link href="https://api.fontshare.com/v2/css?f[]=general-sans@300,400,500,600&display=swap" rel="stylesheet">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
<style>
:root,[data-theme="light"]{{--color-bg:#f5f4f0;--color-surface:#f9f8f5;--color-surface-2:#fdfcfb;--color-surface-offset:#efede8;--color-surface-dynamic:#e8e6e0;--color-divider:#dedad3;--color-border:#d1cdc5;--color-text:#1a1916;--color-text-muted:#6b6a65;--color-text-faint:#a8a69f;--color-text-inverse:#f5f4f0;--color-primary:#01696f;--color-primary-hover:#015a5f;--color-primary-subtle:#e0f0f1;--color-primary-text:#fff;--shadow-sm:0 1px 3px rgba(20,19,18,.06);--shadow-md:0 4px 16px rgba(20,19,18,.09);--font-display:'Instrument Serif',Georgia,serif;--font-body:'General Sans','Helvetica Neue',sans-serif;--text-xs:clamp(.75rem,.7rem + .25vw,.875rem);--text-sm:clamp(.875rem,.82rem + .25vw,1rem);--text-base:clamp(1rem,.95rem + .25vw,1.125rem);--text-lg:clamp(1.125rem,1rem + .6vw,1.375rem);--text-xl:clamp(1.375rem,1.1rem + 1.1vw,2rem);--text-2xl:clamp(2rem,1.4rem + 2.2vw,3.25rem);--text-3xl:clamp(2.75rem,1.2rem + 4.5vw,5.5rem);--radius-md:8px;--radius-lg:12px;--radius-xl:16px;--radius-2xl:24px;--space-1:.25rem;--space-2:.5rem;--space-3:.75rem;--space-4:1rem;--space-5:1.25rem;--space-6:1.5rem;--space-8:2rem;--space-10:2.5rem;--space-12:3rem;--space-16:4rem;--space-20:5rem;--space-24:6rem;--transition-ui:200ms cubic-bezier(.16,1,.3,1);--content-narrow:640px;--content-default:960px;--content-wide:1200px}}
[data-theme="dark"]{{--color-bg:#141312;--color-surface:#1a1917;--color-surface-2:#201f1c;--color-surface-offset:#111010;--color-surface-dynamic:#272522;--color-divider:#2a2826;--color-border:#333130;--color-text:#e8e6e2;--color-text-muted:#7a7872;--color-text-faint:#4f4d4a;--color-text-inverse:#141312;--color-primary:#2d9fa6;--color-primary-hover:#3db5bd;--color-primary-subtle:#1a2f30;--color-primary-text:#fff;--shadow-sm:0 1px 3px rgba(0,0,0,.25);--shadow-md:0 4px 16px rgba(0,0,0,.35)}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{-webkit-font-smoothing:antialiased;scroll-behavior:smooth;scroll-padding-top:80px;text-size-adjust:none}}
body{{min-height:100dvh;font-family:var(--font-body);font-size:var(--text-base);color:var(--color-text);background:var(--color-bg);line-height:1.65;transition:background .25s,color .25s}}
img,svg{{display:block;max-width:100%;height:auto}}ul,ol{{list-style:none}}
h1,h2,h3{{text-wrap:balance;font-family:var(--font-display);font-weight:400;line-height:1.12}}
h4,h5,h6{{font-family:var(--font-body);font-weight:600;line-height:1.3}}
p{{text-wrap:pretty;max-width:68ch}}a{{color:inherit;text-decoration:none}}
::selection{{background:rgba(1,105,111,.15);color:var(--color-text)}}
:focus-visible{{outline:2px solid var(--color-primary);outline-offset:3px;border-radius:var(--radius-md)}}
.nav{{position:sticky;top:0;z-index:100;height:64px;display:flex;align-items:center;justify-content:space-between;padding:0 clamp(var(--space-6),5vw,var(--space-16));background:rgba(245,244,240,.88);backdrop-filter:blur(12px);border-bottom:1px solid transparent;transition:border-color var(--transition-ui)}}
[data-theme="dark"] .nav{{background:rgba(20,19,18,.85)}}
.nav.scrolled{{border-bottom-color:var(--color-divider)}}
.nav-brand{{display:flex;align-items:center;gap:var(--space-3);color:var(--color-text)}}
.nav-name{{font-weight:600;font-size:var(--text-sm);letter-spacing:.04em}}
.nav-right{{display:flex;align-items:center;gap:var(--space-4)}}
.nav-tag{{font-size:var(--text-xs);font-weight:500;letter-spacing:.08em;text-transform:uppercase;color:var(--color-text-muted);padding:var(--space-1) var(--space-3);border:1px solid var(--color-border);border-radius:var(--radius-md)}}
.theme-btn{{width:36px;height:36px;display:flex;align-items:center;justify-content:center;border-radius:var(--radius-md);color:var(--color-text-muted);cursor:pointer;background:none;border:none;transition:background var(--transition-ui)}}
.theme-btn:hover{{background:var(--color-surface-dynamic);color:var(--color-text)}}
.icon-moon{{display:none}}[data-theme="dark"] .icon-sun{{display:none}}[data-theme="dark"] .icon-moon{{display:block}}
.container{{max-width:var(--content-wide);margin-inline:auto;padding-inline:clamp(var(--space-6),5vw,var(--space-16))}}
.container--narrow{{max-width:var(--content-default);margin-inline:auto;padding-inline:clamp(var(--space-6),5vw,var(--space-16))}}
.section-label{{font-family:var(--font-body);font-size:var(--text-xs);font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--color-primary);display:block;margin-bottom:var(--space-4)}}
.hero{{padding:clamp(var(--space-20),10vw,var(--space-24)) 0 clamp(var(--space-16),8vw,var(--space-20));background:var(--color-bg)}}
.hero-pretag{{display:inline-flex;align-items:center;gap:var(--space-2);font-size:var(--text-xs);font-weight:500;letter-spacing:.08em;text-transform:uppercase;color:var(--color-text-muted);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:var(--space-1) var(--space-3);margin-bottom:var(--space-8)}}
.hero h1{{font-size:var(--text-3xl);letter-spacing:-.02em;color:var(--color-text);margin-bottom:var(--space-6);max-width:14ch}}
.hero-lead{{font-size:var(--text-lg);color:var(--color-text-muted);max-width:56ch;line-height:1.6;margin-bottom:var(--space-10)}}
.hero-actions{{display:flex;flex-wrap:wrap;gap:var(--space-4);align-items:center}}
.btn{{font-family:var(--font-body);font-size:var(--text-sm);font-weight:500;padding:var(--space-3) var(--space-6);border-radius:var(--radius-md);border:1.5px solid transparent;cursor:pointer;display:inline-flex;align-items:center;gap:var(--space-2);text-decoration:none;transition:background var(--transition-ui),border-color var(--transition-ui),color var(--transition-ui),box-shadow var(--transition-ui);white-space:nowrap}}
.btn:active{{transform:scale(.98)}}
.btn-primary{{background:var(--color-primary);color:var(--color-primary-text);border-color:var(--color-primary)}}
.btn-primary:hover{{background:var(--color-primary-hover);border-color:var(--color-primary-hover);box-shadow:0 4px 16px rgba(1,105,111,.25)}}
.btn-secondary{{background:transparent;color:var(--color-text);border-color:var(--color-border)}}
.btn-secondary:hover{{background:var(--color-surface-dynamic);border-color:var(--color-text-muted)}}
.stats-strip{{background:#141312;padding:clamp(var(--space-10),6vw,var(--space-16)) 0}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:var(--space-8) var(--space-6);text-align:center}}
.stat-number{{font-family:var(--font-body);font-size:var(--text-2xl);font-weight:600;color:#2d9fa6;line-height:1;display:block}}
.stat-label{{font-size:var(--text-xs);color:#7a7872;display:block;margin-top:var(--space-2);letter-spacing:.04em}}
.chapter{{padding:clamp(var(--space-16),8vw,var(--space-24)) 0}}
.chapter--alt{{background:var(--color-surface-offset)}}
.chapter h2{{font-size:var(--text-2xl);letter-spacing:-.015em;color:var(--color-text);margin-bottom:var(--space-6)}}
.chapter-body{{font-size:var(--text-base);color:var(--color-text-muted);line-height:1.75;max-width:68ch}}
.chapter-body+.chapter-body{{margin-top:var(--space-5)}}
.chapter-lead{{font-size:var(--text-lg);color:var(--color-text);line-height:1.6;max-width:60ch;margin-bottom:var(--space-8)}}
.callout{{background:var(--color-primary-subtle);border-left:3px solid var(--color-primary);border-radius:0 var(--radius-lg) var(--radius-lg) 0;padding:var(--space-6) var(--space-8);margin:var(--space-10) 0}}
.callout-text{{font-family:var(--font-display);font-style:italic;font-size:var(--text-xl);color:var(--color-text);line-height:1.4;max-width:52ch}}
.scenario-callout{{background:#fffbeb;border-left:3px solid #f59e0b;border-radius:0 var(--radius-lg) var(--radius-lg) 0;padding:var(--space-6) var(--space-8);margin:var(--space-8) 0}}
.scenario-callout-label{{font-size:var(--text-xs);font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#92400e;margin-bottom:var(--space-3)}}
.scenario-callout p{{font-size:var(--text-sm);color:#78350f;line-height:1.7;max-width:60ch}}
.leverage-table{{width:100%;border-collapse:collapse;margin:var(--space-8) 0;background:var(--color-surface);border-radius:var(--radius-xl);overflow:hidden;box-shadow:var(--shadow-sm)}}
.leverage-table th{{font-family:var(--font-body);font-size:var(--text-xs);font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--color-text-muted);padding:var(--space-4) var(--space-5);border-bottom:1px solid var(--color-divider);text-align:left}}
.leverage-table td{{padding:var(--space-4) var(--space-5);font-size:var(--text-sm);color:var(--color-text);border-bottom:1px solid var(--color-divider)}}
.leverage-table tr:last-child td{{border-bottom:none}}
.leverage-table tbody tr:hover{{background:var(--color-surface-dynamic)}}
.lev-high{{color:#c0392b;font-weight:600}}[data-theme="dark"] .lev-high{{color:#e05244}}
.lev-note{{font-size:var(--text-xs);color:var(--color-text-muted);margin-top:var(--space-2)}}
.stage-pill{{display:inline-flex;align-items:center;font-size:var(--text-xs);font-weight:600;letter-spacing:.04em;padding:.2em .7em;border-radius:var(--radius-md);background:var(--color-primary-subtle);color:var(--color-primary);white-space:nowrap}}
.stage-pill.high{{background:#fde8e8;color:#c0392b}}[data-theme="dark"] .stage-pill.high{{background:#3a1212;color:#e05244}}
.stage-pill.amber{{background:#fef3c7;color:#92400e}}
.stage-pill.blue{{background:#dbeafe;color:#1e40af}}
.stage-pill.purple{{background:#ede9fe;color:#5b21b6}}
.stage-pill.gray{{background:#f3f4f6;color:#374151}}
.det-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:var(--space-6);margin-top:var(--space-8)}}
.det-card{{background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-xl);padding:var(--space-8)}}
.det-direction{{font-size:var(--text-2xl);font-weight:600;line-height:1;margin-bottom:var(--space-3)}}
.det-direction.neg{{color:#c0392b}}[data-theme="dark"] .det-direction.neg{{color:#e05244}}
.det-direction.pos{{color:var(--color-primary)}}
.det-name{{font-size:var(--text-sm);font-weight:600;letter-spacing:.04em;color:var(--color-text);margin-bottom:var(--space-3)}}
.det-desc{{font-size:var(--text-sm);color:var(--color-text-muted);line-height:1.6}}
.det-theory{{font-size:var(--text-xs);color:var(--color-primary);font-weight:500;margin-top:var(--space-3)}}
.usecase-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:var(--space-6);margin-top:var(--space-8)}}
.usecase-card{{background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-xl);padding:var(--space-8)}}
.usecase-card h4{{font-size:var(--text-base);font-weight:600;color:var(--color-text);margin-bottom:var(--space-3);padding-bottom:var(--space-3);border-bottom:2px solid var(--color-primary)}}
.usecase-card p{{font-size:var(--text-sm);color:var(--color-text-muted);line-height:1.6;margin-bottom:var(--space-3)}}
.kpi-row{{display:flex;justify-content:space-between;align-items:center;padding:var(--space-2) 0;border-bottom:1px solid var(--color-divider)}}
.kpi-row:last-of-type{{border-bottom:none}}
.kpi-label{{font-size:var(--text-xs);color:var(--color-text-muted)}}
.kpi-val{{font-size:var(--text-sm);font-weight:600;color:var(--color-text)}}
.kpi-val.green{{color:#16a34a}}
.kpi-val.red{{color:#dc2626}}
.kpi-val.amber{{color:#d97706}}
.authors-section{{padding:clamp(var(--space-16),8vw,var(--space-24)) 0;background:var(--color-bg)}}
.authors-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:var(--space-8);margin-top:var(--space-8)}}
.author-card{{background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-2xl);padding:var(--space-8);position:relative;overflow:hidden}}
.author-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--color-primary)}}
.author-header{{display:flex;align-items:center;gap:var(--space-5);margin-bottom:var(--space-5)}}
.author-photo{{width:80px;height:80px;border-radius:50%;border:2px solid var(--color-primary);object-fit:cover;flex-shrink:0}}
.author-initials{{width:80px;height:80px;border-radius:50%;border:2px solid var(--color-primary);background:var(--color-primary-subtle);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:var(--text-lg);font-weight:600;color:var(--color-primary)}}
.author-role{{font-size:var(--text-xs);font-weight:600;letter-spacing:.1em;color:var(--color-primary);text-transform:uppercase;margin-bottom:var(--space-1)}}
.author-name{{font-family:var(--font-display);font-size:var(--text-xl);color:var(--color-text);line-height:1.1}}
.author-tagline{{font-size:var(--text-sm);color:var(--color-text-muted);line-height:1.6;margin-bottom:var(--space-5)}}
.author-bullets{{display:flex;flex-direction:column;gap:var(--space-2)}}
.author-bullets li{{display:flex;align-items:flex-start;gap:var(--space-3);font-size:var(--text-sm);color:var(--color-text-muted)}}
.author-arrow{{color:var(--color-primary);font-size:.6em;flex-shrink:0;margin-top:.45em}}
.author-divider{{border:none;border-top:1px solid var(--color-divider);margin:var(--space-5) 0}}
.cta-dark{{background:#141312;padding:clamp(var(--space-16),8vw,var(--space-24)) 0;text-align:center}}
.cta-dark h2{{font-size:var(--text-2xl);color:#e8e6e2;margin-bottom:var(--space-5);letter-spacing:-.015em}}
.cta-dark p{{font-size:var(--text-base);color:#7a7872;max-width:52ch;margin-inline:auto;margin-bottom:var(--space-8)}}
footer{{background:var(--color-surface-offset);padding:clamp(var(--space-12),5vw,var(--space-16)) 0 var(--space-8);border-top:1px solid var(--color-divider)}}
.footer-inner{{max-width:var(--content-wide);margin-inline:auto;padding-inline:clamp(var(--space-6),5vw,var(--space-16));display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:var(--space-6)}}
.footer-brand{{display:flex;align-items:center;gap:var(--space-3)}}
.footer-name{{font-weight:600;font-size:var(--text-sm);letter-spacing:.04em}}
.footer-meta{{font-size:var(--text-xs);color:var(--color-text-muted);text-align:right}}
.ibc-bar-wrap{{margin:var(--space-6) 0;border-radius:var(--radius-md);overflow:hidden;height:32px;display:flex}}
.ibc-seg{{display:flex;align-items:center;justify-content:center;font-size:var(--text-xs);font-weight:600;color:#fff}}
.ibc-seg.green{{background:#16a34a;flex:85}}
.ibc-seg.red{{background:#dc2626;flex:15}}
.refs-section{{padding:clamp(var(--space-12),6vw,var(--space-16)) 0;background:var(--color-surface-offset)}}
.refs-inner{{background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-2xl);padding:clamp(var(--space-8),5vw,var(--space-10));margin-top:var(--space-6)}}
.refs-inner h3{{font-size:var(--text-base);font-weight:600;color:var(--color-text);margin-bottom:var(--space-5);padding-bottom:var(--space-3);border-bottom:1px solid var(--color-divider)}}
.ref-item{{font-size:var(--text-xs);color:var(--color-text-muted);margin-bottom:var(--space-3);padding-left:var(--space-5);text-indent:calc(-1 * var(--space-5));line-height:1.6}}
@media(max-width:640px){{.hero h1{{font-size:clamp(2rem,8vw,2.75rem)}}.stats-grid{{grid-template-columns:repeat(2,1fr)}}.authors-grid,.det-grid,.usecase-grid{{grid-template-columns:1fr}}.leverage-table{{font-size:.8rem}}}}
</style>
</head>
<body id="top">
<script>(function(){{var s=localStorage.getItem('lclev-theme')||'light';document.documentElement.setAttribute('data-theme',s);}})();</script>

<!-- NAV -->
<nav class="nav" id="mainNav">
  <a href="#top" class="nav-brand">
    <svg width="36" height="36" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0">
      <rect width="36" height="36" rx="6" fill="#01696f"/>
      <text x="18" y="13" text-anchor="middle" fill="#7dd6d8" font-family="Arial,sans-serif" font-weight="900" font-size="6" letter-spacing="1.5">EOL</text>
      <line x1="6" y1="17" x2="30" y2="17" stroke="#7dd6d8" stroke-width="0.7" opacity="0.7"/>
      <text x="18" y="27" text-anchor="middle" fill="white" font-family="Arial,sans-serif" font-weight="900" font-size="9" letter-spacing="0.5">ABS</text>
    </svg>
    <span class="nav-name">EOLABS</span>
  </a>
  <div class="nav-right">
    <span class="nav-tag">Practitioner's Guide · v3.1</span>
    <button class="theme-btn" id="themeBtn" aria-label="Toggle theme">
      <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
      <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
    </button>
  </div>
</nav>

<!-- HERO -->
<section class="hero" id="hero">
  <div class="container--narrow">
    <div class="hero-pretag">Practitioner's Guide · LifeCycle Leverage Dashboard · 2025</div>
    <h1>Capital at<br><em>Every Table</em></h1>
    <p class="hero-lead">How eight corporate functions — Board, CFO, Treasurer, Risk, Compliance, Investor Relations, Strategy, and Banker — extract actionable capital-structure intelligence from 401 listed Indian companies across 24 years of CMIE Prowess data.</p>
    <div class="hero-actions">
      <a href="#stakeholders" class="btn btn-primary">Jump to My Role →</a>
      <a href="#stage-norms" class="btn btn-secondary">Stage Leverage Norms</a>
    </div>
  </div>
</section>

<!-- STATS STRIP -->
<section class="stats-strip">
  <div class="container">
    <div class="stats-grid">
      <div><span class="stat-number">401</span><span class="stat-label">Listed Indian Firms<br>BSE / NSE</span></div>
      <div><span class="stat-number">8,677</span><span class="stat-label">Firm-Year<br>Observations</span></div>
      <div><span class="stat-number">8</span><span class="stat-label">Dickinson (2011)<br>Life Stages</span></div>
      <div><span class="stat-number">24 yrs</span><span class="stat-label">Data Coverage<br>2001–2024</span></div>
      <div><span class="stat-number">13</span><span class="stat-label">Analytical<br>Modules</span></div>
      <div><span class="stat-number">17</span><span class="stat-label">Dashboard<br>Pages</span></div>
    </div>
  </div>
</section>

<!-- CHAPTER 1: INTRODUCTION -->
<section class="chapter" id="intro">
  <div class="container--narrow">
    <span class="section-label">Why the Lifecycle Lens Matters</span>
    <h2>The same leverage ratio, two very different stories</h2>
    <p class="chapter-lead">A debt-to-asset ratio of 20% means something entirely different for a firm entering Decline than for one in peak Maturity. The LifeCycle Leverage Dashboard makes that difference visible — and actionable.</p>
    <p class="chapter-body">Most capital-structure analysis anchors on sector averages or static ratios. But the Dickinson (2011) lifecycle classification — using the sign patterns of operating, investing, and financing cash flows — reveals a more powerful signal: <em>where</em> a firm sits in its lifecycle explains leverage variation that sector, size, and profitability alone cannot.</p>
    <p class="chapter-body">This guide shows how eight distinct corporate functions use that signal. Every figure comes from the CMIE Prowess thesis panel (2001–2024, 401 firms, 8,677 firm-year observations) as documented in Kumar (2025), reproduced with the thesis-vintage dataset. Scenario outputs — clearly labelled — are model projections, not observed data.</p>
    <div class="callout">
      <p class="callout-text">"Decline-stage firms carry leverage nearly double that of Maturity firms — a structural signal most financial models fail to isolate."</p>
    </div>
    <p class="chapter-body">The panel regression (OLS with Fixed Effects, preferred by Hausman test at p &lt; 0.01) confirms two headline empirical regularities: profitability and leverage move in opposite directions (Pecking Order Theory, Myers 1984), while asset tangibility and leverage move together (Trade-Off Theory, Modigliani &amp; Miller 1963; Rajan &amp; Zingales 1995). Both forces operate simultaneously — and their relative weight shifts across life stages.</p>
  </div>
</section>

<!-- CHAPTER 2: STAGE LEVERAGE NORMS -->
<section class="chapter chapter--alt" id="stage-norms">
  <div class="container--narrow">
    <span class="section-label">Baseline Benchmarks</span>
    <h2>Leverage norms by Dickinson life stage</h2>
    <p class="chapter-lead">Stage-average leverage across all 8,677 firm-year observations, thesis panel, 2001–2024. These are the reference benchmarks used in all peer-percentile calculations throughout the dashboard.</p>
    <table class="leverage-table">
      <thead>
        <tr>
          <th>Life Stage</th>
          <th>Avg Leverage</th>
          <th>Cash-Flow Signature</th>
          <th>Capital-Structure Reading</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><span class="stage-pill high">Decline</span></td>
          <td class="lev-high">37.77%</td>
          <td style="font-size:var(--text-xs);color:var(--color-text-muted)">NCFO −, NCFI +, NCFF −</td>
          <td style="font-size:var(--text-xs);color:var(--color-text-muted)">Debt-overhang; revenues falling faster than debt repays. Highest credit risk.</td>
        </tr>
        <tr>
          <td><span class="stage-pill purple">Startup</span></td>
          <td style="font-weight:600">34.20%</td>
          <td style="font-size:var(--text-xs);color:var(--color-text-muted)">NCFO −, NCFI −, NCFF +</td>
          <td style="font-size:var(--text-xs);color:var(--color-text-muted)">Pre-cashflow; front-loading debt before internal generation begins.</td>
        </tr>
        <tr>
          <td><span class="stage-pill amber">Shakeout 2</span></td>
          <td style="font-weight:600">32.50%</td>
          <td style="font-size:var(--text-xs);color:var(--color-text-muted)">NCFO +, NCFI +, NCFF −</td>
          <td style="font-size:var(--text-xs);color:var(--color-text-muted)">Consolidation; asset disposal while retiring debt.</td>
        </tr>
        <tr>
          <td><span class="stage-pill blue">Growth</span></td>
          <td>29.68%</td>
          <td style="font-size:var(--text-xs);color:var(--color-text-muted)">NCFO +, NCFI −, NCFF +</td>
          <td style="font-size:var(--text-xs);color:var(--color-text-muted)">Debt funds expansion; watch coverage as revenues scale.</td>
        </tr>
        <tr>
          <td><span class="stage-pill gray">Decay</span></td>
          <td>24.19%</td>
          <td style="font-size:var(--text-xs);color:var(--color-text-muted)">NCFO −, NCFI −, NCFF −</td>
          <td style="font-size:var(--text-xs);color:var(--color-text-muted)">All cash flows negative; late-cycle winding down.</td>
        </tr>
        <tr>
          <td><span class="stage-pill">Maturity</span></td>
          <td>18.96%</td>
          <td style="font-size:var(--text-xs);color:var(--color-text-muted)">NCFO +, NCFI −, NCFF −</td>
          <td style="font-size:var(--text-xs);color:var(--color-text-muted)">Conservative baseline; strong cash flows reduce debt reliance. Reference stage in moderation models.</td>
        </tr>
        <tr>
          <td><span class="stage-pill amber">Shakeout 3</span></td>
          <td>16.45%</td>
          <td style="font-size:var(--text-xs);color:var(--color-text-muted)">NCFO −, NCFI +, NCFF +</td>
          <td style="font-size:var(--text-xs);color:var(--color-text-muted)">Post-consolidation survivors emerge leaner; selective deleveraging.</td>
        </tr>
        <tr>
          <td><span class="stage-pill amber">Shakeout 1</span></td>
          <td>15.20%</td>
          <td style="font-size:var(--text-xs);color:var(--color-text-muted)">NCFO +, NCFI +, NCFF +</td>
          <td style="font-size:var(--text-xs);color:var(--color-text-muted)">All CFs positive; early shakeout market leaders separate from weaker peers.</td>
        </tr>
      </tbody>
    </table>
    <p class="lev-note">Source: CMIE Prowess, thesis panel (vintage = <em>thesis</em>), 401 firms, 8,677 firm-year observations, 2001–2024. Leverage = lev1_100 × 100 (total debt / total assets). Stage classification: Dickinson (2011). Kumar (2025, Ch. 5, Table 5.5).</p>
  </div>
</section>

<!-- CHAPTER 3: STAKEHOLDER USE CASES -->
<section class="chapter" id="stakeholders">
  <div class="container--narrow">
    <span class="section-label">Eight Roles, Eight Questions</span>
    <h2>Capital intelligence for every seat at the table</h2>
    <p class="chapter-lead">The dashboard does not speak with one voice. Each corporate function asks a different question — and receives a different answer from the same underlying data.</p>
  </div>
</section>

<!-- USE CASE 1: BOARD -->
<section class="chapter chapter--alt" id="uc-board">
  <div class="container--narrow">
    <span class="section-label">Use Case 1 · Board of Directors</span>
    <h2>Perpetual Maturity as a governance signal</h2>
    <p class="chapter-lead">Asian Paints Ltd (NSE: ASIANPAINT) is the only firm in the 401-company panel with an unbroken 24-year Maturity classification — an extraordinary balance-sheet discipline story told entirely through cash-flow patterns.</p>
    <p class="chapter-body">From 2001 to 2024, Asian Paints' operating, investing, and financing cash flows consistently matched the Dickinson Maturity signature (NCFO positive, NCFI negative, NCFF negative) in every single year. The Stage KPI Dashboard and Stage Transition module confirm zero deviation across the full thesis panel. This makes Asian Paints an internally consistent reference point for benchmarking balance-sheet conservatism.</p>
    <p class="chapter-body">Leverage tells a compelling narrative within this stable lifecycle. Starting at <strong>25.66%</strong> in 2001, Asian Paints systematically retired debt while growing revenues. By 2018, leverage had fallen to a trough of <strong>0.10%</strong> — near-zero external debt — before rising modestly to <strong>4.44%</strong> in 2024, likely reflecting strategic working-capital needs. At every point, the firm remained well below the Maturity-stage panel median of <strong>18.96%</strong>.</p>
    <div class="callout">
      <p class="callout-text">"Asian Paints: 24 consecutive years of Maturity. Leverage fell from 25.66% (2001) to 0.10% (2018) — then rose only to 4.44% (2024). Stage-median headroom: 14.52 percentage points."</p>
    </div>
    <p class="chapter-body">Boards use the Peer Benchmarking module to monitor whether management is maintaining this conservative posture relative to stage-peers. The Stage Transition module provides the annual re-classification — a board-level KPI that flags the moment a firm's cash-flow signature begins shifting out of Maturity before the income statement shows any distress.</p>
    <table class="leverage-table">
      <thead><tr><th>Year</th><th>Life Stage</th><th>Leverage</th><th>Maturity-Stage Median (Panel)</th></tr></thead>
      <tbody>
        <tr><td>2001</td><td><span class="stage-pill">Maturity</span></td><td>25.66%</td><td>18.96%</td></tr>
        <tr><td>2010</td><td><span class="stage-pill">Maturity</span></td><td>~10% (declining)</td><td>18.96%</td></tr>
        <tr><td>2018</td><td><span class="stage-pill">Maturity</span></td><td style="color:#16a34a;font-weight:600">0.10% (trough)</td><td>18.96%</td></tr>
        <tr><td>2024</td><td><span class="stage-pill">Maturity</span></td><td>4.44%</td><td>18.96%</td></tr>
      </tbody>
    </table>
    <p class="lev-note">Source: CMIE Prowess, thesis panel, 2001–2024. Asian Paints classified Maturity in all 24 years per Dickinson (2011). Kumar (2025, Ch. 5).</p>
  </div>
</section>

<!-- USE CASE 2: CFO -->
<section class="chapter" id="uc-cfo">
  <div class="container--narrow">
    <span class="section-label">Use Case 2 · Chief Financial Officer</span>
    <h2>From distress to recovery — reading leverage through a stage lens</h2>
    <p class="chapter-lead">Tata Motors Ltd (NSE: TATAMOTORS) illustrates how stage-adjusted peer benchmarking reveals a capital-structure story that aggregate ratios alone obscure: a severe interest-coverage crisis followed by a disciplined recovery.</p>
    <p class="chapter-body">In 2024, Tata Motors is classified as <span class="stage-pill amber">Shakeout 3</span> by the Dickinson cash-flow methodology. Its leverage of <strong>20.29%</strong> places it at the <strong>86th percentile</strong> among its 56 Shakeout-3 stage-peers in the same year — meaning 86% of same-stage peers carry less debt. Profitability of <strong>18.12%</strong> ranks at the 62nd percentile. Tangibility stands at <strong>20.51%</strong>.</p>
    <p class="chapter-body">The more important story lies in the interest-coverage trajectory. Coverage of <strong>5.00×</strong> in 2024 — calculated as PBIT / Interest — follows a severe distress episode: coverage fell to <strong>−0.08×</strong> in 2021 (PBIT turned negative during the COVID-demand shock and JLR restructuring) and recovered only partially to <strong>0.45×</strong> in 2022 before crossing back above 1.0× in 2023. The Econometrics Lab flags 2021 and 2022 as IBC-amber/red years for Tata Motors.</p>
    <div class="callout">
      <p class="callout-text">"Tata Motors interest coverage: −0.08× (2021) → 0.45× (2022) → 5.00× (2024). The Pecking Order predicts that this profitability recovery, if sustained, will drive leverage toward the Shakeout-3 median of 16.45%."</p>
    </div>
    <p class="chapter-body">CFOs use the OLS Scenario module to project the leverage reduction achievable through retained-earnings accumulation. The panel coefficient β(profitability) = −0.187 (p &lt; 0.01) implies that each percentage-point rise in profitability reduces leverage by approximately 0.19 percentage points, holding tangibility and firm size constant — a model-based trajectory consistent with Myers (1984) Pecking Order predictions.</p>
    <table class="leverage-table">
      <thead><tr><th>Year</th><th>Stage</th><th>Leverage</th><th>Interest Coverage</th><th>IBC Signal</th></tr></thead>
      <tbody>
        <tr><td>2021</td><td><span class="stage-pill amber">Shakeout 3</span></td><td class="lev-high">—</td><td style="color:#dc2626;font-weight:600">−0.08×</td><td style="font-size:var(--text-xs);color:#dc2626">Red (PBIT negative)</td></tr>
        <tr><td>2022</td><td><span class="stage-pill amber">Shakeout 3</span></td><td class="lev-high">—</td><td style="color:#d97706;font-weight:600">0.45×</td><td style="font-size:var(--text-xs);color:#d97706">Amber (≤ 1.5×)</td></tr>
        <tr><td>2024</td><td><span class="stage-pill amber">Shakeout 3</span></td><td>20.29%</td><td style="color:#16a34a;font-weight:600">5.00×</td><td style="font-size:var(--text-xs);color:#16a34a">Clear</td></tr>
        <tr><td colspan="2" style="font-size:var(--text-xs);color:var(--color-text-muted)">Peer rank (2024, 56 Shakeout-3 peers)</td><td style="color:#d97706;font-weight:600">86th pct</td><td>62nd pct (profitability)</td><td>—</td></tr>
      </tbody>
    </table>
    <p class="lev-note">Source: CMIE Prowess, thesis panel, 2001–2024. Coverage = pbit / interest_amt. IBC thresholds: amber ≤ 1.5×, red ≤ 1.0×. Kumar (2025, Ch. 6); Rajan &amp; Zingales (1995).</p>
  </div>
</section>

<!-- USE CASE 3: TREASURER -->
<section class="chapter chapter--alt" id="uc-treasurer">
  <div class="container--narrow">
    <span class="section-label">Use Case 3 · Group Treasurer</span>
    <h2>Quantifying headroom — how much more can we borrow?</h2>
    <p class="chapter-lead">Bajaj Auto Ltd (NSE: BAJAJ-AUTO) exemplifies the near-zero-debt posture of a Maturity-stage firm with exceptional cash generation — creating precisely the kind of debt capacity question a Group Treasurer must answer before any new issuance.</p>
    <p class="chapter-body">In 2024, Bajaj Auto is classified as <span class="stage-pill">Maturity</span> with leverage of <strong>2.79%</strong>. Among its 244 Maturity-stage firm-year peers across the thesis panel, this places it at the <strong>39th percentile</strong> — not the lowest, because many near-zero-debt FMCG and IT firms populate this cohort, pushing the distribution lower than the stage mean. The critical figure is headroom: <strong>16.17 percentage points</strong> to the Maturity-stage panel median of 18.96%.</p>
    <p class="chapter-body">Interest coverage of <strong>141.09×</strong> (PBIT / Interest, 2024) confirms exceptional debt-servicing capacity. Profitability stands at <strong>29.85%</strong> — 85th percentile among Maturity peers — and tangibility at <strong>9.17%</strong>. The Peer Benchmarking module tracks these rankings in real time as annual CMIE data updates roll in.</p>

    <div class="scenario-callout">
      <div class="scenario-callout-label">⚠ Scenario Illustration — Not Observed Data</div>
      <p>The Scenario OLS module applies the panel coefficients [β(profitability) = −0.187, β(tangibility) = +0.142, both p &lt; 0.01] to project leverage under different financing decisions. If Bajaj Auto were to issue ₹5,000 Cr of NCDs — adding roughly 4–6 percentage points to leverage depending on total assets in the year of issuance — the resulting leverage of approximately 7–9% would remain well below the Maturity-stage median of 18.96% and far below the Decline-stage average of 37.77%. This is a model projection using thesis-panel OLS coefficients; actual leverage movement depends on total asset base and interest capitalisation.</p>
    </div>

    <div class="callout">
      <p class="callout-text">"Bajaj Auto: leverage 2.79%, coverage 141.09×, headroom to stage median 16.17 pp. Stage-peer distribution at 39th percentile — the Treasurer has substantial unexercised debt capacity by any panel benchmark."</p>
    </div>
    <table class="leverage-table">
      <thead><tr><th>Metric</th><th>Bajaj Auto (2024)</th><th>Maturity-Stage Median (Panel)</th></tr></thead>
      <tbody>
        <tr><td>Leverage</td><td style="color:#16a34a;font-weight:600">2.79%</td><td>18.96%</td></tr>
        <tr><td>Headroom to median</td><td style="color:#16a34a;font-weight:600">16.17 pp</td><td>—</td></tr>
        <tr><td>Peer leverage percentile (244 Maturity peers)</td><td>39th pct</td><td>50th pct (by definition)</td></tr>
        <tr><td>Profitability</td><td style="color:#16a34a;font-weight:600">29.85%</td><td>~18%</td></tr>
        <tr><td>Tangibility</td><td>9.17%</td><td>~25%</td></tr>
        <tr><td>Interest Coverage</td><td style="color:#16a34a;font-weight:600">141.09×</td><td>~8×</td></tr>
      </tbody>
    </table>
    <p class="lev-note">Source: CMIE Prowess, thesis panel, 2001–2024. β coefficients from Kumar (2025, Ch. 6 Table 6.2). Myers (1984) Pecking Order; scenario output is illustrative.</p>
  </div>
</section>

<!-- USE CASE 4: RISK -->
<section class="chapter" id="uc-risk">
  <div class="container--narrow">
    <span class="section-label">Use Case 4 · Chief Risk Officer</span>
    <h2>IBC early-warning — 120 firms, two cohorts, one survival question</h2>
    <p class="chapter-lead">The Econometrics Lab provides a systematic IBC stress screen: every firm-year where interest coverage falls below 1.5× (amber) or 1.0× (red) is flagged. Across the thesis panel's 2016–2021 window, 120 firms triggered at least one alert — and their subsequent trajectories reveal a stark divergence.</p>
    <p class="chapter-body">Of the 120 firms entering an amber or red coverage alert in at least one year between 2016 and 2021, <strong>102 (85%)</strong> recovered to above-threshold coverage by 2024. The remaining <strong>18 firms (15%)</strong> did not. CROs use the Econometrics Lab to maintain this dashboard in real time, tracking which firms remain in distress and which have exited. The coverage formula is straightforward: <em>pbit / interest_amt</em> from CMIE Prowess financials, applied uniformly across all 8,677 firm-years.</p>

    <div class="ibc-bar-wrap">
      <div class="ibc-seg green">102 firms recovered (85%)</div>
      <div class="ibc-seg red">18 did not (15%)</div>
    </div>

    <p class="chapter-body">The Stage Transition module adds a second risk dimension: forward-looking transition probabilities. A firm currently classified as Shakeout-3 transitions to <strong>Maturity in 48.5%</strong> of cases in the following year — but migrates to <strong>Decline in only 2.0%</strong> of cases. This allows risk teams to build probability-weighted exposure estimates rather than binary pass/fail credit screens. The complete 8×8 transition matrix is available in the dashboard for all life stages.</p>
    <div class="callout">
      <p class="callout-text">"120 firms entered IBC amber/red alert 2016–2021. 85% recovered. The 15% that did not were identifiable by stage: Decline and Startup firms had systematically lower recovery rates than Shakeout firms in the same cohort."</p>
    </div>
    <table class="leverage-table">
      <thead><tr><th>Metric</th><th>Value</th><th>Panel Source</th></tr></thead>
      <tbody>
        <tr><td>Firms with amber/red coverage (2016–2021)</td><td style="font-weight:600">120</td><td style="font-size:var(--text-xs);color:var(--color-text-muted)">CMIE Prowess, thesis panel</td></tr>
        <tr><td>Recovered by 2024</td><td style="color:#16a34a;font-weight:600">102 (85%)</td><td style="font-size:var(--text-xs);color:var(--color-text-muted)">Coverage &gt; 1.5× in 2024</td></tr>
        <tr><td>Did not recover</td><td style="color:#dc2626;font-weight:600">18 (15%)</td><td style="font-size:var(--text-xs);color:var(--color-text-muted)">Coverage ≤ 1.5× in 2024</td></tr>
        <tr><td>Shakeout-3 → Maturity (1-yr probability)</td><td style="color:#16a34a;font-weight:600">48.5%</td><td style="font-size:var(--text-xs);color:var(--color-text-muted)">Stage Transition module</td></tr>
        <tr><td>Shakeout-3 → Decline (1-yr probability)</td><td>2.0%</td><td style="font-size:var(--text-xs);color:var(--color-text-muted)">Stage Transition module</td></tr>
        <tr><td>Amber threshold</td><td>≤ 1.5× (PBIT / Interest)</td><td style="font-size:var(--text-xs);color:var(--color-text-muted)">IBC / RBI benchmark</td></tr>
      </tbody>
    </table>
    <p class="lev-note">Source: CMIE Prowess, thesis panel, 2001–2024. Dickinson (2011). Kumar (2025, Ch. 7). IBC framework thresholds per RBI guidance.</p>
  </div>
</section>

<!-- USE CASE 5: COMPLIANCE -->
<section class="chapter chapter--alt" id="uc-compliance">
  <div class="container--narrow">
    <span class="section-label">Use Case 5 · Compliance &amp; Governance</span>
    <h2>Panel-calibrated benchmarks for debt governance</h2>
    <p class="chapter-lead">The Econometrics Lab OLS regression (HC1 robust standard errors, Fixed Effects confirmed by Hausman test at p &lt; 0.01) provides the empirically calibrated relationship between capital-structure determinants and leverage — the reference benchmark for compliance reviews of debt covenants and management plans.</p>
    <p class="chapter-body">Two coefficients anchor all compliance reviews. The profitability coefficient β = <strong>−0.187</strong> (p &lt; 0.01) confirms the Pecking Order: each percentage-point rise in profitability is associated with a 0.187 percentage-point reduction in leverage, controlling for tangibility, firm size, and year fixed effects. This means a management team claiming that profitability improvement will reduce leverage is making a claim fully consistent with the panel evidence — compliance teams can use this coefficient to challenge or validate proposed debt-reduction timelines.</p>
    <p class="chapter-body">The tangibility coefficient β = <strong>+0.142</strong> (p &lt; 0.01) confirms the Trade-Off Theory collateral channel: firms with more fixed assets carry more debt. For compliance reviews of capital expenditure-driven leverage increases, this coefficient provides a basis for assessing whether a proposed leverage rise is structurally warranted by the asset base, or represents a deviation from panel norms.</p>
    <div class="det-grid">
      <div class="det-card">
        <div class="det-direction neg">−0.187***</div>
        <div class="det-name">Profitability → Leverage</div>
        <div class="det-desc">Each 1 pp rise in profitability (EBIT / Total Assets) reduces leverage by 0.187 pp, holding tangibility, firm size, and year fixed effects constant. Significant at p &lt; 0.01 across OLS, FE, and GMM specifications.</div>
        <div class="det-theory">Pecking Order Theory · Myers (1984)</div>
      </div>
      <div class="det-card">
        <div class="det-direction pos">+0.142***</div>
        <div class="det-name">Tangibility → Leverage</div>
        <div class="det-desc">Each 1 pp rise in asset tangibility (Net Fixed Assets / Total Assets) raises leverage by 0.142 pp. Asset-rich firms attract more debt — collateral unlocks the borrowing channel consistent with Trade-Off Theory.</div>
        <div class="det-theory">Trade-Off Theory · Modigliani &amp; Miller (1963); Rajan &amp; Zingales (1995)</div>
      </div>
      <div class="det-card">
        <div class="det-direction" style="font-size:var(--text-xl)">0.412</div>
        <div class="det-name">Panel R² (Fixed Effects)</div>
        <div class="det-desc">Fixed Effects OLS explains 41.2% of within-firm leverage variation — a robust fit for a panel regression with 8,677 firm-year observations. Hausman test confirms FE over Random Effects (p &lt; 0.01).</div>
        <div class="det-theory">Kumar (2025, Ch. 6, Table 6.2)</div>
      </div>
    </div>
    <p class="lev-note">Source: Kumar (2025, Ch. 6); Myers (1984); Modigliani &amp; Miller (1963); Rajan &amp; Zingales (1995). *** = p &lt; 0.01.</p>
  </div>
</section>

<!-- USE CASE 6: INVESTOR RELATIONS -->
<section class="chapter" id="uc-ir">
  <div class="container--narrow">
    <span class="section-label">Use Case 6 · Investor Relations</span>
    <h2>Narrating structural advantage to debt and equity investors</h2>
    <p class="chapter-lead">Infosys Ltd (NSE: INFY) spent 18 of its 24 years in Maturity, 5 in Shakeout-3, and 1 in Growth — one of the most lifecycle-stable large-cap firms in the panel. IR teams translate this stability into a data-consistent investor narrative.</p>
    <p class="chapter-body">In 2024, Infosys carries leverage of <strong>3.20%</strong> — the 40th percentile among its 244 Maturity-stage peers in the thesis panel. That ranking appears modest until set against its profitability: <strong>34.22%</strong> places it at the <strong>95th percentile</strong> in the same cohort. The combination — very low leverage, very high profitability, and interest coverage of <strong>134.09×</strong> — constitutes a textbook Pecking Order posture (Myers 1984): a firm that self-funds from retained earnings and has no need of external debt at scale.</p>
    <p class="chapter-body">The Stage Transition module provides the lifecycle narrative: across 24 years of data, the Dickinson classification returned Maturity 18 times (75%), Shakeout-3 five times (21%), and Growth once (4%). For debt investors, this consistency is a structural signal that Infosys' cash flows are durable, not cyclical. For equity investors, the 95th-percentile profitability ranking within stage confirms earnings quality relative to peers in the same lifecycle position.</p>
    <div class="callout">
      <p class="callout-text">"Infosys: 95th-percentile profitability, 40th-percentile leverage, 134.09× interest coverage. The Knowledge Graph confirms profitability as the dominant deleveraging force for this firm — consistent with Pecking Order predictions across all 24 years."</p>
    </div>
    <table class="leverage-table">
      <thead><tr><th>Metric</th><th>Infosys 2024</th><th>Peer Percentile (244 Maturity peers)</th></tr></thead>
      <tbody>
        <tr><td>Life Stage</td><td><span class="stage-pill">Maturity</span></td><td>—</td></tr>
        <tr><td>Leverage</td><td>3.20%</td><td>40th pct</td></tr>
        <tr><td>Profitability</td><td style="color:#16a34a;font-weight:600">34.22%</td><td style="color:#16a34a;font-weight:600">95th pct</td></tr>
        <tr><td>Interest Coverage</td><td style="color:#16a34a;font-weight:600">134.09×</td><td>95th pct+</td></tr>
        <tr><td>Years in Maturity (2001–2024)</td><td style="color:#16a34a;font-weight:600">18 / 24 (75%)</td><td>—</td></tr>
        <tr><td>Years in Shakeout-3</td><td>5 / 24 (21%)</td><td>—</td></tr>
        <tr><td>Years in Growth</td><td>1 / 24 (4%)</td><td>—</td></tr>
      </tbody>
    </table>
    <p class="lev-note">Source: CMIE Prowess, thesis panel, 2001–2024. Dickinson (2011) classification. Kumar (2025, Ch. 5). Myers (1984).</p>
  </div>
</section>

<!-- USE CASE 7: STRATEGY -->
<section class="chapter chapter--alt" id="uc-strategy">
  <div class="container--narrow">
    <span class="section-label">Use Case 7 · Corporate Strategy</span>
    <h2>Reading a capital-cycle transformation through Dickinson cash-flow patterns</h2>
    <p class="chapter-lead">Reliance Industries Ltd (NSE: RELIANCE) executed one of the largest capital-cycle transformations in Indian corporate history between 2019 and 2024. The Dickinson lifecycle classification makes every phase of that transformation visible — in real time, from cash-flow data alone.</p>
    <p class="chapter-body">The Jio and retail investment wave is visible as a multi-year Growth-stage classification (NCFO +, NCFI −, NCFF +): debt-funded expansion with operating surpluses reinvested. In 2019, NCFI stood at <strong>−₹53,949 Cr</strong> — massive investing outflows absorbing capital at scale. In 2020, NCFI reached <strong>−₹1,43,625 Cr</strong>, the largest single-year investing cash outflow in the entire 401-company thesis panel, funded in part by financing inflows of <strong>+₹70,767 Cr</strong>. Both years classify as Growth under the Dickinson schema.</p>
    <p class="chapter-body">In 2021, the Jio fundraise (₹1.52 Lakh Cr from global investors, rights issue, and strategic partners) transformed the financing structure. NCFO turned negative (−₹512 Cr), NCFI flipped positive (+₹74,257 Cr, reflecting asset monetisation), and NCFF turned negative (−₹76,657 Cr, reflecting debt and liability reduction). This combination — all three CFs with unusual sign pattern — classifies as <span class="stage-pill gray">Decay</span> under Dickinson, reflecting the temporary disruption of the transformation. By 2022–2024, Reliance settled back into <span class="stage-pill">Maturity</span> with leverage stabilising around <strong>~22%</strong>.</p>
    <div class="callout">
      <p class="callout-text">"Reliance 2020: NCFI = −₹1,43,625 Cr — the largest single-year investing outflow in the 401-company panel. The Dickinson classification captured this inflection point from cash-flow data alone, two years before it appeared in debt ratios."</p>
    </div>
    <table class="leverage-table">
      <thead><tr><th>Year</th><th>Dickinson Stage</th><th>NCFO</th><th>NCFI</th><th>NCFF</th></tr></thead>
      <tbody>
        <tr><td>2019</td><td><span class="stage-pill blue">Growth</span></td><td>+</td><td style="color:#dc2626;font-weight:600">−₹53,949 Cr</td><td>+</td></tr>
        <tr><td>2020</td><td><span class="stage-pill blue">Growth</span></td><td>+</td><td style="color:#dc2626;font-weight:600">−₹1,43,625 Cr</td><td style="color:#16a34a;font-weight:600">+₹70,767 Cr</td></tr>
        <tr><td>2021</td><td><span class="stage-pill gray">Decay</span></td><td style="color:#dc2626;font-weight:600">−₹512 Cr</td><td style="color:#16a34a;font-weight:600">+₹74,257 Cr</td><td style="color:#dc2626;font-weight:600">−₹76,657 Cr</td></tr>
        <tr><td>2022–2024</td><td><span class="stage-pill">Maturity</span></td><td>+</td><td>−</td><td>−</td></tr>
      </tbody>
    </table>
    <p class="lev-note">Source: CMIE Prowess, thesis panel, 2001–2024. Cash flows in ₹ Cr. Dickinson (2011) classification. Kumar (2025, Ch. 5, Table 5.9).</p>
  </div>
</section>

<!-- USE CASE 8: BANKER -->
<section class="chapter" id="uc-banker">
  <div class="container--narrow">
    <span class="section-label">Use Case 8 · Investment Banker / Lender</span>
    <h2>Same stage, different collateral — why peer benchmarking outperforms sector averages</h2>
    <p class="chapter-lead">Maruti Suzuki (NSE: MARUTI) and Wipro (NSE: WIPRO) both sit in Maturity (2023) — yet their capital-structure profiles diverge in ways that matter acutely for credit structuring and underwriting decisions.</p>
    <p class="chapter-body">In 2023, Maruti carries leverage of <strong>1.53%</strong>, tangibility of <strong>21.30%</strong>, and interest coverage of <strong>55.92×</strong>. Wipro carries leverage of <strong>7.36%</strong>, tangibility of <strong>10.21%</strong>, and coverage of <strong>12.71×</strong>. Both are well below the Maturity-stage panel median leverage of 18.96%, signalling substantial unexercised debt capacity — but the <em>type</em> of capacity differs. Maruti's tangibility (21.30%) gives it a structural collateral advantage: per the panel Trade-Off coefficient β(tangibility) = +0.142 (Econometrics Lab), asset-rich firms attract more debt from lenders willing to underwrite against fixed assets.</p>
    <p class="chapter-body">The Interaction Effects module provides a further nuance: the Stage Moderation OLS reveals that tangibility's marginal effect on leverage (dLeverage/dTangibility) differs significantly across life stages. In Maturity — the reference stage — the marginal effect equals the base coefficient. But at Shakeout-3, the interaction term modifies this effect, computed with delta-method standard errors. Bankers use this module to calibrate collateral-coverage requirements by stage, rather than applying a single ratio across the lifecycle.</p>
    <div class="callout">
      <p class="callout-text">"Maruti tangibility 21.30% vs Wipro 10.21% — same stage, same year, but 11 pp more collateral gives Maruti a structurally different debt capacity profile. The Trade-Off coefficient (β = +0.142) translates this into a 1.56 pp leverage premium."</p>
    </div>
    <table class="leverage-table">
      <thead><tr><th>Metric</th><th>Maruti (2023)</th><th>Wipro (2023)</th><th>Maturity Median (Panel)</th></tr></thead>
      <tbody>
        <tr><td>Life Stage</td><td><span class="stage-pill">Maturity</span></td><td><span class="stage-pill">Maturity</span></td><td>—</td></tr>
        <tr><td>Leverage</td><td style="color:#16a34a;font-weight:600">1.53%</td><td>7.36%</td><td>18.96%</td></tr>
        <tr><td>Tangibility</td><td style="color:#16a34a;font-weight:600">21.30%</td><td>10.21%</td><td>~25%</td></tr>
        <tr><td>Interest Coverage</td><td style="color:#16a34a;font-weight:600">55.92×</td><td>12.71×</td><td>~8×</td></tr>
        <tr><td>Headroom to stage median</td><td>17.43 pp</td><td>11.60 pp</td><td>—</td></tr>
      </tbody>
    </table>
    <p class="lev-note">Source: CMIE Prowess, thesis panel, 2001–2024. Rajan &amp; Zingales (1995). Modigliani &amp; Miller (1963). Kumar (2025, Ch. 6). β(tangibility) = +0.142 (Econometrics Lab, HC1 robust SEs, FE OLS).</p>
  </div>
</section>

<!-- CHAPTER: REFERENCES -->
<section class="refs-section" id="references">
  <div class="container--narrow">
    <span class="section-label">Data &amp; Literature Sources</span>
    <h2>References</h2>
    <div class="refs-inner">
      <h3>Primary Data Sources</h3>
      <p class="ref-item">CMIE (2025). <em>Prowess company financial database</em>. Centre for Monitoring Indian Economy Pvt Ltd, Mumbai. Thesis panel: 401 BSE/NSE-listed Indian firms, 8,677 firm-year observations, 2001–2024 (vintage = <em>thesis</em>). All figures in this document sourced from this vintage unless stated otherwise.</p>
      <p class="ref-item">Kumar, S. (2025). <em>Capital structure determinants and corporate life cycle: Evidence from Indian listed firms</em>. PhD thesis, University of Delhi, Faculty of Management Studies. All OLS, Fixed Effects, GMM, and stage moderation coefficients reproduced from the thesis-vintage panel.</p>
    </div>
    <div class="refs-inner" style="margin-top:var(--space-5)">
      <h3>Academic Literature</h3>
      <p class="ref-item">Dickinson, V. (2011). Cash flow patterns as a proxy for firm life cycle. <em>The Accounting Review</em>, 86(6), 1969–1994. Life-stage classification scheme applied throughout: Startup, Growth, Maturity, Shakeout 1–3, Decline, Decay based on NCFO / NCFI / NCFF sign patterns.</p>
      <p class="ref-item">Myers, S. C. (1984). The capital structure puzzle. <em>The Journal of Finance</em>, 39(3), 574–592. Pecking Order Theory; β(profitability) = −0.187 (p &lt; 0.01) in Kumar (2025, Table 6.2).</p>
      <p class="ref-item">Modigliani, F., &amp; Miller, M. H. (1963). Corporate income taxes and the cost of capital: A correction. <em>The American Economic Review</em>, 53(3), 433–443. Tax shield rationale for the Trade-Off Theory collateral channel.</p>
      <p class="ref-item">Rajan, R. G., &amp; Zingales, L. (1995). What do we know about capital structure? Some evidence from international data. <em>The Journal of Finance</em>, 50(5), 1421–1460. Tangibility as a positive leverage determinant; β(tangibility) = +0.142 (p &lt; 0.01) in Kumar (2025, Table 6.2).</p>
      <p class="ref-item">Frank, M. Z., &amp; Goyal, V. K. (2009). Capital structure decisions: Which factors are reliably important? <em>Financial Management</em>, 38(1), 1–37. Variable selection benchmarks for profitability, tangibility, firm size, and tax rate.</p>
      <p class="ref-item">DeAngelo, H., &amp; Roll, R. (2015). How stable are corporate capital structures? <em>The Journal of Finance</em>, 70(1), 373–418. Lifecycle stability and mean-reversion in leverage — motivation for the Stage Transition matrix.</p>
    </div>
  </div>
</section>

<!-- CTA -->
<section class="cta-dark" id="contact">
  <div class="container--narrow">
    <h2>Ready to put your data to work?</h2>
    <p>The LifeCycle Leverage Dashboard is available to institutional subscribers. Contact the research team for a live demonstration, panel data access, or a Board-export deck for your company.</p>
    <a href="mailto:drbhatiasanjay@gmail.com" class="btn btn-primary">Request Access →</a>
  </div>
</section>

<!-- AUTHORS -->
<section class="authors-section" id="authors">
  <div class="container--narrow">
    <span class="section-label">Research Team</span>
    <h2>About the authors</h2>
    <div class="authors-grid">
      <div class="author-card">
        <div class="author-header">
          <img src="data:image/webp;base64,{AUTHOR}" alt="Dr Sanjay Bhatia" class="author-photo"/>
          <div>
            <div class="author-role">Co-founder, EOLABS</div>
            <div class="author-name">Dr Sanjay K. Bhatia</div>
          </div>
        </div>
        <p class="author-tagline">Research collaborator; responsible for dashboard architecture, CMIE data engineering, econometric modelling pipeline, and ML integration.</p>
        <ul class="author-bullets">
          <li><span class="author-arrow">▶</span>Dashboard design and full-stack engineering</li>
          <li><span class="author-arrow">▶</span>CMIE Prowess API integration and vintage management</li>
          <li><span class="author-arrow">▶</span>Econometric and ML modelling — OLS, FE, GMM, SHAP</li>
          <li><span class="author-arrow">▶</span>Interactive Plotly visualisations and scenario modelling</li>
        </ul>
        <hr class="author-divider"/>
        <div style="font-size:var(--text-xs);color:var(--color-text-muted)">
          Contact: <a href="mailto:drbhatiasanjay@gmail.com" style="color:var(--color-primary)">drbhatiasanjay@gmail.com</a>
        </div>
      </div>
      <div class="author-card">
        <div class="author-header">
          <div class="author-initials">SK</div>
          <div>
            <div class="author-role">Principal Investigator</div>
            <div class="author-name">Prof Surendra Kumar</div>
          </div>
        </div>
        <p class="author-tagline">Faculty of Management Studies, University of Delhi. PhD thesis: <em>Capital Structure Determinants and Corporate Life Cycle: Evidence from Indian Listed Firms</em> (2025). Nifty 500 panel, 401 companies, 2001–2024.</p>
        <ul class="author-bullets">
          <li><span class="author-arrow">▶</span>Thesis research design and hypothesis development</li>
          <li><span class="author-arrow">▶</span>Stata econometric analysis — OLS, FE, RE, GMM, IV/2SLS</li>
          <li><span class="author-arrow">▶</span>Dickinson (2011) life-cycle classification applied to Indian context</li>
          <li><span class="author-arrow">▶</span>Pecking Order and Trade-Off theory empirical tests</li>
        </ul>
        <hr class="author-divider"/>
        <div style="font-size:var(--text-xs);color:var(--color-text-muted)">
          Faculty of Management Studies · University of Delhi
        </div>
      </div>
    </div>
    <div style="margin-top:var(--space-8);padding:var(--space-5) var(--space-6);background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-lg);font-size:var(--text-sm);color:var(--color-text-muted);text-align:center">
      All figures and panel statistics cited in this document are sourced from the CMIE Prowess thesis-vintage dataset (vintage = <em>thesis</em>, 2001–2024) as reproduced in Kumar (2025). Scenario outputs are model projections labelled accordingly and do not represent observed data.
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <div class="footer-inner">
    <div class="footer-brand">
      <svg width="28" height="28" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg">
        <rect width="36" height="36" rx="6" fill="#01696f"/>
        <text x="18" y="13" text-anchor="middle" fill="#7dd6d8" font-family="Arial,sans-serif" font-weight="900" font-size="6" letter-spacing="1.5">EOL</text>
        <line x1="6" y1="17" x2="30" y2="17" stroke="#7dd6d8" stroke-width="0.7" opacity="0.7"/>
        <text x="18" y="27" text-anchor="middle" fill="white" font-family="Arial,sans-serif" font-weight="900" font-size="9" letter-spacing="0.5">ABS</text>
      </svg>
      <span class="footer-name">EOLABS · LifeCycle Leverage Dashboard</span>
    </div>
    <div class="footer-meta">
      Practitioner's Guide v3.1 · © 2025 EOLABS · Academic use only<br/>
      All data: CMIE Prowess, thesis panel (vintage = <em>thesis</em>), 2001–2024 · Kumar (2025)
    </div>
  </div>
</footer>

<script>
var btn=document.getElementById('themeBtn');
var nav=document.getElementById('mainNav');
btn.addEventListener('click',function(){{
  var t=document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark';
  document.documentElement.setAttribute('data-theme',t);
  localStorage.setItem('lclev-theme',t);
}});
window.addEventListener('scroll',function(){{
  nav.classList.toggle('scrolled',window.scrollY>10);
}});
</script>
</body>
</html>"""

out = 'profsur-ebook-v3.1.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(HTML)

size_kb = len(HTML.encode('utf-8')) / 1024
print(f"Written: {out}  ({size_kb:.1f} KB)")
