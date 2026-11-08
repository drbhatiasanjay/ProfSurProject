const { test, expect, audit } = require('../support/fixtures.cjs');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const plan = process.env.PROFSUR_E2E_GOLD_PLAN ? JSON.parse(fs.readFileSync(process.env.PROFSUR_E2E_GOLD_PLAN, 'utf8')) : null;
if (!plan || !plan.documents?.length) {
  test('CORPUS-001 @corpus independently verified issuer corpus plan is required', async () => {
    throw new Error('BLOCKED: Supply --gold-plan using the documented template after source-page review. No issuer expected values are invented.');
  });
} else {
  const issuers = [...new Set(plan.documents.map(d => d.issuer))];
  for (const [issuerIndex, issuer] of issuers.entries()) test(`CORPUS-${900 + issuerIndex} @corpus ${issuer}: shared dossier, review, analysis, delete and reload`, async ({ ui }) => {
    test.setTimeout(3600000);
    const documents = plan.documents.filter(d => d.issuer === issuer);
    if (plan.approved !== true || !plan.reviewedBy || documents.some(d => !d.entityVerified || !d.expected?.length))
      throw new Error('BLOCKED: Approve independently annotated document/entity expectations first.');
    await ui.open(); await ui.createCompany('', issuer);
    for (const [i, doc] of documents.entries()) {
      const file = path.resolve(plan.collectionRoot, doc.path);
      expect(file.startsWith(path.resolve(plan.collectionRoot) + path.sep)).toBe(true);
      expect(crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')).toBe(doc.sha256);
      await ui.retain(file, `${ui.prefix} doc ${i}`, { type: doc.filingType || 'Other evidence', version: doc.version });
      await ui.processDocument(doc.pages);
    }
    const loaded = audit(['--name', ui.company, '--owner', ui.account.username]);
    expect(loaded.documents).toHaveLength(documents.length);
    // Review selected source-located fields using the same real form users must use.
    const reviewed = new Set();
    for (const [i, doc] of documents.entries()) for (const gold of doc.expected.filter(f => f.reviewId)) {
      if (reviewed.has(gold.reviewId)) continue; // conflicts must remain independent candidates, not forced precedence
      reviewed.add(gold.reviewId);
      await ui.tab('Sources & review'); await ui.select('Retained source', new RegExp(`${ui.prefix} doc ${i}`));
      await ui.page.getByLabel('PDF page to inspect (1-based)', { exact: true }).fill(String(gold.page));
      const existing = loaded.facts.some(f => f.id === gold.reviewId);
      await ui.review(gold.value, { id: gold.reviewId, edit: existing, quote: gold.quote,
        context: { Entity: gold.entity, Period: gold.period, Basis: gold.basis, Unit: gold.unit,
          Currency: gold.currency || 'INR', Framework: gold.framework || 'IND_AS', Duration: gold.duration || 'ANNUAL', Definition: gold.definition || gold.attributeId },
        locator: gold.locator || `PDF page ${gold.page}`, reason: `Independent gold page checked by ${plan.reviewedBy}` });
    }
    if (reviewed.size < 2) throw new Error('BLOCKED: At least two source-backed reviewId fields are required for downstream corpus analysis.');
    const frozen = await ui.freeze();
    for (const id of reviewed) expect(frozen.assessment.accepted_fact_revisions[id]).toBeTruthy();
    for (const question of frozen.assessment.questions) {
      expect(question.interpretation.length).toBeGreaterThan(10);
      expect(question.next_action.length).toBeGreaterThan(10);
      if (question.state === 'COMPUTED') expect(question.fact_ids.length).toBeGreaterThan(0);
    }
    await ui.download('Download evidence PPTX', 'corpus-evidence.pptx');
    const beforeDelete = audit(['--name', ui.company, '--owner', ui.account.username]);
    await ui.deleteCompany();
    const deleted = audit(['--name', ui.company, '--owner', ui.account.username, ...beforeDelete.companies.flatMap(id => ['--company-id', id])]);
    expect(deleted.documents).toHaveLength(0); expect(deleted.facts).toHaveLength(0);
    await ui.restart(); await ui.open(); await ui.createCompany('', issuer);
    const first = documents[0]; await ui.retain(path.resolve(plan.collectionRoot, first.path), `${ui.prefix} fresh reload`, { type: first.filingType || 'Other evidence', version: first.version });
    const fresh = await ui.freeze();
    for (const id of reviewed) expect(fresh.assessment.accepted_fact_revisions[id]).toBeUndefined();
    await ui.deleteCompany();
  });
  for (const [index, doc] of plan.documents.entries()) test(`CORPUS-${String(index + 1).padStart(3, '0')} @corpus ${doc.issuer}: ${doc.title}`, async ({ ui }) => {
    test.setTimeout(900000);
    if (plan.approved !== true || !plan.reviewedBy || !doc.entityVerified || !doc.expected?.length)
      throw new Error('BLOCKED: Independent reviewer, entity/perimeter and source-backed expected fields are required for each document.');
    const file = path.resolve(plan.collectionRoot, doc.path);
    expect(file.startsWith(path.resolve(plan.collectionRoot) + path.sep), 'Document path outside collection').toBe(true);
    const bytes = fs.readFileSync(file);
    expect(crypto.createHash('sha256').update(bytes).digest('hex')).toBe(doc.sha256);
    await ui.open(); await ui.createCompany('', doc.issuer);
    await ui.retain(file, `${ui.prefix} ${doc.title}`, { type: doc.filingType || 'Other evidence', version: doc.version });
    await ui.processDocument(doc.pages);
    // Candidate generation must happen through the user workflow; no DB fixture insertion allowed.
    const state = audit(['--name', ui.company, '--owner', ui.account.username]);
    for (const expected of doc.expected) {
      expect(expected.page, 'Gold page binding').toBeGreaterThan(0);
      expect(expected.quote?.length, 'Gold source quote').toBeGreaterThan(5);
      const candidates = state.facts.filter(f => f.id === expected.attributeId || f.metric_id === expected.attributeId);
      expect(candidates.length, `No automatic ${expected.attributeId} candidate: pipeline integration incomplete`).toBeGreaterThan(0);
      const candidate = candidates.at(-1);
      expect(candidate.context?.entity).toBe(expected.entity);
      expect(candidate.context?.period).toBe(expected.period);
      expect(candidate.context?.basis).toBe(expected.basis);
      expect(candidate.context?.unit).toBe(expected.unit);
      expect(candidate.source?.page).toBe(expected.page);
      expect(candidate.review).not.toBe('ACCEPTED');
      const actual = candidate.extraction_raw_value ?? candidate.value ?? candidate.raw_value;
      if (typeof expected.value === 'number') expect(Math.abs(Number(actual) - expected.value)).toBeLessThanOrEqual(expected.absoluteTolerance ?? 0);
      else expect(actual).toEqual(expected.value);
    }
    await ui.tab('Attribute inventory'); await expect(ui.page.getByTestId('stDataFrame').first()).toBeVisible();
    const before = audit(['--name', ui.company, '--owner', ui.account.username]);
    await ui.deleteCompany();
    const after = audit(['--name', ui.company, '--owner', ui.account.username, ...before.companies.flatMap(id => ['--company-id', id])]);
    expect(after.companies).toHaveLength(0); expect(after.documents).toHaveLength(0); expect(after.facts).toHaveLength(0);
    await ui.createCompany('', doc.issuer); await ui.retain(file, `${ui.prefix} ${doc.title}`, { type: doc.filingType || 'Other evidence', version: doc.version });
    expect(audit(['--name', ui.company, '--owner', ui.account.username]).facts.some(f => f.review === 'ACCEPTED')).toBe(false);
    await ui.deleteCompany();
  });
}
