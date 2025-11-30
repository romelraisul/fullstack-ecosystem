# Microsoft Foundry Research Plan — Node.js Simplification & AI Video Scripts

## Goals
- Measure the impact of dependency minimization on install reliability and performance.
- Compare model quality/cost for generating branded short-video scripts.
- Establish repeatable evaluation in Microsoft Foundry with tracing and experiment tracking.

## Hypotheses
- H1: Minimal dependencies reduce install failures and dev startup time (>50%).
- H2: Foundry-hosted models produce higher-quality, on-brand scripts with lower latency than baseline.
- H3: Observability (OpenTelemetry) improves debugging time for prompt/tooling errors (>30% faster).

## Metrics (max 3)
- Install Reliability: npm install success rate; time to "ready" (s).
- Script Quality: Relevance, Brand Consistency (Likert 1-5, human-rated), and short automatic checks.
- Latency/Cost: First-token latency (s); output tokens/sec; est. cost per 1K tokens.

## Dataset & Tasks
- Inputs: Customer profile (name, industry, brand color), product highlights, CTA target.
- Tasks: 45–60s script for Facebook/Instagram Reels; variants: intro, promo, testimonial.
- Size: 30 customers × 3 topics = 90 prompts; seed in `data/queries.jsonl`.

## Model Candidates (Microsoft Foundry)
- gpt-5 | High-quality reasoning; robust branding adherence.
- gpt-4.1-mini | Strong balance of quality & speed.
- Phi-4 | Low latency, low cost; baseline.

## Experiment Design
1. Create Foundry Project & Deploy Models
   - Open Microsoft Foundry portal; create Project & Hub.
   - From Model Catalog, deploy `gpt-5`, `gpt-4.1-mini`, `phi-4`.
2. Prepare Evaluation Assets in Repo
   - `data/queries.jsonl`: structured prompts
   - `eval/config.json`: which models + metrics to run
   - `eval/run.js`: runner using Azure AI Projects SDK
   - `eval/metrics.js`: metric computation
3. Run A/B/C Trials
   - 90 prompts × 3 models; save outputs to `eval/outputs/<model>.jsonl`.
4. Score & Compare
   - Human quick ratings + automatic checks (length, CTA presence, brand term usage).
   - Summaries + charts in `eval/report.md`.

## Tracing (Azure AI Projects SDK)
- Use OpenTelemetry with OTLP exporter to `http://localhost:4318/v1/traces`.
- Instrument Azure SDK; if using OpenAI SDK path, add traceloop OpenAI instrumentation.
- Key spans: prompt build, completion call, token count, retry/backoff.

## Evaluation Flow (Planner)
- Metrics clarified above; queries: `data/queries.jsonl`; responses: `eval/outputs/*.jsonl`.
- After first run, compute metrics and request user approval to lock evaluation spec.

## Foundry Steps Checklist
- [ ] Create Project & Hub
- [ ] Deploy `gpt-5`, `gpt-4.1-mini`, `phi-4`
- [ ] Set project endpoint & credentials in `.env.local`
- [ ] Seed `data/queries.jsonl`
- [ ] Run `node eval/run.js`
- [ ] Review `eval/report.md`

## Minimal Code Stubs (Node.js)

`eval/run.js`
```javascript
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { AIProjectClient } = require('@azure/ai-projects');
const { DefaultAzureCredential } = require('@azure/identity');

const ENDPOINT = process.env.AZURE_AI_FOUNDRY_PROJECT_ENDPOINT;
const MODELS = (process.env.EVAL_MODELS || 'gpt-5,gpt-4.1-mini,phi-4').split(',');
const QUERIES = path.join(__dirname, '../data/queries.jsonl');

async function loadQueries() {
  return fs.readFileSync(QUERIES, 'utf8')
    .trim()
    .split(/\r?\n/)
    .map((l) => JSON.parse(l));
}

async function runModel(project, model, queries) {
  const outPath = path.join(__dirname, `./outputs/${model}.jsonl`);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  const client = await project.inference.chatCompletions();
  for (const q of queries) {
    const body = {
      model,
      messages: [
        { role: 'system', content: 'You are a marketing script writer. Keep to 60s.' },
        { role: 'user', content: q.prompt },
      ],
    };
    const res = await client.post({ body });
    const text = res.body?.choices?.[0]?.message?.content || '';
    fs.appendFileSync(outPath, JSON.stringify({ id: q.id, model, text }) + '\n');
  }
}

(async () => {
  const project = new AIProjectClient(ENDPOINT, new DefaultAzureCredential());
  const queries = await loadQueries();
  for (const m of MODELS) {
    console.log('Running', m);
    await runModel(project, m, queries);
  }
  console.log('Done. See eval/outputs/*.jsonl');
})();
```

`eval/metrics.js`
```javascript
const fs = require('fs');
const path = require('path');

function autoChecks(text) {
  return {
    hasCTA: /call\s*to\s*action|যোগাযোগ|subscribe|buy/i.test(text),
    lengthOK: text.split(/\s+/).length <= 180, // ~60s spoken
    brandTerms: /cloud|AI|hostamar/i.test(text),
  };
}

function scoreFile(file) {
  const lines = fs.readFileSync(file, 'utf8').trim().split(/\r?\n/);
  const rows = lines.map((l) => JSON.parse(l));
  const checks = rows.map((r) => autoChecks(r.text));
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
  const files = fs.readdirSync(dir).map((f) => path.join(dir, f));
  const report = files.map((f) => ({ file: path.basename(f), agg: scoreFile(f) }));
  fs.writeFileSync(path.join(__dirname, 'report.json'), JSON.stringify(report, null, 2));
  console.log('Wrote eval/report.json');
})();
```

`data/queries.jsonl`
```json
{"id": 1, "prompt": "Brand: Hostamar. Industry: Retail. Topic: Holiday promo. CTA: সাইন আপ করুন।"}
{"id": 2, "prompt": "Brand: Hostamar. Industry: Clinic. Topic: New service launch. CTA: এখনই যোগাযোগ করুন।"}
{"id": 3, "prompt": "Brand: Hostamar. Industry: Restaurant. Topic: Weekend offer. CTA: বুক করুন।"}
```

## Environment
Add to `.env.local` (and PowerShell env if running locally):
```
AZURE_AI_FOUNDRY_PROJECT_ENDPOINT="https://<your-project-endpoint>"
EVAL_MODELS="gpt-5,gpt-4.1-mini,phi-4"
```

## Next Steps
- Run local dev: `npm run dev` and validate landing page.
- Create Foundry project; deploy models; set endpoint.
- Execute `node eval/run.js` then `node eval/metrics.js`; review `eval/report.json`.
- Iterate prompts, add human ratings into `eval/report.md` and pick best model.