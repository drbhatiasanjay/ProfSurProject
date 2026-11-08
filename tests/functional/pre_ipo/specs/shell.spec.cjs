const { test, expect } = require('../support/fixtures.cjs');
test('UI-001 @smoke authenticated sidebar reaches evidence without initialization', async ({ ui }) => {
  await ui.open();
  await expect(ui.page.getByRole('heading', { name: 'Inspect existing data', exact: true })).toBeVisible();
  await expect(ui.page.getByTestId('stSelectbox').filter({ hasText: 'Company dossier' })).toBeVisible();
  await expect(ui.page.getByTestId('stDataFrame').first()).toBeVisible();
});
for (const tab of ['Attribute inventory', 'Sources & review', 'Conflicts & CMIE', 'Missing data & actions', 'Analysis & snapshots']) {
  test(`UI-00${2 + ['Attribute inventory', 'Sources & review', 'Conflicts & CMIE', 'Missing data & actions', 'Analysis & snapshots'].indexOf(tab)} ${tab} renders without raw HTML or exceptions`, async ({ ui }) => {
    await ui.open(); await ui.tab(tab); await expect(ui.page.getByRole('tab', { name: tab, exact: true })).toHaveAttribute('aria-selected', 'true');
  });
}
test('UI-007 search and empty results do not reset company selection', async ({ ui }) => {
  await ui.open();
  const selector = ui.page.getByTestId('stSelectbox').filter({ hasText: 'Company dossier' });
  const before = await selector.innerText();
  const searchBox = ui.page.getByLabel('Find an attribute or value', { exact: true });
  await searchBox.fill('NO_SUCH_ATTRIBUTE_7f6a');
  await searchBox.press('Enter');
  await expect(ui.page.getByText('0 matching rows.', { exact: false })).toBeVisible();
  await expect(selector).toHaveText(before);
});
test('UI-008 theme toggle preserves selected company and usable controls', async ({ ui }) => {
  await ui.open();
  const before = await ui.page.getByTestId('stSelectbox').filter({ hasText: 'Company dossier' }).innerText();
  const toggle = ui.page.locator('#navbar-theme-toggle-btn');
  await toggle.click();
  await expect(toggle).toContainText(ui.theme === 'dark' ? 'Dark Mode' : 'Light Mode');
  await expect(ui.page.getByTestId('stSelectbox').filter({ hasText: 'Company dossier' })).toHaveText(before);
  await ui.healthy();
});
test('UI-009 narrow desktop keeps navigation and main form usable', async ({ ui }) => {
  await ui.page.setViewportSize({ width: 1024, height: 800 });
  await ui.open();
  await expect(ui.page.getByRole('heading', { name: 'Company facts & evidence', exact: true })).toBeVisible();
  const overflow = await ui.page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2);
  expect(overflow, 'Whole-page horizontal overflow').toBe(false);
});
test('AUTH-001 viewer cannot publish and writers have enabled private-review entry', async ({ ui }) => {
  await ui.open(); await ui.tab('Sources & review');
  const action = ui.page.getByRole('button', { name: 'Start private review of this data', exact: true });
  if (ui.account.role === 'viewer') await expect(action).toBeDisabled();
  else await expect(action).toBeEnabled();
  await ui.open('Decision-depth workbench');
  for (const label of ['New private case', 'Run decision assessment']) {
    if (ui.account.role === 'viewer') await expect(ui.page.getByRole('button', { name: label, exact: true })).toBeDisabled();
    else await expect(ui.page.getByRole('button', { name: label, exact: true })).toBeEnabled();
  }
});
test('AUTH-002 sign out protects direct Pre-IPO navigation', async ({ ui }) => {
  await ui.open();
  await ui.page.getByRole('button', { name: /Sign Out/i }).click();
  await ui.page.goto(`${ui.session.baseURL}/pre_ipo_drhp`);
  await expect(ui.page.getByLabel('Username or email', { exact: true })).toBeVisible();
  await expect(ui.page.getByRole('heading', { name: 'Company facts & evidence', exact: true })).toHaveCount(0);
});
