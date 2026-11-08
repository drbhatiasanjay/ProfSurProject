// Independent small arithmetic/decision examples. Never derive expected values by calling app models.
const semantic = { metric: 'CFO', entity: 'Synthetic', period: 'FY24', duration: 'ANNUAL', basis: 'CONSOLIDATED', definition: 'reported CFO', unit: 'crore', lease: 'reported', net: false };
const dcf = { cash_flows: [100], discount_rate: .1, terminal_next_cash: 0, terminal_growth: .02,
  claim: 'FCFF', rate_claim: 'WACC', currency: 'INR', rate_currency: 'INR', basis: 'nominal', rate_basis: 'nominal' };
const commitment = { id: 'C1', target: 10, direction: 'at_least', deadline: '2024-12-31', metric: 'capacity', period: 'FY24', basis: 'operational' };
const vectors = [
  ['operating_model', { segments: [{ name: 'A', quantity: 10, capacity: 20, net_price: 5, unit_cost: 2, fixed_cost: 3 }], reconciliation_revenue: 50 }, 'COMPUTED', { revenue: 50, reconciliation_difference: 0 }, { segments: [{ name: 'A', quantity: 21, capacity: 20, net_price: 5, unit_cost: 2, fixed_cost: 3 }] }, 'INFEASIBLE'],
  ['cohort_retention', { opening: 100, expansion: 20, contraction: 5, churn: 10, new_customers: 99 }, 'COMPUTED', { nrr: 1.05, existing_cohort_revenue: 105 }, { opening: 100, expansion: 0, contraction: 70, churn: 40 }, 'INVALID_INPUT'],
  ['cash_flow_bridge', { cfo: 100, cash_capex: 20, cash_interest: 10, realized_interest_tax_benefit: 2, cfo_includes_interest: true }, 'COMPUTED', { fcff: 88, cfo_less_capex: 80 }, { cfo: 100, cash_capex: 20, cash_interest: 10, realized_interest_tax_benefit: 11, cfo_includes_interest: true }, 'INVALID_INPUT'],
  ['cash_tax', { taxable_profit: 100, rate: .25, loss_available: 20 }, 'CONDITIONAL_MODEL', { cash_tax: 20, loss_used: 20 }, { taxable_profit: 100, rate: 1.2 }, 'INVALID_INPUT'],
  ['cash_schedule', { opening_cash: 50, minimum_cash: 10, events: [{ date: '2024-01-01', cash_capex: 20 }] }, 'CONDITIONAL_MODEL', { closing_cash: 30 }, { opening_cash: 0, minimum_cash: 10, events: [{ date: '2024-01-01', draw: 100, facility_id: 'not-committed' }] }, 'INFEASIBLE'],
  ['ordinary_raise', { old_shares: 100, required_net: 90, price: 10, proportional_fee: .1 }, 'CONDITIONAL_MODEL', { gross_raise: 100, new_shares: 10, post_shares: 110 }, { old_shares: 100, required_net: 90, price: 0, proportional_fee: .1 }, 'INVALID_INPUT'],
  ['equity_bridge', { operating_ev: 1000, debt: 200, unrestricted_excess_cash: 50 }, 'CONDITIONAL_MODEL', { aggregate_equity_value: 850 }, { operating_ev: 1000, debt: 200, unrestricted_excess_cash: 50, repayment: 201 }, 'INFEASIBLE'],
  ['terminal_cash', { next_nopat: 100, growth: .03, marginal_roic: .15 }, 'CONDITIONAL_MODEL', { next_fcff: 80, growth_reinvestment: 20 }, { next_nopat: 100, growth: .2, marginal_roic: .1 }, 'INFEASIBLE'],
  ['discounted_value', dcf, 'CONDITIONAL_MODEL', { value: 100 / 1.1 }, { ...dcf, terminal_growth: .1 }, 'INVALID_DOMAIN'],
  ['reverse_dcf', { base_fcff: 100, target_ev: 1000, discount_rate: .1, terminal_growth: 0, low: -.2, high: .2 }, 'SOLVED_IN_BRACKET', { root: 0 }, { base_fcff: 100, target_ev: 1e9, discount_rate: .1, terminal_growth: 0, low: -.2, high: .2 }, 'UNBRACKETED'],
  ['reverse_stress', { candidates: [{ id: 'shock', shocks: { revenue: -.1 }, cash_margin: -5, economically_admissible: true }], scales: { revenue: .1 } }, 'ENUMERATED_FAILURE_FRONTIER', { 'failure_paths.0.severity': 1 }, { candidates: [], scales: { revenue: .1 } }, 'INSUFFICIENT_EVIDENCE'],
  ['price_attribution', { eps0: 10, eps1: 12, multiple0: 10, multiple1: 15 }, 'COMPUTED', { price_change: 80, earnings_component: 25, multiple_component: 55, residual: 0 }, { eps0: -10, eps1: 12, multiple0: 10, multiple1: 15 }, 'INVALID_INPUT'],
  ['investor_returns', { flows: [{ date: '2023-01-01', amount: -100 }, { date: '2024-01-01', amount: 110 }], discount_rate: .1 }, 'IRR_SOLVED', { 'roots_found.0': .1, npv: 0 }, { flows: [{ date: '2023-01-01', amount: 100 }], discount_rate: .1 }, 'IRR_UNAVAILABLE'],
  ['private_waterfall', { proceeds: 100, terms_verified: true, classes: [{ id: 'A', shares: 1, conversion_election: 'ordinary' }, { id: 'B', shares: 1, conversion_election: 'ordinary' }] }, 'CONDITIONAL_MODEL', { 'class_proceeds.A': 50, 'class_proceeds.B': 50, conservation_residual: 0 }, { proceeds: 100, classes: [], terms_verified: false }, 'INSUFFICIENT_EVIDENCE'],
  ['diligence_priority', { gaps: [{ attribute: 'Audit note', mandatory: true }] }, 'RULE_BASED', { 'gaps.0.priority': 'BLOCKER' }, { gaps: [{ impact_range: [10, 1], decision_hurdle: 5 }] }, 'INVALID_INPUT'],
  ['information_value', { priors: { good: .5, bad: .5 }, utilities: { invest: { good: 100, bad: -100 }, wait: { good: 0, bad: 0 } } }, 'CONDITIONAL_MODEL', { baseline: 0, evpi: 50 }, { priors: { good: .8, bad: .8 }, utilities: { wait: { good: 0, bad: 0 } } }, 'INVALID_INPUT'],
  ['compare_opportunities', { opportunities: [{ id: 'A', context: { currency: 'INR' }, scenarios: { base: { return: 10 } } }, { id: 'B', context: { currency: 'INR' }, scenarios: { base: { return: 5 } } }], context_keys: ['currency'], orientations: { return: 1 } }, 'PAIRED_SCENARIOS', { 'comparisons.0.state': 'A_DOMINATES' }, { opportunities: [{ id: 'A', context: { currency: 'INR' } }, { id: 'B', context: { currency: 'USD' } }], context_keys: ['currency'], orientations: { return: 1 } }, 'NOT_COMPARABLE'],
  ['evaluate_commitment', { commitment, as_of: '2025-01-01', observation: { metric: 'capacity', period: 'FY24', basis: 'operational', value: 12, available_by: '2024-12-31' } }, 'MET', { variance: 2 }, { commitment, as_of: '2025-01-01' }, 'PENDING_COMPARABLE_OBSERVATION'],
  ['monitor', { observation: { id: 'M1', value: 2 }, threshold: 1, recovery: 1.5 }, 'NORMAL', { value: 2 }, { observation: null, threshold: 1, recovery: 1.5 }, 'UNKNOWN'],
  ['robustness', { variants: [{ value: 80, decision: 'defer' }, { value: 100, decision: 'defer' }] }, 'STABLE_ON_TESTED_VARIANTS', { minimum: 80, maximum: 100 }, { variants: [] }, 'INSUFFICIENT_EVIDENCE'],
  ['compare_facts', { a: { ...semantic, value: 100 }, b: { ...semantic, value: 100 }, absolute_tolerance: 0 }, 'COMPATIBLE', { difference: 0 }, { a: { ...semantic, value: 100 }, b: { ...semantic, entity: 'Other', value: 100 }, absolute_tolerance: 0 }, 'NOT_COMPARABLE'],
  ['method_eligibility', { method: 'descriptive', independent_entities: 1, periods: 1 }, 'ELIGIBLE', {}, { method: 'panel_regression', independent_entities: 1, periods: 1 }, 'INSUFFICIENT_DATA'],
];
function bundle(company, models = {}) {
  return { schema_version: 1, company, as_of: '2026-11-08', currency: 'INR', unit: 'crore',
    background: 'Synthetic financial acceptance case; no real issuer recommendation', evidence: [], propositions: [],
    models, gaps: [{ attribute: 'Original evidence', mandatory: true, next_action: 'Request source and verify inputs' }] };
}
module.exports = { vectors, bundle, dcf };
