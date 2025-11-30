require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { AIProjectClient } = require('@azure/ai-projects');
const { DefaultAzureCredential } = require('@azure/identity');

const ENDPOINT = process.env.AZURE_AI_FOUNDRY_PROJECT_ENDPOINT;
const MODELS = (process.env.EVAL_MODELS || 'gpt-5,gpt-4.1-mini,phi-4').split(',');
const QUERIES = path.join(__dirname, '../data/queries.jsonl');
const MOCK_MODE = process.env.MOCK_MODE === 'true';

function loadQueries() {
  return fs.readFileSync(QUERIES, 'utf8')
    .trim()
    .split(/\r?\n/)
    .map((l) => JSON.parse(l));
}

async function getInferenceClient(project) {
  // Try REST-style chatCompletions first
  if (project.inference && typeof project.inference.chatCompletions === 'function') {
    const client = await project.inference.chatCompletions();
    return { mode: 'rest', client };
  }
  // Fallback to OpenAI-compatible client
  if (project.inference && typeof project.inference.azureOpenAI === 'function') {
    const client = await project.inference.azureOpenAI();
    return { mode: 'openai', client };
  }
  return { mode: 'direct-rest', client: null };
}

async function runModel(project, model, queries) {
  const outPath = path.join(__dirname, `./outputs/${model}.jsonl`);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });

  if (MOCK_MODE) {
    for (const q of queries) {
      const text = generateMockResponse(q.prompt, model);
      fs.appendFileSync(outPath, JSON.stringify({ id: q.id, model, text }) + '\n');
    }
    return;
  }

  const { mode, client } = await getInferenceClient(project);

  for (const q of queries) {
    if (mode === 'rest') {
      const body = {
        model,
        messages: [
          { role: 'system', content: 'You are a marketing script writer. Keep to 60s.' },
          { role: 'user', content: q.prompt },
        ],
      };
      const res = await client.post({ body });
      const text = (res.body && res.body.choices && res.body.choices[0] && res.body.choices[0].message && res.body.choices[0].message.content) || '';
      fs.appendFileSync(outPath, JSON.stringify({ id: q.id, model, text }) + '\n');
    } else if (mode === 'openai') {
      const res = await client.chat.completions.create({
        model,
        messages: [
          { role: 'system', content: 'You are a marketing script writer. Keep to 60s.' },
          { role: 'user', content: q.prompt },
        ],
      });
      const text = (res.choices && res.choices[0] && res.choices[0].message && res.choices[0].message.content) || '';
      fs.appendFileSync(outPath, JSON.stringify({ id: q.id, model, text }) + '\n');
    } else if (mode === 'direct-rest') {
      const text = await callChatCompletionsDirect(ENDPOINT, model, [
        { role: 'system', content: 'You are a marketing script writer. Keep to 60s.' },
        { role: 'user', content: q.prompt },
      ]);
      fs.appendFileSync(outPath, JSON.stringify({ id: q.id, model, text }) + '\n');
    }
  }
}

async function callChatCompletionsDirect(endpoint, model, messages) {
  const credential = new DefaultAzureCredential();

  const urlCandidates = [
    `${endpoint.replace(/\/$/, '')}/inference/chatCompletions?api-version=2024-10-01-preview`,
    `${endpoint.replace(/\/$/, '')}/inference/chat/completions?api-version=2024-10-01-preview`,
    `${endpoint.replace(/\/$/, '')}/inference/chatCompletions?api-version=2024-05-01-preview`,
    `${endpoint.replace(/\/$/, '')}/inference/chat/completions?api-version=2024-05-01-preview`,
  ];

  const scopeCandidates = [
    'https://ai.azure.com/.default',
    'https://ml.azure.com/.default',
    'https://cognitiveservices.azure.com/.default',
  ];

  const body = {
    model,
    messages,
  };

  let lastErr;
  for (const scope of scopeCandidates) {
    try {
      const token = await credential.getToken(scope);
      if (!token || !token.token) continue;
      for (const url of urlCandidates) {
        try {
          const res = await fetch(url, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token.token}`,
            },
            body: JSON.stringify(body),
          });
          if (res.ok) {
            const data = await res.json();
            const text = (data && data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content) || '';
            return text;
          }
          lastErr = new Error(`HTTP ${res.status} ${res.statusText} for ${url} (scope ${scope})`);
        } catch (e) {
          lastErr = e;
        }
      }
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr || new Error('All REST inference attempts failed');
}

function generateMockResponse(prompt, model) {
  const templates = [
    `আপনার ব্যবসার জন্য ${model} দিয়ে তৈরি ভিডিও স্ক্রিপ্ট: " ${prompt.substring(0, 50)}... " - এখনই যোগাযোগ করুন এবং আপনার ব্র্যান্ডকে এগিয়ে নিন।`,
    `Cloud-powered AI automation for your business. ${prompt.substring(0, 40)}. Contact us today!`,
    `Hostamar platform এ স্বাগতম। ${prompt.substring(0, 30)}। সাইন আপ করুন।`,
  ];
  return templates[Math.floor(Math.random() * templates.length)];
}

(async () => {
  if (!MOCK_MODE && !ENDPOINT) {
    console.error('Missing AZURE_AI_FOUNDRY_PROJECT_ENDPOINT in environment. Set MOCK_MODE=true for offline testing.');
    process.exit(1);
  }
  const project = MOCK_MODE ? null : new AIProjectClient(ENDPOINT, new DefaultAzureCredential());
  const queries = loadQueries();
  for (const m of MODELS) {
    console.log('Running', m);
    await runModel(project, m, queries);
  }
  console.log('Done. See eval/outputs/*.jsonl');
})();
