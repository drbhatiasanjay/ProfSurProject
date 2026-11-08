const { test, expect } = require('../support/fixtures.cjs');
const { vectors, bundle, dcf } = require('../support/model-vectors.cjs');
for (const [index, [method, good, goodState, expected, bad, badState]] of vectors.entries()) {
  test(`MOD-${String(index * 2 + 1).padStart(3, '0')} ${method}: independently calculated output and interpretation`, async ({ ui }) => {
    const report = await ui.runCase(bundle(ui.prefix, { [method]: { inputs: good, evidence_ids: [] } }));
    const result = report.results[method];
    expect(result.state).toBe(goodState);
    for (const [key, value] of Object.entries(expected)) {
      const actual = key.split('.').reduce((v, k) => v?.[k], result.data);
      if (typeof value === 'number') expect(actual, key).toBeCloseTo(value, 5);
      else expect(actual, key).toBe(value);
    }
    expect(result.question.length).toBeGreaterThan(10);
    expect(result.interpretation.length).toBeGreaterThan(30);
    expect(result.next_action.length).toBeGreaterThan(15);
    expect(result.evidence_status).toBe('ASSUMPTIONS_OR_UNVERIFIED_INPUTS');
    const detail = await ui.expand(new RegExp(method.replaceAll('_', ' '), 'i'));
    await expect(detail.getByText(result.interpretation, { exact: true }).first()).toBeVisible();
    await expect(detail.getByText(`Next action: ${result.next_action}`, { exact: true }).first()).toBeVisible();
    await expect(detail.getByText(/Source support|ASSUMPTIONS_OR_UNVERIFIED_INPUTS/i).first()).toBeVisible();
  });
  test(`MOD-${String(index * 2 + 2).padStart(3, '0')} ${method}: rejects or qualifies adverse inputs`, async ({ ui }) => {
    const report = await ui.runCase(bundle(ui.prefix, { [method]: { inputs: bad, evidence_ids: [] } }));
    expect(report.results[method].state).toBe(badState);
    expect(report.results[method].next_action.length).toBeGreaterThan(15);
  });
}
test('MOD-045 no supplied inputs means no fabricated model results', async ({ ui }) => {
  const report = await ui.runCase(bundle(ui.prefix));
  for (const [method] of vectors) expect(report.results[method].state, method).toBe('INSUFFICIENT_EVIDENCE');
  expect(report.results.diligence.data.gaps[0].priority).toBe('BLOCKER');
});
test('MOD-046 financial institution rejects generic industrial DCF', async ({ ui }) => {
  const input = bundle(ui.prefix, { discounted_value: { inputs: dcf } }); input.sector_model = 'financial_institution';
  const report = await ui.runCase(input); expect(report.results.discounted_value.state).toBe('UNSUPPORTED');
});
test('MOD-047 nominal real and currency mismatch never becomes a valuation', async ({ ui }) => {
  const report = await ui.runCase(bundle(ui.prefix, { discounted_value: { inputs: { ...dcf, rate_currency: 'USD' } } }));
  expect(report.results.discounted_value.state).toBe('UNSUPPORTED');
  expect(report.results.discounted_value.data.value).toBeUndefined();
});
test('MOD-048 future evidence excluded from historical replay', async ({ ui }) => {
  const input = bundle(ui.prefix);
  input.as_of = '2024-01-01';
  input.evidence = [{ id: 'future', citation: 'Synthetic future filing', locator: 'page 1', available_by: '2025-01-01', origin_family: 'one', review_state: 'accepted' }];
  const report = await ui.runCase(input);
  expect(report.evidence.data.eligible).toHaveLength(0);
  expect(report.evidence.data.excluded.length).toBeGreaterThan(0);
});
