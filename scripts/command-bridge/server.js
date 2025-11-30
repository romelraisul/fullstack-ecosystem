const express = require('express');
const { exec } = require('child_process');

const PORT = process.env.CB_PORT || 8085;
const AUTH_TOKEN = process.env.CB_TOKEN || 'changeme';

const app = express();
app.use(express.json());

// Whitelisted commands only
const ALLOWED = {
  deploy: 'bash ~/scripts/deploy-all-from-vm.sh hostamar.com',
  health: 'curl -s http://localhost:3001/api/health',
  pm2_status: 'pm2 status',
  nginx_test: 'sudo nginx -t',
};

app.post('/run', (req, res) => {
  try {
    const token = req.headers['x-auth'];
    if (!token || token !== AUTH_TOKEN) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
    const cmdKey = req.body && req.body.cmd;
    const cmd = ALLOWED[cmdKey];
    if (!cmd) {
      return res.status(400).json({ error: 'Invalid command' });
    }
    exec(cmd, { timeout: 10 * 60 * 1000 }, (err, stdout, stderr) => {
      if (err) {
        return res.status(500).json({ error: err.message, stderr });
      }
      res.json({ ok: true, stdout });
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/healthz', (_req, res) => res.json({ ok: true }));

app.listen(PORT, () => console.log(`Command bridge listening on ${PORT}`));
