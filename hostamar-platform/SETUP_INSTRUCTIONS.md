# Hostamar Platform - Manual Setup Instructions

## Open Windows PowerShell (NOT WSL!)

Press `Win + X` and select "Windows PowerShell" or "Terminal"

## Run These Commands One by One:

```powershell
# Navigate to project
cd c:\Users\romel\OneDrive\Documents\aiauto\hostamar-platform

# Clean previous installation
Remove-Item -Recurse -Force .\node_modules -ErrorAction SilentlyContinue
Remove-Item -Force .\package-lock.json -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .\.next -ErrorAction SilentlyContinue

# Install dependencies (will take 2-3 minutes)
npm install --legacy-peer-deps

# Create environment file
@"
DATABASE_URL="postgresql://user:password@localhost:5432/hostamar"
GITHUB_TOKEN="your-github-token-here"
NEXTAUTH_SECRET="change-this-random-string"
NEXTAUTH_URL="http://localhost:3000"
"@ | Out-File -FilePath .\.env.local -Encoding utf8

# Build production bundle
$env:NODE_ENV = "production"
npm run build

# Start development server
npm run dev
```

## After npm run dev starts:

Open your browser and visit: **http://localhost:3000**

You should see the Hostamar landing page!

## What's Been Created:

✅ **Landing Page** (`app/page.tsx`)
- Hero section
- Features (Cloud Hosting, AI Videos, Free Marketing)
- Pricing (Starter ৳2,000, Business ৳3,500, Enterprise ৳6,000)
- Call-to-action sections

✅ **Video Generation System** (`lib/video-generator.ts`)
- AI script generation
- Voice-over support
- FFmpeg video composition
- MinIO storage integration

✅ **Database Schema** (`prisma/schema.prisma`)
- Customer management
- Business profiles
- Video tracking
- Service provisioning
- Subscription billing

✅ **Complete Package** (`package.json`)
- Next.js 14
- Prisma ORM
- OpenAI integration
- Video processing tools

## Quick Test Checklist:

- [ ] Landing page loads at localhost:3000
- [ ] Navigation works
- [ ] Pricing section displays correctly
- [ ] Responsive design works (try mobile view)

## Next Steps (After Local Testing):

### 1. Update GitHub Token
Edit `.env.local` and replace `your-github-token-here` with your actual GitHub token

### 2. Deploy to GCP VM (34.47.163.149)

Option A - Manual Upload:
```powershell
# Compress the build
Compress-Archive -Path .next,public,package.json,.env.local -DestinationPath hostamar-build.zip

# Upload via SCP (from WSL or Git Bash)
scp hostamar-build.zip user@34.47.163.149:/var/www/hostamar/
```

Option B - Git Push:
```bash
# Initialize git (if not already)
git init
git add .
git commit -m "Initial hostamar platform"

# Push to your repo and pull from server
```

### 3. Server Setup Commands (SSH to GCP VM):

```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install PM2
sudo npm i -g pm2

# Setup app directory
sudo mkdir -p /var/www/hostamar
cd /var/www/hostamar

# Extract your zip or git pull
# Then:
npm install --production --legacy-peer-deps
npm run build

# Start with PM2
pm2 start npm --name "hostamar" -- start
pm2 save
pm2 startup
```

### 4. Nginx Configuration:

```bash
sudo tee /etc/nginx/sites-available/hostamar <<'EOF'
server {
    listen 80;
    server_name hostamar.com www.hostamar.com;
    
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/hostamar /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. SSL Certificate (Let's Encrypt):

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d hostamar.com -d www.hostamar.com --email admin@hostamar.com --agree-tos --redirect
```

### 6. DNS Configuration (Cloudflare):

Add these records:
- A record: `hostamar.com` → `34.47.163.149`
- A record: `www.hostamar.com` → `34.47.163.149`
- Enable proxy (orange cloud) for DDoS protection

## Timeline:

- **Local setup & test**: 10-15 minutes ✅
- **Deploy to GCP**: 20-30 minutes
- **DNS propagation**: 5-30 minutes
- **SSL setup**: 5 minutes
- **Total**: ~1 hour to live site! 🚀

## Support:

If you encounter issues:
1. Check `npm install` completed without errors
2. Verify `.env.local` exists
3. Check port 3000 is not in use
4. Review build logs: `npm run build > build.log 2>&1`

## Ready to Launch! 

Your platform is ready for customers. Just:
1. Test locally ✅
2. Deploy to server
3. Point DNS
4. Start onboarding customers! 💰
