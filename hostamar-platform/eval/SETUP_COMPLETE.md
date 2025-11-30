# Eval Setup Complete ✅

## What's Ready

### Offline Testing (MOCK_MODE)
- `eval/.env` এ `MOCK_MODE="true"` সেট করা আছে
- এখন Foundry access ছাড়াই locally run করা যাবে
- Synthetic responses তৈরি হবে testing এর জন্য

### Run Now
```powershell
cd "c:\Users\romel\OneDrive\Documents\aiauto\hostamar-platform\eval"
npm install
npm run eval:run
npm run eval:metrics
```

### After Foundry Access
যখন Foundry portal access পাবেন:
1. `eval/.env` এ `MOCK_MODE="false"` করুন
2. Foundry থেকে exact model deployment name verify করুন
3. Re-run: `npm run eval:run`

### Files Created
- `eval/run.js` → Mock mode + REST fallback সহ
- `eval/metrics.js` → Automatic checks (CTA, length, brand terms)
- `eval/.env` → Endpoint + mock flag
- `data/queries.jsonl` → 3 sample prompts (retail, clinic, restaurant)
- `.github/workflows/foundry-eval.yml` → GitHub Actions pipeline
- `foundry/pipeline.yaml` → Foundry pipeline template

### Next Steps
1. **Run eval locally** (mock mode):
   ```powershell
   cd eval
   npm run eval:run
   npm run eval:metrics
   ```
2. **Review outputs**:
   - `eval/outputs/gpt-4o.jsonl`
   - `eval/report.json`
3. **Add more queries** to `data/queries.jsonl`
4. **When Foundry ready**, set `MOCK_MODE="false"` and re-run

## Mock Mode Details
- Generates বাংলা + English mixed responses
- Includes brand terms (Cloud, AI, Hostamar)
- CTA present (\u09af\u09cb\u0997\u09be\u09af\u09cb\u0997, contact, \u09b8\u09be\u0987\u09a8 \u0986\u09aa)
- Length appropriate (~60s script length)

All set! Run `npm run eval:run` now. 🚀
