const { test, expect, audit } = require('../support/fixtures.cjs');
const { UI } = require('../support/ui.cjs');
const fs = require('node:fs');
function state(ui, ids = [], cases = []) {
  return audit(['--name', ui.company, '--owner', ui.account.username, ...ids.flatMap(id => ['--company-id', id]), ...cases.flatMap(id => ['--case-id', id])]);
}
test.beforeEach(async ({ ui }) => { await ui.open(); await ui.createCompany(); await ui.retain(); await ui.review(); });
test('LIFE-001 withdrawal invalidates current reliance and survives restart', async ({ ui }) => {
  const before = await ui.freeze();
  expect(before.assessment.accepted_fact_revisions['history[0].cfo_cr']).toBeTruthy();
  await ui.tab('Sources & review'); await ui.expand(/Document Lifecycle/);
  await ui.page.getByLabel('Withdrawal reason', { exact: true }).fill('Synthetic acceptance withdrawal');
  await ui.page.getByRole('button', { name: 'Withdraw Document', exact: true }).click();
  await ui.healthy();
  const after = await ui.freeze();
  expect(after.assessment.accepted_fact_revisions['history[0].cfo_cr']).toBeUndefined();
  await ui.restart(); await ui.open(); await ui.select('Company dossier', ui.company);
  const restored = await ui.freeze();
  expect(restored.assessment.accepted_fact_revisions['history[0].cfo_cr']).toBeUndefined();
});
test('LIFE-002 source delete requires confirmation, purges copies and preserves companion', async ({ ui }) => {
  const original = state(ui).documents[0];
  await ui.retain('companion.pdf', `${ui.prefix} companion`, { type: 'Other evidence' });
  await ui.select('Retained source', new RegExp(`${ui.prefix} filing`));
  await ui.expand(/Document Lifecycle/);
  await expect(ui.page.getByRole('button', { name: 'Delete Document', exact: true })).toBeDisabled();
  const docLabel = ui.page.locator('label').filter({ hasText: 'Confirm permanent deletion of THIS document only' });
  await docLabel.scrollIntoViewIfNeeded();
  await docLabel.click();
  await ui.page.getByRole('button', { name: 'Delete Document', exact: true }).click();
  const after = state(ui);
  expect(after.documents).toHaveLength(1);
  expect(after.documents[0].title).toContain('companion');
  expect(after.facts.some(f => f.source?.id === original.id), 'Deleted source copied into fact history').toBe(false);
});
test('LIFE-003 delete and identical reupload cannot resurrect acceptance', async ({ ui }) => {
  const title = `${ui.prefix} filing`;
  await ui.tab('Sources & review'); await ui.expand(/Document Lifecycle/);
  const docLabel = ui.page.locator('label').filter({ hasText: 'Confirm permanent deletion of THIS document only' });
  await docLabel.scrollIntoViewIfNeeded();
  await docLabel.click();
  await ui.page.getByRole('button', { name: 'Delete Document', exact: true }).click();
  await ui.retain('known-values.pdf', title);
  const after = await ui.freeze();
  expect(after.assessment.accepted_fact_revisions['history[0].cfo_cr']).toBeUndefined();
});
test('LIFE-004 @smoke company delete, reload and same-name reingest remain clean', async ({ ui }) => {
  await ui.freeze();
  const before = state(ui); const oldName = ui.company;
  await ui.deleteCompany();
  const after = state(ui, before.companies);
  expect(after.companies).toHaveLength(0);
  for (const [table, count] of Object.entries(after.counts)) {
    if (table === 'pre_ipo_tombstones' || table === 'pre_ipo_jobs') continue; // minimal lifecycle metadata only; inspect retention separately
    expect(count, `${table} orphan after company delete`).toBe(0);
  }
  await ui.restart(); await ui.open();
  await ui.page.getByTestId('stSelectbox').filter({ hasText: 'Company dossier' }).locator('[data-baseweb=select]').click();
  await expect(ui.page.getByRole('option', { name: oldName, exact: true })).toHaveCount(0);
  await ui.page.keyboard.press('Escape');
  await ui.createCompany(); expect(ui.company).toBe(oldName);
  await ui.retain(); const recreated = await ui.freeze();
  expect(recreated.assessment.accepted_fact_revisions['history[0].cfo_cr']).toBeUndefined();
});
test('LIFE-005 private issuer is absent for another owner', async ({ ui, browser }) => {
  const accounts = JSON.parse(fs.readFileSync(ui.session.credentialsFile, 'utf8'));
  const other = accounts[ui.account.username === 'drbhatia' ? 'skumar' : 'drbhatia'];
  const context = await browser.newContext();
  try {
    const page = await context.newPage(); const second = new UI(page, ui.session, ui.info, other, ui.theme);
    await second.login(); await second.open();
    await page.getByTestId('stSelectbox').filter({ hasText: 'Company dossier' }).locator('[data-baseweb=select]').click();
    await expect(page.getByRole('option', { name: ui.company, exact: true })).toHaveCount(0);
    await expect(page.getByTestId('stException')).toHaveCount(0);
  } finally { await context.close(); }
});
test('LIFE-006 stale browser review after company deletion is rejected', async ({ ui, browser }) => {
  const context = await browser.newContext();
  try {
    const second = new UI(await context.newPage(), ui.session, ui.info, ui.account, ui.theme);
    await second.login(); await second.open(); await second.select('Company dossier', ui.company);
    second.company = ui.company;
    await second.tab('Sources & review');
    await second.select('Retained source', new RegExp(`${ui.prefix} filing`));
    await second.select('Fact to review', 'New attribute');
    await second.page.getByLabel('Attribute identifier', { exact: true }).fill('history[0].ebitda_cr');
    await ui.deleteCompany();
    await second.page.getByLabel('Interpreted value', { exact: true }).fill('234');
    await second.page.getByLabel('Why this interpretation or decision is appropriate', { exact: true }).fill('Stale browser must not recreate deleted company');
    await second.page.getByRole('button', { name: 'Submit fact review', exact: true }).click();
    await expect(second.page.getByTestId('stAlert').filter({ hasText: /deleted|stale|changed|no longer|reload/i })).toBeVisible();
    expect(state(ui).companies).toHaveLength(0);
  } finally { await context.close(); }
});
test('LIFE-007 company deletion removes handoff-linked saved decisions, actions and cached export', async ({ ui }) => {
  await ui.freeze();
  await ui.page.getByRole('button', { name: 'Prepare this snapshot for the decision workbench', exact: true }).click();
  await ui.open('Decision-depth workbench');
  await ui.page.getByRole('button', { name: 'Apply prepared evidence case', exact: true }).click();
  await ui.page.getByRole('button', { name: 'Run decision assessment', exact: true }).click();
  await ui.page.getByRole('button', { name: 'Save private case revision', exact: true }).click();
  await expect(ui.page.getByText('Saved revision 1', { exact: true })).toBeVisible();
  await ui.page.getByLabel('Rationale and next action', { exact: true }).fill('Synthetic decision rationale must follow deletion policy');
  await ui.page.getByRole('button', { name: 'Record action on saved revision', exact: true }).click();
  await expect(ui.page.getByText(/Action recorded against/)).toBeVisible();
  const before = state(ui); expect(before.case_ids).toHaveLength(1);
  await ui.open(); await ui.select('Company dossier', ui.company); await ui.deleteCompany();
  const after = state(ui, before.companies, before.case_ids);
  expect(after.case_ids).toHaveLength(0);
  expect(after.counts.remembered_decision_actions).toBe(0);
  expect(after.counts.pre_ipo_decision_versions || 0).toBe(0);
  await ui.open('Decision-depth workbench');
  await expect(ui.page.getByRole('button', { name: 'Download evidence and results JSON', exact: true })).toHaveCount(0);
});
test('LIFE-008 stale review from an old company incarnation cannot write into recreated issuer', async ({ ui, browser }) => {
  const context = await browser.newContext();
  try {
    const second = new UI(await context.newPage(), ui.session, ui.info, ui.account, ui.theme);
    await second.login(); await second.open(); await second.select('Company dossier', ui.company);
    await second.tab('Sources & review'); await second.select('Fact to review', 'New attribute');
    await second.page.getByLabel('Attribute identifier', { exact: true }).fill('late-stale-incarnation-note');
    await second.page.getByLabel('Interpreted value', { exact: true }).fill('must never persist');
    await second.page.getByLabel('Why this interpretation or decision is appropriate', { exact: true }).fill('Old form was opened before deletion');
    await ui.deleteCompany(); await ui.createCompany(); await ui.retain();
    await second.page.getByRole('button', { name: 'Submit fact review', exact: true }).click();
    await expect(second.page.getByTestId('stAlert').filter({ hasText: /stale|generation|changed|reload|deleted/i })).toBeVisible();
    expect(state(ui).facts.some(f => f.id === 'late-stale-incarnation-note')).toBe(false);
  } finally { await context.close(); }
});
