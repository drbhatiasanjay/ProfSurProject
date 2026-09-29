# AI Financial Assistant: Master Demo Walkthrough Strategy

## 1. Executive Summary & Objective
To produce an institutional-grade, broadcast-ready master video walkthrough of the **AI Financial Assistant** (`pages/19_ai_assistant.py`) demonstrating empirical corporate finance decision intelligence across **all 5 featured enterprise archetypes**, panel econometrics (`xtreg`), and literature benchmarking.

---

## 2. Core Operational Pillars

### Pillar 1: Deterministic 4-Phase Synchronization Strategy
To eliminate premature narration and ensure authentic visual credibility, every interactive scene follows a strict state machine:

```
[Phase 1: Input & Intent]
  ├─ Audio: Sentence 0 plays (introduces corporate context & query).
  └─ Visual: Live typing into `stChatInputTextArea` @ 15ms/char, then Enter is pressed.

[Phase 2: Authentic Working State & Silence]
  ├─ Audio: 100% SILENCE (Zero voiceover, zero talking).
  ├─ Visual: Native Streamlit `Working...` reasoning trace spinner visible.
  └─ Engine: Script dynamically awaits `Working...` detachment (exact Δt measured).

[Phase 3: Viewport Reset to Top (y=0)]
  ├─ Visual: Immediately executes multi-container `scrollTo({top: 0, behavior: 'instant'})`.
  └─ Result: Executive Hypothesis badge, Dickinson Life Stage, and query header in full view.

[Phase 4: Commentary, CFO Recommendations & Focal Scroll]
  ├─ Audio: Sentences 1..N play sequentially (narrating analysis & recommendations).
  ├─ Subtitles: Granular sentence-level captions rendered in upper white space (`MarginV=90`).
  └─ Visual: Smooth paced focal scrolling down through CFO Strategy Tables & Plotly charts.
```

---

## 3. Scene Breakdown & Narrative Architecture

| Scene # | Identifier | Type | Focus / Archetype | Key Visual Deliverables |
|:---:|---|---|---|---|
| **1** | `scene1_title_card` | Static Card | Institutional Attribution | Title overlay, Dr. Sanjay Bhatia & Dr. Surender Kumar credentials, EOLABS.IN badge |
| **2** | `scene2_assistant_overview` | Interactive | 6-Layer Decision Architecture | Telemetry, Hypothesis, Theory Narrative, CFO Table, Plotly Chart, Literature Vault |
| **3** | `scene3_infosys_tech` | Company 1 | **Infosys Ltd. (Tech)** | Mature stage, 4.2% near-zero leverage, internal cash self-financing playbook |
| **4** | `scene4_tata_steel_stress` | Company 2 | **Tata Steel (Metals)** | Macro rate shock (+150 bps), ICR compression (1.72x vs 2.00x floor), covenant defense |
| **5** | `scene5_airtel_telecom` | Company 3 | **Bharti Airtel (Telecom)** | 5G spectrum commitments, InvIT tower monetization, balance-sheet deleveraging |
| **6** | `scene6_indigo_aviation` | Company 4 | **IndiGo (Aviation)** | Aviation turbine fuel shocks, cash burn runway, Sale-and-Leaseback debt capacity |
| **7** | `scene7_sunpharma_pharma` | Company 5 | **Sun Pharma (Pharma)** | Cross-border M&A financing, Euro-denominated notes natural currency FX hedge |
| **8** | `scene8_researcher_stata` | Econometrics | Panel Fixed-Effects | Researcher mode toggle, `xtreg lev size tang roa mtb i.year, fe cluster(ind_code)` |
| **9** | `scene9_literature_vault` | Governance | Literature Benchmark Vault | Dickinson (2011), Rajan & Zingales (1995), Myers (1984), Board Deck export |
| **10** | `scene10_closing_card` | Static Card | Executive Epilogue | Closing institutional credits, verified production seal, EOLABS.IN |

---

## 4. Visual Governance & Layout Constraints

1. **Resolution & Canvas:** 1920x1080 Full HD (16:9), 60 fps capture via Chromium Playwright.
2. **Slim HUD Overlay:**
   - Dark glassmorphism pill centered at `top: 8px`.
   - Cyan archetype pill tag + White scene title + Slate subtitle description.
3. **Subtitle Placement:**
   - Font: Arial, 11pt, White with subtle dark border (`Outline=1.5`).
   - Vertical Margin: `MarginV=90` (positioned in upper clean area, strictly preventing any overlap with the chat bar or lower controls).
4. **Session Isolation:**
   - Pre-scene SQLite cleanup (`DELETE FROM chat_messages; DELETE FROM chat_sessions;`) ensuring zero message leakage across companies.

---

## 5. Verification & Red Team Quality Gates

Before the video is finalized, an automated visual red team inspection validates:
- [x] **Zero Audio Overlap:** Silence audio track strictly matches generation elapsed time.
- [x] **Prompt Visibility:** Prompt typed into chat box is clearly visible before submission.
- [x] **Top Snapping:** Viewport resets to $y=0$ before post-generation commentary begins.
- [x] **5 Company Coverage:** All 5 individual company archetypes recorded with distinct outputs.
- [x] **Subtitle Clarity:** Subtitles visible with zero occlusion of critical UI data.
