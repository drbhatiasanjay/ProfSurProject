const path = require('node:path');
const { test, expect, audit } = require('../support/fixtures.cjs');
test.beforeEach(async ({ ui }) => { await ui.open(); await ui.createCompany(); });
test('ING-001 @smoke retain original and inspect correct source bytes', async ({ ui }) => {
  await ui.retain();
  const source = await ui.download('Download owned source PDF', 'original.pdf');
  const fs = require('node:fs');
  expect(fs.readFileSync(source).equals(fs.readFileSync(path.join(ui.session.fixtureDir, 'known-values.pdf')))).toBe(true);
  await expect(ui.page.getByLabel('Source page text (inert, read-only)', { exact: true })).toHaveValue(/Revenue from operations 1234/);
});
for (const [id, file, error] of [
  ['ING-002', 'not-a-pdf.pdf', /PDF|invalid|format/i], ['ING-003', 'corrupt.pdf', /PDF|invalid|corrupt|read/i],
  ['ING-004', 'encrypted.pdf', /encrypt|password|unsupported/i], ['ING-005', 'oversize.pdf', /25|size|large|limit/i],
]) test(`${id} rejects ${file} without creating a retained source`, async ({ ui }) => {
  await ui.retain(file, `${ui.prefix} invalid`, { expectError: true });
  await expect(ui.page.getByTestId('stAlert').filter({ hasText: error })).toBeVisible();
  expect(audit(['--name', ui.company, '--owner', ui.account.username]).documents).toHaveLength(0);
});
test('ING-006 missing retention rights rejected', async ({ ui }) => {
  await ui.retain('known-values.pdf', `${ui.prefix} rights`, { rights: '', expectError: true });
  await expect(ui.page.getByTestId('stAlert').filter({ hasText: /permission|rights|policy|required/i })).toBeVisible();
  expect(audit(['--name', ui.company, '--owner', ui.account.username]).documents).toHaveLength(0);
});
test('ING-007 duplicate retain is idempotent', async ({ ui }) => {
  const title = `${ui.prefix} duplicate`;
  await ui.retain('known-values.pdf', title); await ui.retain('known-values.pdf', title);
  expect(audit(['--name', ui.company, '--owner', ui.account.username]).documents).toHaveLength(1);
});
test('ING-008 separate companion source coexists', async ({ ui }) => {
  await ui.retain(); await ui.retain('companion.pdf', `${ui.prefix} companion`, { type: 'Other evidence' });
  expect(audit(['--name', ui.company, '--owner', ui.account.username]).documents).toHaveLength(2);
});
test('ING-009 selected-page extraction scope is explicit and bounded', async ({ ui }) => {
  await ui.retain('multi-page.pdf'); await ui.expand(/Native extraction scope/);
  await ui.page.getByLabel('PDF page to inspect (1-based)', { exact: true }).fill('21');
  await ui.page.getByLabel('Pages in this batch', { exact: true }).fill('3');
  await ui.page.getByRole('button', { name: 'Extract selected native pages', exact: true }).click();
  await expect(ui.page.getByText(/Only the selected pages were processed/)).toBeVisible();
  await expect(ui.page.getByLabel('Source page text (inert, read-only)', { exact: true })).toHaveValue(/SYNTHETIC PAGE 21/);
});
test('ING-010 scanned page produces OCR output or explicit gap, never a clean empty success', async ({ ui }) => {
  await ui.retain('scanned.pdf'); await ui.expand(/Native extraction scope/);
  await ui.page.getByRole('button', { name: 'Extract selected native pages', exact: true }).click();
  await expect(ui.page.getByText(/COMPLETED_WITH_GAPS|GAP-OCR-01/).first()).toBeVisible();
  expect(audit(['--name', ui.company, '--owner', ui.account.username]).facts.some(f => f.review === 'ACCEPTED')).toBe(false);
});
test('ING-011 original intake automatically exposes accurate candidates', async ({ ui }) => {
  // This intentionally exercises the original user's path, not ledger service inserts.
  await ui.page.getByText('Existing Pre-IPO terminal', { exact: true }).click();
  await ui.select('Active Pre-IPO Deal Dossier', /Ingest New DRHP/);
  await ui.page.getByLabel('Upload Draft Red Herring Prospectus (DRHP) PDF', { exact: true }).setInputFiles(path.join(ui.session.fixtureDir, 'known-values.pdf'));
  await ui.page.getByLabel('Company Name / Filing Entity', { exact: true }).fill(`${ui.company} original intake`);
  await ui.page.getByRole('button', { name: 'Run Automated Prospectus Extraction & Forensic Audit', exact: true }).click();
  await expect(ui.page.getByRole('heading', { name: 'Company facts & evidence', exact: true })).toBeVisible({ timeout: 120000 });
  const state = audit(['--name', `${ui.company} original intake`, '--owner', ui.account.username]);
  const latest = new Map(state.facts.map(f => [f.id, f]));
  for (const [field, value] of Object.entries({ revenue_ops_cr: 1234, ebitda_cr: 234, pat_cr: 89, cfo_cr: 100, net_worth_cr: 678 })) {
    const row = [...latest.values()].find(f => f.id.endsWith(`.${field}`));
    expect(row, `Candidate ${field}`).toBeTruthy();
    expect(Number(row.extraction_raw_value ?? row.raw_value)).toBe(value);
    expect(row.review).not.toBe('ACCEPTED');
  }
});
test('ING-012 source markup remains inert', async ({ ui }) => {
  let dialog = false; ui.page.on('dialog', async d => { dialog = true; await d.dismiss(); });
  await ui.retain('html-payload.pdf');
  await expect(ui.page.getByLabel('Source page text (inert, read-only)', { exact: true })).toHaveValue(/<script>/);
  expect(dialog).toBe(false);
});
for (const [id, file, attribute, value] of [
  ['ING-013', 'zeros.pdf', 'ebitda_cr', 0], ['ING-014', 'mixed-units.pdf', 'cfo_cr', 20],
  ['ING-015', 'negative-values.pdf', 'cfo_cr', -100],
]) test(`${id} original intake preserves zero, unit or sign semantics (${file})`, async ({ ui }) => {
  await ui.open('Existing Pre-IPO terminal'); await ui.select('Active Pre-IPO Deal Dossier', /Ingest New DRHP/);
  await ui.page.getByLabel('Upload Draft Red Herring Prospectus (DRHP) PDF', { exact: true }).setInputFiles(path.join(ui.session.fixtureDir, file));
  const name = `${ui.company} semantic intake`;
  await ui.page.getByLabel('Company Name / Filing Entity', { exact: true }).fill(name);
  await ui.page.getByRole('button', { name: 'Run Automated Prospectus Extraction & Forensic Audit', exact: true }).click();
  await expect(ui.page.getByRole('heading', { name: 'Company facts & evidence', exact: true })).toBeVisible({ timeout: 120000 });
  const facts = audit(['--name', name, '--owner', ui.account.username]).facts;
  const fact = facts.filter(f => f.id.endsWith(`.${attribute}`)).at(-1);
  expect(fact, `Expected ${attribute} candidate`).toBeTruthy();
  expect(Number(fact.extraction_raw_value ?? fact.value ?? fact.raw_value)).toBe(value);
  expect(fact.presence, 'A disclosed zero/sign/unit must not turn into missing').toBe('OBSERVED_VALUE');
});
