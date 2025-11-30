# VM Command Bridge Setup

This adds a lightweight command bridge on the GCP VM to run whitelisted deployment commands. It is resilient to SSH instability and easy to trigger from Azure AI Foundry or VS Code tasks.

## Files

- `scripts/command-bridge/server.js`: Node/Express server with token auth and whitelisted commands.
- `scripts/trigger-deploy.js`: Local client to call the bridge (`deploy`, `health`, etc.).

## VM Setup

1. Copy bridge to VM (via your existing Remote-SSH or upload method):

   ```bash
   mkdir -p ~/command-bridge
   cp ~/hostamar-platform/scripts/command-bridge/server.js ~/command-bridge/server.js
   ```

2. Run under PM2:

   ```bash
   cd ~/command-bridge
   npm init -y
   npm install express
   CB_TOKEN=changeme CB_PORT=8085 pm2 start server.js --name command-bridge
   pm2 save
   ```

3. Test locally on the VM:

   ```bash
   curl http://localhost:8085/healthz
   ```

## Trigger from local (VS Code)

1. Install dependencies:

   ```bash
   cd scripts
   npm init -y
   npm install axios
   ```

2. Run a command:

   ```bash
   setx VM_CMD_URL http://<vm-ip>:8085/run
   setx VM_CMD_TOKEN changeme
   node scripts/trigger-deploy.js deploy
   ```

Replace `<vm-ip>` with your VM public IP.

## Secure the bridge (optional)

- Change `CB_TOKEN` to a strong secret.
- Reverse-proxy behind Nginx and restrict by IP allow-list.
- Only keep necessary commands whitelisted.

## Integrate with Azure AI Foundry

- Create a small Foundry action that runs `node scripts/trigger-deploy.js deploy`.
- Store `VM_CMD_URL` and `VM_CMD_TOKEN` as environment variables or Foundry secrets.
