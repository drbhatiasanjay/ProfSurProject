const { expect } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');
class UI {
  constructor(page, session, info, account, theme) {
    Object.assign(this, { page, session, info, account, theme });
    this.prefix = `E2E ${session.runId} ${info.project.name} ${info.title.match(/[A-Z]+-\d+/)?.[0] || 'case'}`;
  }
  async login() {
    const resumeTrace = this.tracing === true;
    if (resumeTrace) {
      await this.page.context().tracing.stop({ path: this.info.outputPath(`pre-reauth-${Date.now()}.zip`) });
      this.tracing = false;
    }
    await this.page.goto(`${this.session.baseURL}/?theme=${this.theme}`, { waitUntil: 'domcontentloaded' });
    try {
      await this.page.getByLabel('Username or email', { exact: true }).fill(this.account.username);
      await this.page.locator('input[type=password]').fill(this.account.password);
      await this.page.getByRole('button', { name: /^Sign In/i }).click();
    } catch {
      throw new Error('Isolated test login control failed; credential values suppressed. Inspect the login form and selectors.');
    }
    await expect(this.page.getByRole('button', { name: /Sign Out/i })).toBeVisible({ timeout: 60000 });
    if (resumeTrace) {
      await this.page.context().tracing.start({ screenshots: true, snapshots: true, sources: false });
      this.tracing = true;
    }
  }
  async open(workspace = 'Facts & evidence review') {
    const preIpoLink = this.page.getByRole('link', { name: /Pre-IPO DRHP Intelligence/ }).first();
    try {
      await preIpoLink.waitFor({ state: 'visible', timeout: 5000 });
    } catch {
      if (await this.page.getByLabel('Username or email').isVisible().catch(() => false) ||
          await this.page.getByRole('button', { name: /Sign In/i }).isVisible().catch(() => false)) {
        await this.login();
      }
    }
    await this.page.getByRole('link', { name: /Pre-IPO DRHP Intelligence/ }).first().click();
    await this.page.getByText(workspace, { exact: true }).click();
    const title = workspace === 'Facts & evidence review' ? 'Company facts & evidence' :
      workspace === 'Decision-depth workbench' ? 'Pre-IPO decision workbench' : null;
    if (title) await expect(this.page.getByRole('heading', { name: title, exact: true })).toBeVisible();
    await this.healthy();
  }
  async healthy() {
    await expect(this.page.getByTestId('stException')).toHaveCount(0);
    const visibleCode = this.page.locator('pre code').filter({ hasText: /<div\s+(?:style|class)=/ });
    await expect(visibleCode, 'Raw HTML leaked as code').toHaveCount(0);
  }
  async expand(name) {
    const summary = this.page.locator('[data-testid=stExpander] summary').filter({ hasText: name });
    await expect(summary).toHaveCount(1);
    if (await summary.getAttribute('aria-expanded') === 'false' || !await summary.evaluate(e => e.parentElement.open)) await summary.click();
    return summary.locator('..');
  }
  async select(label, option) {
    const widget = this.page.getByTestId('stSelectbox').filter({ has: this.page.locator('label').filter({ hasText: new RegExp(`^${escapeRegex(label)}$`) }) });
    await expect(widget, `Selectbox ${label}`).toHaveCount(1);
    await widget.locator('[data-baseweb=select]').click();
    const choice = this.page.getByRole('option', { name: option, exact: typeof option === 'string' });
    if (!await choice.count() && typeof option === 'string') await widget.locator('input').fill(option);
    await choice.click();
  }
  async firstOption(label) {
    const widget = this.page.getByTestId('stSelectbox').filter({ has: this.page.locator('label').filter({ hasText: new RegExp(`^${escapeRegex(label)}$`) }) });
    await widget.locator('[data-baseweb=select]').click();
    const choice = this.page.getByRole('option').filter({ hasText: /.+/ }).filter({ hasNotText: 'Choose a source' }).last();
    const value = await choice.innerText();
    await choice.click();
    return value;
  }
  async tab(name) { await this.page.getByRole('tab', { name, exact: true }).click(); await this.healthy(); }
  async createCompany(suffix = '', legalName = null) {
    this.company = legalName || `${this.prefix}${suffix}`;
    await this.tab('Sources & review');
    await this.expand(/Add a private company/);
    await this.page.getByLabel('Company legal name', { exact: true }).fill(this.company);
    await this.page.getByLabel('Sector / business description', { exact: true }).fill('Synthetic functional acceptance only');
    await this.page.getByLabel('Reporting periods (comma separated)', { exact: true }).fill('FY24');
    await this.page.getByRole('button', { name: 'Create private company', exact: true }).click();
    await expect(this.page.getByTestId('stSelectbox').filter({ hasText: 'Company dossier' })).toContainText(this.company);
    await this.tab('Sources & review');
    const initialize = this.page.getByRole('button', { name: 'Start private review of this data', exact: true });
    if (await initialize.count()) {
      await initialize.click();
      await expect(initialize).toHaveCount(0);
    }
    return this.company;
  }
  async retain(file = 'known-values.pdf', title = `${this.prefix} filing`, options = {}) {
    await this.tab('Sources & review');
    await this.expand(/Retain an exact filing/);
    const form = this.page.getByTestId('stForm').filter({ has: this.page.getByRole('button', { name: 'Retain private PDF', exact: true }) });
    await form.locator('input[type=file]').setInputFiles(path.isAbsolute(file) ? file : path.join(this.session.fixtureDir, file));
    await form.getByLabel('Source title', { exact: true }).fill(title);
    await this.select('Filing type', options.type || 'DRHP');
    await form.getByLabel('Exact document version/date label', { exact: true }).fill(options.version || 'Synthetic v1');
    await form.getByLabel('Official source URL (recorded, not fetched)', { exact: true }).fill('https://example.invalid/synthetic.pdf');
    await form.getByLabel('Retention and use permission / policy', { exact: true }).fill(options.rights ?? 'Synthetic test document; private local acceptance');
    await form.getByRole('button', { name: 'Retain private PDF', exact: true }).click();
    if (!options.expectError) {
      await expect(this.page.getByText('Original bytes retained privately with a content hash.', { exact: true })).toBeVisible();
      await this.select('Retained source', new RegExp(escapeRegex(title)));
    }
    return title;
  }
  async processDocument(pages = 1) {
    const structured = this.page.getByRole('button', { name: /^(Run.*structured.*extraction|Process document|Extract document)$/i });
    if (await structured.count() === 1) {
      await structured.click();
      await expect(this.page.getByTestId('stException')).toHaveCount(0);
      return;
    }
    await this.expand(/Native extraction scope/);
    for (let first = 1; first <= pages; first += 20) {
      await this.page.getByLabel('PDF page to inspect (1-based)', { exact: true }).fill(String(first));
      await this.page.getByLabel('Pages in this batch', { exact: true }).fill(String(Math.min(20, pages - first + 1)));
      await this.page.getByRole('button', { name: 'Extract selected native pages', exact: true }).click();
      await expect(this.page.getByText(/Only the selected pages were processed/)).toBeVisible();
    }
  }
  async review(value = '100', overrides = {}) {
    await this.tab('Sources & review');
    const id = overrides.id || 'history[0].cfo_cr';
    const selector = this.page.getByTestId('stSelectbox').filter({ has: this.page.locator('label').filter({ hasText: /^Fact to review$/ }) });
    await selector.locator('[data-baseweb=select]').click();
    const existing = this.page.getByRole('option', { name: id, exact: true });
    const edit = await existing.count() > 0;
    await (edit ? existing : this.page.getByRole('option', { name: 'New attribute', exact: true })).click();
    if (!edit) await this.page.getByLabel('Attribute identifier', { exact: true }).fill(id);
    await this.page.getByLabel('Interpreted value', { exact: true }).fill(String(value));
    await this.select('Presence', overrides.presence || 'OBSERVED_VALUE');
    await this.select('Origin', overrides.origin || 'FILING_FACT');
    await this.select('Review decision', overrides.review || 'ACCEPTED');
    const context = { Entity: this.company, Period: 'FY24', Duration: 'ANNUAL', Basis: 'CONSOLIDATED', Framework: 'IND_AS', Currency: 'INR', Unit: 'crore', Definition: 'Cash flow from operations', ...overrides.context };
    for (const [key, v] of Object.entries(context)) await this.page.getByLabel(key, { exact: true }).fill(v);
    await this.page.getByLabel('Table, printed page label and footnote locator', { exact: true }).fill(overrides.locator ?? 'Table 1, PDF page 1');
    await this.page.getByLabel('Exact source quotation including label/unit context', { exact: true }).fill(overrides.quote ?? 'FY24 consolidated IND AS INR crore: CFO 100');
    await this.page.getByLabel('Why this interpretation or decision is appropriate', { exact: true }).fill(overrides.reason ?? 'Synthetic source verified for functional test');
    if (overrides.scope) await this.page.getByLabel('Search / applicability scope (required for non-disclosure or N/A)', { exact: true }).fill(overrides.scope);
    const confirmLabel = this.page.locator('label').filter({ hasText: 'I checked the selected PDF page, units, period and reporting basis' });
    const chk = this.page.getByRole('checkbox', { name: 'I checked the selected PDF page, units, period and reporting basis', exact: true });
    const shouldCheck = overrides.confirm !== false;
    const isChecked = await chk.isChecked().catch(() => false);
    if (isChecked !== shouldCheck) {
      await confirmLabel.scrollIntoViewIfNeeded();
      await confirmLabel.click();
    }
    await this.page.getByRole('button', { name: 'Submit fact review', exact: true }).click();
    if (!overrides.expectError) {
      await this.tab('Attribute inventory');
      const searchBox = this.page.getByLabel('Find an attribute or value', { exact: true });
      await searchBox.fill(overrides.id || 'history[0].cfo_cr');
      await searchBox.press('Enter');
      // Streamlit grids use canvas; never infer a cell value from nonexistent DOM text.
      await expect(this.page.getByTestId('stDataFrame').first()).toBeVisible();
      await expect(this.page.getByText('1 matching rows.', { exact: false })).toBeVisible();
    }
  }
  async freeze() {
    await this.tab('Analysis & snapshots');
    await this.page.getByRole('button', { name: 'Freeze evidence snapshot', exact: true }).click();
    await expect(this.page.getByText(/Immutable snapshot saved/)).toBeVisible();
    return this.downloadJSON('Download evidence JSON');
  }
  async download(name, filename) {
    const pending = this.page.waitForEvent('download');
    await this.page.getByRole('button', { name, exact: true }).click();
    const dl = await pending;
    expect(await dl.failure()).toBeNull();
    const target = this.info.outputPath(`${Date.now()}-${require('node:crypto').randomUUID().slice(0, 8)}-${filename || dl.suggestedFilename()}`);
    await dl.saveAs(target);
    await this.info.attach(name, { path: target });
    return target;
  }
  async downloadJSON(name) { return JSON.parse(fs.readFileSync(await this.download(name, 'evidence.json'), 'utf8')); }
  async applyCase(bundle) {
    await this.open('Decision-depth workbench');
    await this.expand(/Advanced case editor/);
    await this.page.getByLabel('Complete case JSON', { exact: true }).fill(typeof bundle === 'string' ? bundle : JSON.stringify(bundle));
    await this.page.getByRole('button', { name: 'Validate and apply case', exact: true }).click();
  }
  async runCase(bundle) {
    await this.applyCase(bundle);
    await this.page.getByRole('button', { name: 'Run decision assessment', exact: true }).click();
    await expect(this.page.getByRole('heading', { name: /Interpretation and action/ })).toBeVisible();
    await this.healthy();
    return this.downloadJSON('Download evidence and results JSON');
  }
  async deleteCompany() {
    await this.tab('Sources & review');
    await this.expand(/Delete Private Company Package/);
    await expect(this.page.getByRole('button', { name: 'Delete private company', exact: true })).toBeDisabled();
    const delLabel = this.page.locator('label').filter({ hasText: 'I confirm permanent deletion of this private company and all dependent records' });
    const chk = this.page.getByRole('checkbox', { name: 'I confirm permanent deletion of this private company and all dependent records', exact: true });
    if (!await chk.isChecked().catch(() => false)) {
      await delLabel.scrollIntoViewIfNeeded();
      await delLabel.click();
    }
    await this.page.getByRole('button', { name: 'Delete private company', exact: true }).click();
    await expect(this.page.getByTestId('stSelectbox').filter({ hasText: 'Company dossier' })).not.toContainText(this.company);
  }
  async restart() {
    const control = JSON.parse(fs.readFileSync(process.env.PROFSUR_E2E_CONTROL, 'utf8'));
    // Node-side request keeps the disposable control credential out of browser traces.
    const response = await fetch(control.url, { method: 'POST', headers: { Authorization: control.token }, signal: AbortSignal.timeout(90000) });
    expect(response.ok, 'Owned isolated server restart').toBeTruthy();
    await this.login();
  }
}
function escapeRegex(text) { return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
module.exports = { UI };
