const axios = require('axios');

const url = process.env.VM_CMD_URL || 'http://<vm-ip>:8085/run';
const token = process.env.VM_CMD_TOKEN || 'changeme';
const cmd = process.argv[2] || 'deploy';

(async () => {
  const r = await axios.post(url, { cmd }, { headers: { 'X-Auth': token } });
  console.log(r.data);
})().catch(e => {
  const data = e.response?.data || e.message;
  console.error(data);
  process.exit(1);
});
