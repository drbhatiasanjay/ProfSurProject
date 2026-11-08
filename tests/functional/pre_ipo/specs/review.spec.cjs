const { test, expect, audit } = require('../support/fixtures.cjs');
test.beforeEach(async ({ ui }) => { await ui.open(); await ui.createCompany(); await ui.retain(); });
test('REV-001 @smoke accepted source-backed fact survives browser reload', async ({ ui }) => {
  await ui.review();
  await ui.page.reload(); await ui.open(); await ui.select('Company dossier', ui.company);
  await ui.tab('Attribute inventory');
  const searchBox = ui.page.getByLabel('Find an attribute or value', { exact: true });
  await searchBox.fill('history[0].cfo_cr');
  await searchBox.press('Enter');
  await expect(ui.page.getByText('1 matching rows.', { exact: false })).toBeVisible();
  const state = audit(['--name', ui.company, '--owner', ui.account.username]);
  expect(state.facts.filter(f => f.id === 'history[0].cfo_cr').at(-1).value).toBe('100');
});
for (const [id, overrides, error] of [
  ['REV-002', { confirm: false }, /Confirm inspection/],
  ['REV-003', { locator: '' }, /locator|source/i],
  ['REV-004', { quote: '' }, /quotation|quote|source/i],
  ['REV-005', { reason: '' }, /reason|required/i],
  ['REV-006', { context: { Period: 'NOT_ESTABLISHED' } }, /period|context/i],
  ['REV-007', { presence: 'NOT_DISCLOSED' }, /scope/i],
]) test(`${id} incomplete acceptance rejected`, async ({ ui }) => {
  await ui.review('100', { ...overrides, expectError: true });
  await expect(ui.page.getByTestId('stAlert').filter({ hasText: error })).toBeVisible();
  expect(audit(['--name', ui.company, '--owner', ui.account.username]).facts.filter(f => f.review === 'ACCEPTED')).toHaveLength(0);
});
test('REV-008 zero is a disclosed value, not missing', async ({ ui }) => {
  await ui.retain('zeros.pdf', `${ui.prefix} zeros`);
  await ui.review('0', { quote: 'Cash flow from operations 0.00' });
  const frozen = await ui.freeze();
  const fact = frozen.facts.find(f => f.id === 'history[0].cfo_cr');
  expect(Number(fact.value)).toBe(0); expect(fact.presence).toBe('OBSERVED_VALUE');
});
test('REV-009 negative cash flow remains negative in snapshot', async ({ ui }) => {
  await ui.retain('negative-values.pdf', `${ui.prefix} negative`);
  await ui.review('-100', { quote: 'Cash flow from operations -100.00' });
  const frozen = await ui.freeze(); expect(Number(frozen.facts.find(f => f.id === 'history[0].cfo_cr').value)).toBe(-100);
});
test('REV-010 diligence follow-up does not magically close evidence gap', async ({ ui }) => {
  await ui.review(); await ui.tab('Missing data & actions');
  await ui.page.getByLabel('Question or gap identifier', { exact: true }).fill(`${ui.prefix} missing interest`);
  await ui.page.getByLabel('Evidence to request and why', { exact: true }).fill('Obtain interest classification note before FCFF calculation');
  await ui.page.getByRole('button', { name: 'Record follow-up', exact: true }).click();
  await expect(ui.page.getByText(/evidence gap remains open/)).toBeVisible();
  await expect(ui.page.getByTestId('stDataFrame').last()).toBeVisible();
});
test('REV-011 analysis displays interpretation, source binding and next action', async ({ ui }) => {
  await ui.review(); await ui.tab('Analysis & snapshots');
  const summaries = ui.page.locator('[data-testid=stExpander] summary').filter({ hasText: /FY24/ });
  await expect(summaries.first()).toBeVisible(); await summaries.first().click();
  await expect(ui.page.getByText(/^Interpretation:/).first()).toBeVisible();
  await expect(ui.page.getByText(/^Next action:/).first()).toBeVisible();
  await expect(ui.page.getByText(/^Fact bindings:/).first()).toBeVisible();
  const frozen = await ui.freeze(); expect(frozen.assessment.gaps.length).toBeGreaterThan(0);
});
test('REV-012 accepted snapshot handoff preserves company and leaves assumptions blank', async ({ ui }) => {
  await ui.review(); const frozen = await ui.freeze();
  await ui.page.getByRole('button', { name: 'Prepare this snapshot for the decision workbench', exact: true }).click();
  await ui.open('Decision-depth workbench');
  await ui.page.getByRole('button', { name: 'Apply prepared evidence case', exact: true }).click();
  await expect(ui.page.getByLabel('Company legal name', { exact: true })).toHaveValue(ui.company);
  await ui.expand(/Optional model inputs/); await ui.select('Analysis', 'cash_flow_bridge');
  await expect(ui.page.getByLabel('Cfo', { exact: true })).toHaveValue(/100/);
  await expect(ui.page.getByLabel('Cash interest', { exact: true })).toHaveValue('');
  expect(frozen.id).toBeTruthy();
});
