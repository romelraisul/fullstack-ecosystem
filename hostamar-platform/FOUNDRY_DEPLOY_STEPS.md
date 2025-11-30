# Deploy Models in Microsoft Foundry

## Prereqs
- Azure subscription + access to Microsoft Foundry (Azure AI Foundry rebranded)
- Contributor role on the Foundry Project/Hub

## Steps
1. Open Microsoft Foundry Portal
   - Go to https://ai.azure.com (Microsoft Foundry) and sign in.
2. Create Project & Hub
   - New Project → select subscription, resource group, region
   - Create/attach a Hub to the project
3. Deploy Models from Catalog
   - Open Model Catalog
   - Search and deploy:
     - `gpt-5`
     - `gpt-4.1-mini`
     - `phi-4`
   - Choose the same region as your project
4. Get Project Endpoint
   - In Project → Overview → copy `Project endpoint`
   - Set in `.env.local`:
     ```
     AZURE_AI_FOUNDRY_PROJECT_ENDPOINT="https://<your-project-endpoint>"
     EVAL_MODELS="gpt-5,gpt-4.1-mini,phi-4"
     ```
5. Run Evaluation Locally
   - Install eval deps:
     ```powershell
     cd "c:\Users\romel\OneDrive\Documents\aiauto\hostamar-platform\eval"
     npm install
     ```
   - Execute:
     ```powershell
     $env:AZURE_AI_FOUNDRY_PROJECT_ENDPOINT="https://<your-project-endpoint>"; $env:EVAL_MODELS="gpt-5,gpt-4.1-mini,phi-4"; npm run eval:run
     npm run eval:metrics
     ```
   - Review outputs in `eval/outputs/*.jsonl` and `eval/report.json`

## Notes
- If using service principal, ensure your environment is configured for `DefaultAzureCredential` (Azure CLI login or environment variables).
- For tracing, add OpenTelemetry and instrument Azure SDK as per `RESEARCH_PLAN_AZURE_FOUNDRY.md`.
