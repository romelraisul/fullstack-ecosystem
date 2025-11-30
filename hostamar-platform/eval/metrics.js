const fs = require('fs');
const path = require('path');

function autoChecks(text) {
  return {
    hasCTA: /call\s*to\s*action|যোগাযোগ|subscribe|buy|সাইন আপ/i.test(text),
    lengthOK: text.split(/\s+/).length <= 180,
    brandTerms: /cloud|AI|hostamar/i.test(text),
  };
}

function scoreFile(file) {
  const lines = fs.readFileSync(file, 'utf8').trim().split(/\r?\n/);
  const rows = lines.map((l) => JSON.parse(l));
  const checks = rows.map((r) => autoChecks(r.text || ''));
  const agg = {
    count: checks.length,
    hasCTA: checks.filter((c) => c.hasCTA).length,
    lengthOK: checks.filter((c) => c.lengthOK).length,
    brandTerms: checks.filter((c) => c.brandTerms).length,
  };
  return agg;
}

(function main() {
  const dir = path.join(__dirname, 'outputs');
  if (!fs.existsSync(dir)) {
    console.error('No outputs found. Run `npm run eval:run` first.');
    process.exit(1);
  }
  const files = fs.readdirSync(dir).map((f) => path.join(dir, f));
  const report = files.map((f) => ({ file: path.basename(f), agg: scoreFile(f) }));
  fs.writeFileSync(path.join(__dirname, 'report.json'), JSON.stringify(report, null, 2));
  console.log('Wrote eval/report.json');
})();
