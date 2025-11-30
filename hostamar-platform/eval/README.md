# Hostamar Foundry Evaluation

## Setup
1. Add to environment:
```
AZURE_AI_FOUNDRY_PROJECT_ENDPOINT="https://<your-project-endpoint>"
EVAL_MODELS="gpt-5,gpt-4.1-mini,phi-4"
```
2. Install deps:
```
cd eval
npm install
```

## Run
```
npm run eval:run
npm run eval:metrics
```
Outputs are in `eval/outputs/*.jsonl` and summary in `eval/report.json`.
