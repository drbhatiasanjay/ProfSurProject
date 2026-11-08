const fs = require('node:fs');
const path = require('node:path');
class FunctionalReporter {
  constructor() { this.rows = []; }
  onTestEnd(test, result) {
    const errors = (result.errors || []).map(error => error.message || 'Unknown error');
    this.rows.push({ id: test.title.match(/\b[A-Z]+-\d+\b/)?.[0], title: test.title,
      project: test.parent.project()?.name, status: errors.some(e => e.includes('BLOCKED:')) ? 'BLOCKED' :
        result.status === 'passed' ? 'PASS' : result.status === 'skipped' ? 'NOT_EXECUTED' : 'FAIL',
      durationMs: result.duration, errors, artifacts: result.attachments.map(a => ({ name: a.name, path: a.path })) });
  }
  onEnd(result) {
    const file = process.env.PROFSUR_E2E_SESSION;
    if (!file) return;
    const { runDir } = JSON.parse(fs.readFileSync(file, 'utf8'));
    fs.writeFileSync(path.join(runDir, 'functional-results.json'), JSON.stringify({
      overall: result.status, executedAt: new Date().toISOString(),
      note: 'BLOCKED and NOT_EXECUTED are not passes. Visual/academic validity still requires documented reviewer sign-off.',
      results: this.rows }, null, 2));
  }
}
module.exports = FunctionalReporter;
