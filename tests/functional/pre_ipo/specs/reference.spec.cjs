const { test, expect } = require('../support/fixtures.cjs');
const path = require('node:path');
test.beforeEach(async ({ ui }) => { await ui.open(); await ui.createCompany(); await ui.retain(); await ui.review(); await ui.tab('Conflicts & CMIE'); });
test('CMIE-001 missing catalogue gives recoverable validation', async ({ ui }) => {
  await ui.page.getByRole('button', { name: 'Register reference version', exact: true }).click();
  await expect(ui.page.getByTestId('stAlert').filter({ hasText: /Choose a reference file/ })).toBeVisible();
});
test('CMIE-002 authorized catalogue is visible as candidate, not verified company coverage', async ({ ui }) => {
  const form = ui.page.getByTestId('stForm').filter({ has: ui.page.getByRole('button', { name: 'Register reference version', exact: true }) });
  await form.locator('input[type=file]').setInputFiles(path.join(ui.session.fixtureDir, 'catalogue.csv'));
  await form.getByLabel('Catalogue version / retrieval date', { exact: true }).fill(`E2E ${ui.session.runId} synthetic catalogue v1`);
  await form.getByLabel('Reference permitted-use declaration', { exact: true }).fill('Synthetic catalogue only; no CMIE licensed observations');
  await form.getByRole('button', { name: 'Register reference version', exact: true }).click();
  await expect(ui.page.getByText(/Reference registered privately/)).toBeVisible();
  await expect(ui.page.getByLabel('Find vendor field / indicator', { exact: true })).toBeVisible();
  await ui.page.getByLabel('Find vendor field / indicator', { exact: true }).fill('CFO');
  await expect(ui.page.getByText(/No company coverage denominator is inferred/)).toBeVisible();
  await ui.select('Attribute for reference candidate', 'history[0].cfo_cr');
  await ui.select('Vendor table', 'Synthetic');
  await ui.page.getByLabel('Exact vendor field name', { exact: true }).fill('CFO');
  await ui.page.getByLabel('Candidate mapping rationale and definition gaps', { exact: true }).fill('Synthetic name match only; definition and licensed values not established');
  await ui.page.getByRole('button', { name: 'Record table-qualified candidate', exact: true }).click();
  await expect(ui.page.getByText(/DEFINITION_REQUIRED/).first()).toBeVisible();
});
test('CMIE-003 empty reference permissions cannot be registered', async ({ ui }) => {
  const form = ui.page.getByTestId('stForm').filter({ has: ui.page.getByRole('button', { name: 'Register reference version', exact: true }) });
  await form.locator('input[type=file]').setInputFiles(path.join(ui.session.fixtureDir, 'catalogue.csv'));
  await form.getByLabel('Catalogue version / retrieval date', { exact: true }).fill('Synthetic v1');
  await form.getByRole('button', { name: 'Register reference version', exact: true }).click();
  await expect(ui.page.getByTestId('stAlert').filter({ hasText: /permission|rights|use|required/i })).toBeVisible();
});
