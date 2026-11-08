const { test, expect, audit } = require('../support/fixtures.cjs');
const { bundle } = require('../support/model-vectors.cjs');
const { spawnSync } = require('node:child_process');
const path = require('node:path');
test('DEC-010 identical analytical inputs produce identical results for a new researcher and admin', async ({ ui, browser }) => {
  const input = bundle(`E2E ${ui.session.runId} ROLE PARITY`, { cash_tax: { inputs: { taxable_profit: 100, rate: .25 } } });
  const original = await ui.runCase(input);
  const accounts = JSON.parse(require('node:fs').readFileSync(ui.session.credentialsFile, 'utf8'));
  const { UI } = require('../support/ui.cjs');
  const context = await browser.newContext({ acceptDownloads: true });
  try {
    const second = new UI(await context.newPage(), ui.session, ui.info,
      accounts[ui.account.username === 'e2e_new_researcher' ? 'drbhatia' : 'e2e_new_researcher'], ui.theme);
    await second.login();
    const other = await second.runCase(input);
    expect(other.context_hash).toBe(original.context_hash);
    expect(other.results).toEqual(original.results);
    expect(other.methodology_references).toEqual(original.methodology_references);
  } finally { await context.close(); }
});
test('DEC-001 @smoke save, restore and record a decision with rationale', async ({ ui }) => {
  const input = bundle(ui.prefix, { cash_tax: { inputs: { taxable_profit: 100, rate: .25 } } });
  const report = await ui.runCase(input);
  await ui.page.getByRole('button', { name: 'Save private case revision', exact: true }).click();
  await expect(ui.page.getByText('Saved revision 1', { exact: true })).toBeVisible();
  await ui.page.getByLabel('Rationale and next action', { exact: true }).fill(`${ui.prefix} obtain audited tax losses before commitment`);
  await ui.page.getByRole('button', { name: 'Record action on saved revision', exact: true }).click();
  await expect(ui.page.getByText(/Action recorded against the immutable saved revision/)).toBeVisible();
  await ui.page.reload(); await ui.open('Decision-depth workbench');
  await ui.expand(/Import or restore a private case/);
  const saved = audit(['--name', ui.prefix, '--owner', ui.account.username]);
  expect(saved.case_ids).toHaveLength(1);
  await ui.select('Saved case', saved.case_ids[0]);
  await ui.page.getByRole('button', { name: 'Restore selected revision', exact: true }).click();
  const restored = await ui.downloadJSON('Download evidence and results JSON');
  expect(restored.context_hash).toBe(report.context_hash);
  expect(restored.results.cash_tax.data.cash_tax).toBe(25);
});
for (const [id, patch, error] of [
  ['DEC-002', { company: '' }, /company.*required/i], ['DEC-003', { as_of: 'not-a-date' }, /date|ISO|timestamp/i],
  ['DEC-004', { currency: '' }, /currency.*required/i], ['DEC-005', { schema_version: 999 }, /schema/i],
  ['DEC-006', { models: { nonexistent_method: { inputs: {} } } }, /model set/i],
]) test(`${id} invalid decision form reports recoverable validation`, async ({ ui }) => {
  await ui.applyCase({ ...bundle(ui.prefix), ...patch });
  await expect(ui.page.getByTestId('stAlert').filter({ hasText: error })).toBeVisible();
  await ui.healthy();
});
test('DEC-007 NaN JSON is rejected without crashing the application', async ({ ui }) => {
  await ui.applyCase('{"schema_version":1,"company":NaN}');
  await expect(ui.page.getByTestId('stAlert').filter({ hasText: /Non-finite|NaN/i })).toBeVisible();
});
test('DEC-008 unsaved assessment cannot receive recorded action', async ({ ui }) => {
  await ui.runCase(bundle(ui.prefix));
  await expect(ui.page.getByRole('button', { name: 'Record action on saved revision', exact: true })).toBeDisabled();
});
test('DEC-009 changing applied inputs invalidates prior report and exports', async ({ ui }) => {
  await ui.runCase(bundle(ui.prefix));
  await ui.page.getByLabel('Company legal name', { exact: true }).fill(`${ui.prefix} revised`);
  await ui.page.getByRole('button', { name: 'Apply company facts', exact: true }).click();
  await expect(ui.page.getByRole('button', { name: 'Download evidence and results JSON', exact: true })).toHaveCount(0);
});
test('EXP-001 JSON and PPTX contain matching case values, caveats and methodology references', async ({ ui }) => {
  const report = await ui.runCase(bundle(ui.prefix, { cash_flow_bridge: { inputs: { cfo: 100, cash_capex: 20, cash_interest: 10, realized_interest_tax_benefit: 2, cfo_includes_interest: true } } }));
  const pptx = await ui.download('Download decision deck', 'decision.pptx');
  const result = spawnSync(ui.session.python, [path.join(ui.session.suiteRoot, 'support/inspect_export.py'), pptx, ui.prefix, '88'], { encoding: 'utf8', windowsHide: true });
  expect(result.status, result.stderr || result.stdout).toBe(0);
  expect(report.methodology_references.length).toBeGreaterThan(0);
  expect(report.limitations.join(' ')).toMatch(/not empirical probabilities|not.*investment advice/i);
  // Text parity is automated. Rendered PPTX layout needs the review checklist, not a false visual pass.
});
