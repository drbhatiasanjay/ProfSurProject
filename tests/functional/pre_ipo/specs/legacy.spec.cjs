const { test, expect } = require('../support/fixtures.cjs');
const dossiers = ['NTPC Green', 'Mankind Pharma', 'Afcons Infrastructure', 'Swiggy', 'Tata Technologies'];
for (const [index, name] of dossiers.entries()) test(`LEG-00${index + 1} ${name} terminal, commentary and workpapers render`, async ({ ui }) => {
  await ui.open('Existing Pre-IPO terminal');
  await ui.select('Active Pre-IPO Deal Dossier', new RegExp(name, 'i'));
  for (const title of [/Company Overview/, /Investor Questions/, /Detailed Workpapers/, /CMIE Reference/, /IC Stance/]) {
    const tab = ui.page.getByRole('tab', { name: title });
    await expect(tab).toHaveCount(1); await tab.click(); await ui.healthy();
  }
  await ui.page.getByRole('tab', { name: /Detailed Workpapers/ }).click();
  for (const title of [/Financials.*Proceeds/, /Indebtedness.*Maturity/, /Stress Testing/, /Valuation.*Peers/]) {
    await ui.page.getByRole('tab', { name: title }).click(); await ui.healthy();
    await expect(ui.page.getByText(/Quantitative Observation.*What You See/i).first()).toBeVisible();
  }
});
for (const [index, persona] of ['CFO', 'Lender', 'Institutional Equity', 'Retail Investor', 'Board', 'Compliance'].entries())
test(`LEG-01${index} ${persona} perspective has questions and actions`, async ({ ui }) => {
  await ui.open('Existing Pre-IPO terminal'); await ui.select('Decision Persona Lens', new RegExp(persona, 'i'));
  await ui.page.getByRole('tab', { name: /Investor Questions/ }).click();
  await expect(ui.page.getByText(/question|thesis/i).first()).toBeVisible();
  await ui.page.getByRole('tab', { name: /IC Stance/ }).click();
  await expect(ui.page.getByText(/action|recommend|diligence/i).first()).toBeVisible(); await ui.healthy();
});
test('LEG-020 visual diligence path and decision matrix expose source drill-down', async ({ ui }) => {
  await ui.open('Existing Pre-IPO terminal');
  // Required feature gate: absence is a real acceptance failure, never a silent skip.
  await expect(ui.page.getByText(/diligence (path|funnel)/i).first()).toBeVisible();
  await expect(ui.page.getByText(/decision matrix/i).first()).toBeVisible();
  await expect(ui.page.getByRole('button', { name: /source|evidence|drill.down/i }).first()).toBeVisible();
});
