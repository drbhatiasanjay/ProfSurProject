const path = require("path");
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel,
  BorderStyle, WidthType, ShadingType, PageNumber, PageBreak
} = require(path.join(process.env.APPDATA, "npm", "node_modules", "docx"));

// ── Shared constants ──────────────────────────────────────────────
const FONT = "Arial";
const NAVY = "1B3A5C";
const ACCENT = "2E75B6";
const LIGHT_BG = "E8F0F8";
const TABLE_HEADER_BG = "1B3A5C";
const TABLE_ALT_BG = "F2F7FB";
const BORDER = { style: BorderStyle.SINGLE, size: 1, color: "B0B0B0" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };
const CELL_MARGINS = { top: 60, bottom: 60, left: 100, right: 100 };

// Page dimensions: US Letter, 1" margins
const PAGE_WIDTH = 12240;
const MARGIN = 1440;
const CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN; // 9360

// ── Helpers ────────────────────────────────────────────────────────
function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 200 },
    children: [new TextRun({ text, font: FONT, size: 32, bold: true, color: NAVY })],
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, font: FONT, size: 26, bold: true, color: ACCENT })],
  });
}

function heading3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 120 },
    children: [new TextRun({ text, font: FONT, size: 22, bold: true, color: NAVY })],
  });
}

function para(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 120, line: 276 },
    alignment: opts.align || AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, font: FONT, size: 22, ...opts })],
  });
}

function boldPara(label, text) {
  return new Paragraph({
    spacing: { after: 120, line: 276 },
    alignment: AlignmentType.JUSTIFIED,
    children: [
      new TextRun({ text: label, font: FONT, size: 22, bold: true }),
      new TextRun({ text, font: FONT, size: 22 }),
    ],
  });
}

function bulletItem(text, ref = "bullets", level = 0) {
  return new Paragraph({
    numbering: { reference: ref, level },
    spacing: { after: 80, line: 276 },
    children: [new TextRun({ text, font: FONT, size: 22 })],
  });
}

function numberedItem(text, ref = "numbers", level = 0) {
  return new Paragraph({
    numbering: { reference: ref, level },
    spacing: { after: 80, line: 276 },
    children: [new TextRun({ text, font: FONT, size: 22 })],
  });
}

function richBullet(runs, ref = "bullets", level = 0) {
  return new Paragraph({
    numbering: { reference: ref, level },
    spacing: { after: 80, line: 276 },
    children: runs,
  });
}

function headerCell(text, width) {
  return new TableCell({
    borders: BORDERS,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: TABLE_HEADER_BG, type: ShadingType.CLEAR },
    margins: CELL_MARGINS,
    verticalAlign: "center",
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text, font: FONT, size: 18, bold: true, color: "FFFFFF" })],
    })],
  });
}

function dataCell(text, width, opts = {}) {
  const shading = opts.shading ? { fill: opts.shading, type: ShadingType.CLEAR } : undefined;
  return new TableCell({
    borders: BORDERS,
    width: { size: width, type: WidthType.DXA },
    shading,
    margins: CELL_MARGINS,
    verticalAlign: "center",
    children: [new Paragraph({
      alignment: opts.align || AlignmentType.LEFT,
      children: [new TextRun({
        text,
        font: FONT,
        size: 18,
        bold: opts.bold || false,
        color: opts.color || "333333",
      })],
    })],
  });
}

function spacer() {
  return new Paragraph({ spacing: { after: 80 }, children: [] });
}

// ── Competitor Analysis Table Builder ─────────────────────────────
function competitorTable(headers, rows, colWidths) {
  const tableRows = [];
  // Header row
  tableRows.push(new TableRow({
    children: headers.map((h, i) => headerCell(h, colWidths[i])),
  }));
  // Data rows
  rows.forEach((row, ri) => {
    tableRows.push(new TableRow({
      children: row.map((cell, ci) => dataCell(cell, colWidths[ci], {
        shading: ri % 2 === 1 ? TABLE_ALT_BG : undefined,
        bold: ci === 0,
        align: ci === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
      })),
    }));
  });
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: tableRows,
  });
}

// ── Document ──────────────────────────────────────────────────────
const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: FONT, color: NAVY },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT, color: ACCENT },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 },
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: FONT, color: NAVY },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "\u00B7", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }, {
          level: 1, format: LevelFormat.BULLET, text: "\u00B7", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 1440, hanging: 360 } } },
        }],
      },
      {
        reference: "numbers",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
      {
        reference: "numbers2",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
      {
        reference: "numbers3",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
      {
        reference: "numbers4",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_WIDTH, height: 15840 },
        margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: ACCENT, space: 4 } },
          children: [
            new TextRun({ text: "Section E: Commercial Gap Analysis & Competitive Landscape", font: FONT, size: 18, italics: true, color: "888888" }),
          ],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC", space: 4 } },
          children: [
            new TextRun({ text: "LifeCycle Leverage Dashboard \u2014 Commercial Gap Analysis  |  Page ", font: FONT, size: 16, color: "999999" }),
            new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: "999999" }),
          ],
        })],
      }),
    },
    children: [
      // ════════════════════════════════════════════════════════════
      // TITLE
      // ════════════════════════════════════════════════════════════
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 80 },
        children: [new TextRun({ text: "SECTION E", font: FONT, size: 40, bold: true, color: NAVY })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
        children: [new TextRun({ text: "Commercial Gap Analysis & Competitive Landscape", font: FONT, size: 32, bold: true, color: ACCENT })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 60 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: ACCENT, space: 8 } },
        children: [new TextRun({ text: "LifeCycle Leverage Dashboard  |  April 2026", font: FONT, size: 22, color: "666666" })],
      }),
      spacer(),

      // ════════════════════════════════════════════════════════════
      // E.1 EXISTING SOFTWARE LANDSCAPE
      // ════════════════════════════════════════════════════════════
      heading1("E.1  Existing Software Landscape"),

      para("The capital structure analytics market is fragmented across enterprise terminals, statistical software, credit risk platforms, and emerging fintech tools. No single product currently offers lifecycle-aware capital structure modelling with integrated econometric and machine learning capabilities. This section evaluates seven categories of incumbent solutions, identifying their strengths, pricing, and structural limitations relative to the LifeCycle Leverage Dashboard."),

      // E.1.1 Bloomberg
      heading2("E.1.1  Bloomberg Terminal / Refinitiv Eikon"),

      boldPara("Overview. ", "Bloomberg Terminal (Bloomberg L.P.) and Refinitiv Eikon (LSEG) are the dominant enterprise platforms for financial data, analytics, and trading. Bloomberg covers approximately 325,000 terminal subscribers globally (2024), while Eikon serves an estimated 190,000 users. Both platforms provide broad financial data feeds, screening tools, and charting capabilities."),

      boldPara("Capital Structure Capabilities. ", "Bloomberg offers the CRPR (Credit Risk/Probability of Default) module, DDIS (Debt Distribution), and FA (Financial Analysis) functions that allow users to view debt composition, maturity profiles, interest coverage ratios, and peer comparisons. Refinitiv Eikon provides similar functionality through StarMine credit risk models and Datastream for historical financial data. Both platforms enable users to screen companies by leverage ratios and export data for external analysis."),

      boldPara("Pricing. ", "Bloomberg Terminal subscriptions range from USD 20,000 to USD 27,600 per user per year (with volume discounts for large deployments). Refinitiv Eikon pricing is tiered from approximately USD 3,600 per year (Eikon with Datastream Basic) to USD 22,000 per year for premium tiers. The total cost of ownership including hardware, data feeds, and training typically exceeds USD 30,000 per seat annually."),

      boldPara("Structural Gaps. ", "Neither platform provides:"),
      bulletItem("Corporate lifecycle stage classification (Dickinson cash-flow taxonomy or any alternative)"),
      bulletItem("Stage-specific regression models that allow determinants to vary by growth, maturity, or decline"),
      bulletItem("Panel econometric models (Fixed Effects, Random Effects, System GMM) within the terminal interface"),
      bulletItem("Machine learning-driven leverage prediction with explainability (SHAP values)"),
      bulletItem("Survival analysis for stage transition probabilities"),
      bulletItem("Dynamic, context-aware interpretation of statistical results"),
      para("Bloomberg and Eikon remain tools for data retrieval and screening; they are not analytical engines for capital structure research."),

      // E.1.2 S&P Capital IQ / FactSet
      heading2("E.1.2  S&P Capital IQ / FactSet"),

      boldPara("Overview. ", "S&P Capital IQ (S&P Global) and FactSet Research Systems are institutional-grade financial data and analytics platforms widely used by investment banks, private equity firms, and corporate finance teams. Capital IQ covers over 62,000 public companies and 53,000 private companies globally. FactSet aggregates data from 200+ vendors with proprietary analytical tools."),

      boldPara("Capital Structure Capabilities. ", "Capital IQ provides detailed debt breakdowns (by instrument, currency, maturity), credit ratings histories, and comparable company analysis (comps) with leverage metrics. Its Excel plug-in allows bulk data extraction for custom modelling. FactSet offers the Debt Capital Structure data set, portfolio analytics, and quantitative screening with over 1,000 financial data points per company."),

      boldPara("Pricing. ", "Capital IQ subscriptions range from USD 12,000 to USD 20,000 per user per year depending on modules selected. FactSet pricing is similar, typically USD 12,000 to USD 18,000 per user per year, with enterprise agreements for larger deployments. Both platforms charge additional fees for premium data sets (e.g., private company data, real-time feeds)."),

      boldPara("Structural Gaps. ", ""),
      bulletItem("No built-in panel econometric models; users must export data to Stata or R for Fixed Effects, Random Effects, or GMM estimation"),
      bulletItem("No lifecycle classification framework; all analysis is cross-sectional or time-series without stage awareness"),
      bulletItem("No ML-driven leverage prediction or SHAP-based feature importance"),
      bulletItem("No survival analysis or transition probability estimation"),
      bulletItem("Indian market coverage, while improving, remains secondary to US and European data depth (particularly for mid-cap and small-cap Indian firms)"),
      bulletItem("No automated interpretation; results require manual expert analysis"),

      // E.1.3 CMIE Prowess
      heading2("E.1.3  CMIE ProwessOnWeb / Prowess IQ"),

      boldPara("Overview. ", "The Centre for Monitoring Indian Economy (CMIE) Prowess database is the most comprehensive source of Indian corporate financial data, covering over 48,000 companies (listed and unlisted). ProwessOnWeb is the web-based interface; Prowess IQ is the downloadable analytical tool. CMIE is the de facto standard for academic research on Indian firms and is used extensively by the Reserve Bank of India, SEBI, and Indian business schools."),

      boldPara("Capital Structure Capabilities. ", "Prowess provides detailed balance sheet data including long-term borrowings, short-term borrowings, debentures, bank loans, foreign currency debt, and preference capital. Historical data extends back to the early 1990s for listed firms. The platform allows ratio calculations, industry aggregates, and data export in multiple formats."),

      boldPara("Pricing. ", "Academic institutional subscriptions for ProwessOnWeb range from INR 25,000 to INR 1,00,000 per year depending on the number of concurrent users and data modules. Corporate subscriptions are negotiated individually but typically range from INR 2,00,000 to INR 5,00,000 per year. Individual researcher licences are available at approximately INR 15,000 to INR 30,000 per year."),

      boldPara("Structural Gaps. ", "CMIE Prowess is fundamentally a data provider, not an analytical platform:"),
      bulletItem("No econometric models of any kind (not even OLS regression)"),
      bulletItem("No lifecycle stage classification; users must manually compute Dickinson indicators from raw cash flow data"),
      bulletItem("No visualisation beyond basic charting; no interactive dashboards"),
      bulletItem("No ML models, no SHAP explanations, no survival analysis"),
      bulletItem("No dynamic interpretation of results"),
      bulletItem("Data export requires significant post-processing in Stata, R, or Python before any analytical work can begin"),
      para("For capital structure researchers, CMIE is a necessary input but not a substitute for an analytical platform."),

      // E.1.4 Stata/R/Python
      heading2("E.1.4  Statistical Software: Stata, R, and Python"),

      boldPara("Overview. ", "Stata (StataCorp), R (open source), and Python (open source) are the primary tools used by academic researchers and quantitative analysts for capital structure studies. The vast majority of published capital structure research (including the foundational studies by Rajan & Zingales 1995, Frank & Goyal 2009, and Lemmon, Roberts & Zender 2008) was conducted using Stata or R."),

      boldPara("Capital Structure Capabilities. ", "These tools can, in principle, perform any econometric or statistical analysis. Stata offers built-in commands for Fixed Effects (xtreg, fe), Random Effects (xtreg, re), GMM (xtabond2), and Hausman tests. R provides equivalent functionality through the plm, lmtest, and pgmm packages. Python offers statsmodels for panel data and linearmodels for instrumental variable estimation."),

      boldPara("Pricing. ", "Stata perpetual licences range from USD 595 (IC/student) to USD 1,595 (SE) to USD 2,985 (MP) with annual renewal options at approximately USD 300 to USD 900. R and Python are free and open source, though commercial support and IDE licences (RStudio Team at USD 15,000/year; JetBrains PyCharm at USD 249/year) represent additional costs."),

      boldPara("Structural Gaps. ", ""),
      bulletItem("No pre-built capital structure models; every analysis must be coded from scratch, requiring 200-500 lines of code for a basic panel regression study"),
      bulletItem("No lifecycle classification automation; researchers must manually implement the Dickinson (2011) taxonomy or alternatives"),
      bulletItem("No interactive dashboard; results are static outputs (tables, PDFs) that cannot be explored by non-technical users"),
      bulletItem("No SHAP-based explanations unless manually integrated with Python ML libraries"),
      bulletItem("No dynamic interpretation; statistical output requires expert human judgement to contextualise"),
      bulletItem("Steep learning curve: proficiency in Stata panel data commands or R/Python econometric libraries typically requires 6-12 months of training"),
      bulletItem("No collaboration features for teams of mixed technical ability (e.g., a CFO reviewing an analyst's model output)"),

      // E.1.5 Moody's / CreditEdge
      heading2("E.1.5  Moody's Analytics / CreditEdge"),

      boldPara("Overview. ", "Moody's Analytics CreditEdge platform provides expected default frequency (EDF) measures, credit transition matrices, and portfolio credit risk analytics. The platform covers approximately 40,000 public firms and 500 million private firms (via RiskCalc). Moody's KMV model is the industry standard for structural credit risk assessment based on the Merton distance-to-default framework."),

      boldPara("Pricing. ", "CreditEdge subscriptions are enterprise-priced, typically ranging from USD 50,000 to USD 200,000 per year depending on coverage, modules, and number of users. RiskCalc for private companies is priced separately. Individual researcher access is generally not available outside institutional agreements."),

      boldPara("Structural Gaps. ", ""),
      bulletItem("Focus is exclusively on default probability and credit migration, not capital structure optimisation or determinant analysis"),
      bulletItem("No lifecycle classification framework; firms are classified by credit rating, not corporate maturity stage"),
      bulletItem("No regression-based determinant analysis (the platform does not answer \"what drives leverage\" but rather \"what is the probability of default\")"),
      bulletItem("No stage-specific models that distinguish growth-phase firms from mature or declining firms"),
      bulletItem("Indian market coverage is limited to rated firms (approximately 400-500 companies with Moody's or ICRA ratings), missing the vast majority of BSE-listed companies"),
      bulletItem("No ML-based leverage prediction or SHAP explainability"),

      // E.1.6 McKinsey / Damodaran
      heading2("E.1.6  McKinsey Valuation Framework / Damodaran Tools"),

      boldPara("Overview. ", "McKinsey's Valuation (Koller, Goedhart & Wessels) framework and Professor Aswath Damodaran's publicly available valuation spreadsheets and datasets are widely used reference tools for corporate finance practitioners. Damodaran's website provides industry-average capital structure data, cost of capital estimates, and valuation models for approximately 90 countries."),

      boldPara("Pricing. ", "Damodaran's tools are freely available (academic public good). McKinsey's proprietary tools are available only to McKinsey consultants and clients (internal use). McKinsey published valuation resources (books, frameworks) are commercially available at nominal cost."),

      boldPara("Structural Gaps. ", ""),
      bulletItem("Static spreadsheets with annual updates; no real-time or quarterly data refresh"),
      bulletItem("No panel data analysis; all figures are cross-sectional industry averages"),
      bulletItem("No firm-level granularity; users cannot drill down from industry averages to individual company analysis"),
      bulletItem("No lifecycle classification; capital structure averages do not distinguish between growth-stage and mature firms within the same industry"),
      bulletItem("No econometric modelling (OLS, FE, RE, GMM); the tools provide descriptive statistics only"),
      bulletItem("No ML models, survival analysis, or forecasting capabilities"),
      bulletItem("No interactive dashboard; all output is in Excel or PDF format"),

      // E.1.7 Indian Fintech
      heading2("E.1.7  Indian Fintech Platforms"),

      boldPara("Overview. ", "Several Indian fintech platforms provide corporate financial data and screening tools. The most relevant platforms include:"),

      richBullet([
        new TextRun({ text: "Screener.in ", font: FONT, size: 22, bold: true }),
        new TextRun({ text: "(Screener.in Pvt. Ltd.) \u2014 Free and premium screening tool covering approximately 5,000 BSE/NSE-listed companies. Provides financial statements, ratios, peer comparison, and customisable screens. Premium tier at INR 4,999/year.", font: FONT, size: 22 }),
      ]),
      richBullet([
        new TextRun({ text: "Trendlyne ", font: FONT, size: 22, bold: true }),
        new TextRun({ text: "(Trendlyne Analytics) \u2014 Stock analysis platform with financial data, momentum indicators, insider trading data, and institutional holding patterns. Premium at INR 3,000 to INR 15,000/year.", font: FONT, size: 22 }),
      ]),
      richBullet([
        new TextRun({ text: "Tijori Finance ", font: FONT, size: 22, bold: true }),
        new TextRun({ text: "(Tijori Pvt. Ltd.) \u2014 Newer entrant focused on clean financial data presentation, industry mapping, and investor-friendly visualisations. Freemium model with premium at approximately INR 5,000/year.", font: FONT, size: 22 }),
      ]),
      richBullet([
        new TextRun({ text: "Moneycontrol / ET Markets ", font: FONT, size: 22, bold: true }),
        new TextRun({ text: "\u2014 Mass-market financial portals with company financials, analyst estimates, and news. Free with advertising; premium at INR 2,000 to INR 4,000/year.", font: FONT, size: 22 }),
      ]),

      boldPara("Structural Gaps. ", "All Indian fintech screening platforms share the same fundamental limitations:"),
      bulletItem("Designed for equity investors (stock screening, momentum), not capital structure researchers or CFOs"),
      bulletItem("No econometric models of any kind; no regression analysis, no panel data handling"),
      bulletItem("No lifecycle classification; firms are categorised by sector and market capitalisation only"),
      bulletItem("No ML models for leverage prediction or optimisation"),
      bulletItem("No survival analysis, no transition probability estimation"),
      bulletItem("No academic-grade statistical output (coefficient tables, Hausman tests, diagnostic statistics)"),
      bulletItem("No dynamic interpretation of analytical results"),
      para("These platforms serve a retail investor audience and are not positioned to address institutional or academic capital structure analytics needs."),

      new Paragraph({ children: [new PageBreak()] }),

      // ════════════════════════════════════════════════════════════
      // E.2 GAP ANALYSIS MATRIX
      // ════════════════════════════════════════════════════════════
      heading1("E.2  Gap Analysis Matrix"),

      para("Table E.1 presents a comprehensive feature comparison across seven competitor categories and the LifeCycle Leverage Dashboard. A tick mark indicates native, built-in capability accessible through the platform's standard interface. \"Partial\" denotes limited or indirect availability. \"Code\" indicates that the capability exists only through manual programming."),

      spacer(),

      // Main comparison table
      competitorTable(
        ["Feature / Capability", "Bloomberg Eikon", "Capital IQ FactSet", "CMIE Prowess", "Stata / R", "Moody\u2019s CreditEdge", "Damodaran Tools", "Indian Fintech", "LifeCycle Dashboard"],
        [
          ["Indian corporate data (400+ firms, 24 years)", "Partial", "Partial", "Full", "No data", "Limited", "Averages", "Partial", "401 firms"],
          ["Lifecycle stage classification (Dickinson)", "No", "No", "No", "Manual", "No", "No", "No", "Automatic"],
          ["Pooled OLS with robust SEs", "No", "No", "No", "Code", "No", "No", "No", "Built-in"],
          ["Panel Fixed Effects / Random Effects", "No", "No", "No", "Code", "No", "No", "No", "Built-in"],
          ["System GMM estimation", "No", "No", "No", "Code", "No", "No", "No", "Built-in"],
          ["Hausman specification test", "No", "No", "No", "Code", "No", "No", "No", "Built-in"],
          ["Stage-specific determinant analysis", "No", "No", "No", "Manual", "No", "No", "No", "Automatic"],
          ["ML leverage prediction (RF, XGB, LGBM)", "No", "No", "No", "Code", "No", "No", "No", "Built-in"],
          ["SHAP feature explanations", "No", "No", "No", "Code", "No", "No", "No", "Built-in"],
          ["Cox PH survival analysis", "No", "No", "No", "Code", "No", "No", "No", "Built-in"],
          ["Kaplan-Meier survival curves", "No", "No", "No", "Code", "No", "No", "No", "Built-in"],
          ["LSTM/GRU leverage forecasting", "No", "No", "No", "Code", "No", "No", "No", "Built-in"],
          ["Event/shock impact analysis (COVID, demonetisation)", "Partial", "Partial", "No", "Manual", "Partial", "No", "No", "Automatic"],
          ["Dynamic AI-generated interpretation", "No", "No", "No", "No", "No", "No", "No", "Built-in"],
          ["Interactive web dashboard", "Terminal", "Desktop", "Web", "No", "Web", "Excel", "Web", "Web (Streamlit)"],
          ["Approximate annual cost (per user)", "$24,000", "$15,000", "$4,000", "$1,000", "$100,000+", "Free", "$500", "TBD"],
        ],
        [1600, 900, 900, 900, 800, 900, 900, 900, 1160]
      ),

      spacer(),

      para("Table E.1 reveals a decisive pattern: the LifeCycle Leverage Dashboard is the only platform that combines lifecycle classification, multi-tier econometric and ML modelling, survival analysis, leverage forecasting, and automated interpretation in a single, browser-accessible interface. Stata and R can, in principle, replicate individual analytical components, but only through extensive custom coding that produces static output inaccessible to non-technical stakeholders.", { italics: true }),

      new Paragraph({ children: [new PageBreak()] }),

      // ════════════════════════════════════════════════════════════
      // E.2.1 PRICING COMPARISON
      // ════════════════════════════════════════════════════════════
      heading2("E.2.1  Pricing Comparison"),

      para("Table E.2 summarises the annual cost structure for a hypothetical institutional user (e.g., an Indian investment bank or business school) requiring capital structure analytics for Indian companies."),

      spacer(),

      competitorTable(
        ["Platform", "Annual Cost (USD)", "Indian Data Coverage", "Analytical Capability", "Accessibility"],
        [
          ["Bloomberg Terminal", "$20,000\u2013$27,600", "Partial (large-cap bias)", "Data + screening", "Dedicated terminal"],
          ["Refinitiv Eikon", "$3,600\u2013$22,000", "Partial (large-cap bias)", "Data + screening", "Desktop application"],
          ["S&P Capital IQ", "$12,000\u2013$20,000", "Partial (improving)", "Data + screening + Excel", "Desktop + Excel plug-in"],
          ["FactSet", "$12,000\u2013$18,000", "Partial (improving)", "Data + quantitative screens", "Desktop + web"],
          ["CMIE ProwessOnWeb", "$500\u2013$6,000", "Full (48,000+ firms)", "Raw data only", "Web interface"],
          ["Stata (SE)", "$895/yr renewal", "None (BYO data)", "Full econometric toolkit", "Desktop (command-line)"],
          ["R + RStudio", "Free\u2013$15,000", "None (BYO data)", "Full statistical toolkit", "Desktop IDE"],
          ["Moody\u2019s CreditEdge", "$50,000\u2013$200,000", "Limited (rated firms)", "Credit risk only", "Web platform"],
          ["Screener.in (Premium)", "$60", "5,000 listed firms", "Screening only", "Web"],
          ["LifeCycle Leverage Dashboard", "TBD", "401 firms (24 years)", "Full analytical suite", "Web (any browser)"],
        ],
        [2000, 1800, 1800, 1900, 1860]
      ),

      spacer(),

      para("The pricing gap is significant. A researcher or institution seeking both Indian corporate data and analytical capability currently faces a choice between: (a) purchasing CMIE data plus Stata/R software and investing 6-12 months in custom model development, at a combined cost of approximately USD 2,000-7,000 plus substantial time investment; or (b) subscribing to Bloomberg or Capital IQ at USD 15,000-25,000 per year and still lacking lifecycle classification and advanced analytical models. The LifeCycle Leverage Dashboard eliminates this trade-off by providing pre-built, validated analytical models on curated Indian data through an accessible web interface."),

      new Paragraph({ children: [new PageBreak()] }),

      // ════════════════════════════════════════════════════════════
      // E.3 UNIQUE SELLING PROPOSITIONS
      // ════════════════════════════════════════════════════════════
      heading1("E.3  Unique Selling Propositions"),

      para("The LifeCycle Leverage Dashboard possesses five differentiated capabilities that no existing competitor, individually or in combination, currently offers."),

      spacer(),

      // USP 1
      heading3("USP 1: Lifecycle-Aware Capital Structure Models"),
      para("The dashboard is the first commercial tool to embed Dickinson's (2011) cash-flow-based lifecycle classification directly into capital structure analysis. Every model, visualisation, and interpretation is conditioned on whether a firm is in its introduction, growth, maturity, shake-out, or decline stage. This is not a cosmetic label but a structural feature: separate regression coefficients, separate ML models, and separate survival curves are estimated for each stage. No Bloomberg function, Capital IQ screen, or CMIE query can replicate this."),

      // USP 2
      heading3("USP 2: Stage-Specific Determinant Analysis"),
      para("Capital structure determinants (profitability, tangibility, firm size, growth opportunities, tax shields) behave differently across lifecycle stages. A growth-stage firm's leverage is driven by different factors than a mature firm's. The dashboard estimates stage-specific regression models that quantify these differences, enabling users to understand not just what drives leverage in general, but what drives leverage at each point in a firm's lifecycle. This directly addresses the gap identified in Frank and Goyal's (2009) survey of capital structure determinants, which noted the absence of lifecycle conditioning in empirical work."),

      // USP 3
      heading3("USP 3: Econometric and Machine Learning Triangulation"),
      para("The dashboard employs a three-tier analytical architecture: Tier 1 (econometric models: OLS, Fixed Effects, Random Effects, System GMM) provides theory-grounded coefficient estimates with standard errors and specification tests; Tier 2 (ML models: Random Forest, XGBoost, LightGBM with SHAP) provides predictive accuracy and non-linear feature importance; Tier 3 (survival analysis, LSTM forecasting, clustering) provides forward-looking risk and trajectory analysis. Results from all three tiers are presented together, enabling users to triangulate findings. Where econometric models identify causal relationships, ML models confirm predictive relevance, and survival models assess dynamic risk. This multi-method approach is standard in PhD-level research but has never been packaged into a commercial tool."),

      // USP 4
      heading3("USP 4: Dynamic AI-Generated Interpretation"),
      para("Every chart, regression table, and model output in the dashboard is accompanied by a dynamically generated interpretation that explains the result in finance-contextual language. These interpretations are not static text blocks; they are algorithmically generated from the actual data, adjusting for the specific values, significance levels, and comparative benchmarks present in each analysis. A user viewing a Fixed Effects regression for mature-stage firms receives an interpretation specific to that subset, explaining which determinants are statistically significant, what their economic magnitudes imply, and how the results compare to theoretical predictions. No existing platform, including Bloomberg, provides this capability."),

      // USP 5
      heading3("USP 5: Academic Rigour with Commercial Usability"),
      para("The dashboard's methodology is grounded in a PhD thesis (Kumar, University of Delhi) that follows peer-reviewed econometric practices: panel-robust standard errors, Hausman specification testing, winsorisation of outliers, panel-aware cross-validation for ML models, and survival analysis with competing risks. This academic rigour is combined with a Streamlit-based web interface that requires no coding, no software installation, and no statistical expertise from the end user. The combination of methodological validity and interface accessibility is unique in the market."),

      new Paragraph({ children: [new PageBreak()] }),

      // ════════════════════════════════════════════════════════════
      // E.4 MARKET SIZING
      // ════════════════════════════════════════════════════════════
      heading1("E.4  Market Sizing"),

      heading2("E.4.1  Total Addressable Market (TAM)"),
      para("The TAM encompasses all professionals and institutions that analyse or manage corporate capital structure in India. This includes:"),
      bulletItem("Chief Financial Officers and treasury teams of the approximately 5,000 actively traded BSE/NSE-listed companies"),
      bulletItem("Credit analysts at 34 scheduled commercial banks, 43 regional rural banks, and 10 small finance banks regulated by the Reserve Bank of India"),
      bulletItem("Investment banking divisions at approximately 250 registered merchant bankers (Category I through IV, SEBI-regulated)"),
      bulletItem("Private equity and venture capital firms: approximately 120 active PE/VC firms operating in India (IVCA members)"),
      bulletItem("Credit rating agencies: CRISIL, ICRA, CARE, India Ratings, Brickwork, Acuite (6 SEBI-registered agencies with approximately 2,000 analysts collectively)"),
      bulletItem("Academic institutions: 20 IIMs, 23 IITs (with management departments), 800+ AICTE-approved MBA programmes, and approximately 50 research universities with active finance PhD programmes"),
      bulletItem("Regulatory bodies: RBI, SEBI, Ministry of Corporate Affairs (research divisions)"),
      para("Estimated TAM: approximately 50,000 to 80,000 potential users across all categories."),

      heading2("E.4.2  Serviceable Addressable Market (SAM)"),
      para("The SAM narrows to professionals actively engaged in capital structure analysis or decision-making, who would derive direct value from lifecycle-aware analytical tools:"),
      bulletItem("CFOs and finance heads of BSE 500 companies (active capital structure management): approximately 1,500 professionals"),
      bulletItem("Credit analysts at major banks (SBI, HDFC, ICICI, Axis, Kotak, and 10 other large commercial banks): approximately 3,000 analysts"),
      bulletItem("Investment banking analysts covering Indian equities and debt capital markets: approximately 1,000 professionals"),
      bulletItem("PE/VC professionals conducting due diligence and portfolio monitoring: approximately 500 professionals"),
      bulletItem("Finance faculty and PhD researchers at top-50 Indian institutions: approximately 2,000 researchers"),
      bulletItem("CRISIL, ICRA, and CARE credit rating analysts: approximately 1,200 analysts"),
      para("Estimated SAM: approximately 9,000 to 12,000 potential paying users."),

      heading2("E.4.3  Serviceable Obtainable Market (SOM)"),
      para("The SOM represents the realistic initial market capture within 12-18 months of commercial launch:"),
      bulletItem("Academic early adopters: 20-30 institutions (IIMs, top universities) with 3-10 users each: 100-200 users"),
      bulletItem("Credit analyst teams at 5-8 major banks (pilot programmes): 50-100 users"),
      bulletItem("CFO offices at 10-20 mid-to-large Indian corporates: 30-60 users"),
      bulletItem("Independent researchers and consultants: 20-40 users"),
      para("Estimated SOM: 200 to 400 users in Year 1, generating initial revenue validation and usage data for product iteration."),

      heading2("E.4.4  Revenue Projections (Indicative)"),
      spacer(),
      competitorTable(
        ["Scenario", "Users (Year 1)", "Price Point (Annual)", "Year 1 Revenue", "Year 3 Revenue (projected)"],
        [
          ["Academic", "150", "USD 500/institution", "USD 75,000", "USD 300,000"],
          ["Professional (Individual)", "100", "USD 2,000/user", "USD 200,000", "USD 800,000"],
          ["Enterprise (Bank/PE)", "50", "USD 10,000/team", "USD 500,000", "USD 2,000,000"],
          ["Blended Total", "300", "Weighted average", "USD 775,000", "USD 3,100,000"],
        ],
        [1800, 1600, 2000, 2000, 1960]
      ),

      spacer(),
      para("These projections assume conservative adoption rates and do not include potential revenue from consulting engagements, custom model development, or data licensing arrangements that may emerge from platform usage."),

      new Paragraph({ children: [new PageBreak()] }),

      // ════════════════════════════════════════════════════════════
      // E.5 EXPANSION STRATEGY
      // ════════════════════════════════════════════════════════════
      heading1("E.5  Expansion Strategy"),

      para("The platform expansion follows a phased approach that balances market validation with capability development, ensuring each phase builds on validated demand from the preceding one."),

      heading2("Phase 1: Indian Market Foundation (Current \u2013 Month 6)"),
      boldPara("Focus. ", "Indian corporates, academic institutions, and credit analysts."),
      boldPara("Key Activities: ", ""),
      bulletItem("Secure 5-10 academic institutional licences (IIMs, Delhi University, IITs) as anchor customers"),
      bulletItem("Pilot programme with 2-3 bank credit analyst teams (CRISIL, SBI Capital, ICICI Securities)"),
      bulletItem("Publish 2-3 working papers using the dashboard's analytical output to establish academic credibility"),
      bulletItem("Present at National Conference on Capital Structure (IGIDR) and IIM finance research seminars"),
      bulletItem("Expand dataset from 401 to 800+ firms (adding BSE 500 firms not currently covered)"),
      boldPara("Revenue Target. ", "USD 150,000 (primarily academic and pilot enterprise licences)."),

      heading2("Phase 2: Credit Risk Integration (Month 6 \u2013 Month 12)"),
      boldPara("Focus. ", "Banking sector partnerships and credit risk analytics."),
      boldPara("Key Activities: ", ""),
      bulletItem("Integrate credit rating data (CRISIL, ICRA ratings histories) to link lifecycle stages with credit migration"),
      bulletItem("Develop distress prediction module combining leverage forecasting with financial distress indicators (Altman Z-score, Ohlson O-score adapted for Indian accounting standards)"),
      bulletItem("Partner with 1-2 Indian banks for internal credit review tool deployment"),
      bulletItem("Add NPA (Non-Performing Asset) analysis module linking capital structure dynamics to loan default"),
      bulletItem("Develop API access for integration with bank internal risk management systems"),
      boldPara("Revenue Target. ", "USD 500,000 cumulative (adding enterprise banking contracts)."),

      heading2("Phase 3: Multi-Country Expansion (Month 12 \u2013 Month 18)"),
      boldPara("Focus. ", "Geographic expansion to emerging and developed markets with distinct capital structure dynamics."),
      boldPara("Key Activities: ", ""),
      bulletItem("Add US market data (Compustat universe, approximately 4,000 firms) to enable cross-country comparative analysis"),
      bulletItem("Add UK/EU market data (approximately 2,000 firms) from Worldscope or equivalent"),
      bulletItem("Add ASEAN market data (Singapore, Malaysia, Thailand, Indonesia \u2014 approximately 3,000 firms collectively)"),
      bulletItem("Implement country-specific institutional variables (legal origin, creditor rights, tax regimes) following La Porta et al. (1998) and subsequent comparative capital structure literature"),
      bulletItem("Publish comparative lifecycle-leverage study across 5+ countries to attract international academic attention"),
      boldPara("Revenue Target. ", "USD 1,500,000 cumulative (adding international institutional clients)."),

      heading2("Phase 4: Platform Play (Month 18 \u2013 Month 24)"),
      boldPara("Focus. ", "Transformation from a single-purpose tool to a research platform."),
      boldPara("Key Activities: ", ""),
      bulletItem("Open API for researchers to deploy their own econometric and ML models on the platform's data infrastructure"),
      bulletItem("Create model marketplace where researchers can publish and monetise validated analytical models"),
      bulletItem("Enable custom dataset uploads (firms can upload proprietary data for private analysis)"),
      bulletItem("Develop white-label deployment for consulting firms (McKinsey, Deloitte, EY) to embed lifecycle analytics in client deliverables"),
      bulletItem("Explore partnership with CMIE for integrated data licensing (CMIE data + LifeCycle analytics)"),
      boldPara("Revenue Target. ", "USD 3,000,000+ cumulative (platform licensing, API revenue, and model marketplace commissions)."),

      new Paragraph({ children: [new PageBreak()] }),

      // ════════════════════════════════════════════════════════════
      // E.6 COMPETITIVE MOAT
      // ════════════════════════════════════════════════════════════
      heading1("E.6  Competitive Moat"),

      para("The LifeCycle Leverage Dashboard possesses four structural competitive advantages that create meaningful barriers to replication by incumbents or new entrants."),

      spacer(),

      heading3("Moat 1: PhD-Grade Methodology"),
      para("The analytical models embedded in the dashboard are derived from a doctoral thesis that underwent formal academic review at the University of Delhi. This includes the specific variable definitions, winsorisation thresholds, panel-robust standard error specifications, cross-validation strategies (PanelGroupKFold to prevent data leakage across firms), and model selection criteria. Replicating this methodology requires not just coding ability but deep familiarity with the capital structure literature, panel econometric theory, and Indian accounting standards. General-purpose financial platforms (Bloomberg, FactSet) lack the specialised academic expertise to develop these models internally. Fintech startups lack the econometric depth. This is not a feature that can be replicated by adding a regression function to an existing platform; it requires a complete analytical framework built from first principles."),

      heading3("Moat 2: Indian Market Data Depth"),
      para("The dashboard's curated dataset of 401 Indian firms across 24 years (2001-2024) represents a cleaned, validated, and lifecycle-classified panel that has been through the rigour of doctoral-level data preparation. Raw data from CMIE contains missing values, inconsistent classifications, mergers, delistings, and accounting standard changes (Indian GAAP to Ind-AS transition in 2016-17) that require expert handling. The dashboard's data pipeline addresses all of these issues. A competitor would need to invest 12-18 months in data cleaning and validation to achieve comparable data quality, and would still lack the lifecycle classification that structures every analysis."),

      heading3("Moat 3: Multi-Method Analytical Architecture"),
      para("The three-tier architecture (econometric, ML, advanced) is a structural differentiator because it addresses fundamentally different user needs simultaneously. Econometric models provide causal inference and theory testing (valued by academics and regulators). ML models provide predictive accuracy and non-linear pattern detection (valued by practitioners and investors). Survival and forecasting models provide forward-looking risk assessment (valued by credit analysts and CFOs). Building all three tiers, integrating them into a coherent interface, and ensuring methodological consistency across tiers requires a rare combination of academic econometrics, data science, and software engineering expertise."),

      heading3("Moat 4: Dynamic Interpretation Engine"),
      para("The automated interpretation system translates statistical output into finance-contextual language, explaining not just what the numbers are but what they mean for capital structure decisions. This capability is absent from every competitor evaluated in this section. Bloomberg provides data without interpretation. Stata provides statistics without context. CMIE provides figures without analysis. The interpretation engine encodes domain expertise from the capital structure literature (trade-off theory, pecking order theory, agency theory, market timing theory) and applies it dynamically to each analytical result. Replicating this requires both the statistical models (to generate results) and the domain knowledge (to interpret them), creating a compound barrier that is significantly harder to overcome than either alone."),

      spacer(),

      // Closing summary
      new Paragraph({
        spacing: { before: 200, after: 200 },
        border: {
          top: { style: BorderStyle.SINGLE, size: 4, color: ACCENT, space: 8 },
          bottom: { style: BorderStyle.SINGLE, size: 4, color: ACCENT, space: 8 },
        },
        children: [
          new TextRun({ text: "Summary. ", font: FONT, size: 22, bold: true, color: NAVY }),
          new TextRun({ text: "The commercial gap analysis demonstrates that the LifeCycle Leverage Dashboard occupies a unique and currently uncontested position in the market: the intersection of lifecycle-aware corporate finance analytics, multi-method modelling (econometric + ML + survival), Indian market depth, and accessible web-based delivery. No existing platform, from USD 200,000/year enterprise terminals to free academic tools, offers this combination. The competitive moat is grounded in methodological depth, data curation, multi-tier architecture, and dynamic interpretation, creating compound barriers that cannot be replicated by adding incremental features to existing platforms.", font: FONT, size: 22 }),
        ],
      }),
    ],
  }],
});

// ── Generate ──────────────────────────────────────────────────────
const outPath = path.resolve("c:/Users/hemas/Downloads/ProfSurProject/docs/Section_E_Commercial_Gap_Analysis.docx");
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outPath, buffer);
  console.log("Created: " + outPath);
  console.log("Size: " + (buffer.length / 1024).toFixed(1) + " KB");
});
