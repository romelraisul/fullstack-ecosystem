# Hostamar Platform

AI-powered video marketing automation platform for small businesses.

## 🚀 Quick Start

### Local Development
```bash
npm install
npx prisma db push
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Production Deployment (GCP Mumbai)
```bash
cd deploy
bash gcp-mumbai-deploy.sh
```

See **[deploy/README.md](deploy/README.md)** for complete deployment guide.

---

## 📦 Project Structure

```
hostamar-platform/
├── app/                    # Next.js App Router
│   ├── api/               # API routes
│   │   ├── auth/         # NextAuth authentication
│   │   └── health/       # Health check endpoint
│   ├── auth/             # Signup/Login pages
│   └── page.tsx          # Landing page
├── prisma/
│   └── schema.prisma     # Database schema
├── lib/
│   └── prisma.ts         # Prisma client
├── eval/                 # Microsoft Foundry evaluation
│   ├── run.js           # Evaluation runner
│   └── metrics.js       # Quality metrics
├── deploy/               # 🆕 GCP Deployment
│   ├── README.md        # Complete deployment guide
│   ├── gcp-mumbai-deploy.sh  # Automated deployment
│   ├── deploy.py        # Python deployment script
│   ├── nginx-setup.sh   # Nginx + SSL setup
│   ├── CHEATSHEET.md    # Quick commands
│   └── DEPLOYMENT_GUIDE.md   # Step-by-step with AI prompts
└── .github/workflows/   # CI/CD pipelines
```

---

## 🛠️ Tech Stack

- **Framework:** Next.js 14.2 (App Router)
- **Authentication:** NextAuth.js with Credentials provider
- **Database:** Prisma ORM with SQLite (dev) / PostgreSQL (prod)
- **Styling:** Tailwind CSS
- **AI Integration:** Azure AI Foundry (Microsoft Foundry)
- **Deployment:** Google Cloud Platform (Mumbai region)
- **Process Manager:** PM2
- **Web Server:** Nginx with Let's Encrypt SSL

---

## 🔐 Authentication

- **Signup:** `/auth/signup`
- **Login:** `/auth/signin`
- **Dashboard:** `/dashboard` (protected)

### Database Schema
- **Customer** - User accounts with hashed passwords (bcrypt)
- **Business** - Business profiles (one-to-one with Customer)
- **Video** - AI-generated video scripts
- **Subscription** - Payment plans (৳2000, ৳3500, ৳6000)

---

## 🌐 Deployment

### GCP Mumbai VM (asia-south1-a)

**Method 1: Automated Script**
```bash
cd deploy
bash gcp-mumbai-deploy.sh
```

**Method 2: AI Agent (VS Code Copilot)**
```
প্রম্পট: Deploy my hostamar-platform to GCP Mumbai VM. 
Configure SSH, upload code via rsync, setup environment, and start with PM2.
```

**Full Documentation:** [deploy/DEPLOYMENT_GUIDE.md](deploy/DEPLOYMENT_GUIDE.md)

### Architecture
```
VS Code (Local) 
  → gcloud SSH 
  → rsync upload 
  → VM (Mumbai)
    → Node.js + PM2 
    → Nginx (Reverse Proxy) 
    → Let's Encrypt SSL 
    → Cloudflare DNS 
    → https://hostamar.com
```

---

## 🔍 Monitoring

### Health Check
```bash
curl http://localhost:3000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": { "connected": true, "customers": 0 },
  "environment": { "nodeEnv": "production" }
}
```

### PM2 Status
```bash
pm2 status
pm2 logs hostamar
pm2 monit
```

---

## 🤖 AI Evaluation System

Microsoft Foundry integration for AI video script quality evaluation.

**Features:**
- Mock mode for offline testing
- Automatic quality metrics (CTA presence, length check, brand terms)
- GitHub Actions CI/CD pipeline
- Multi-model comparison

**Run Evaluation:**
```bash
cd eval
npm install
npm run eval:run    # Generate outputs
npm run eval:metrics # Compute metrics
```

**Docs:** [eval/SETUP_COMPLETE.md](eval/SETUP_COMPLETE.md)

---

## 📋 Environment Variables

### Development (`.env.local`)
```env
DATABASE_URL="file:./dev.db"
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET="your-secret-here"
GITHUB_TOKEN="ghp_..."
AZURE_AI_FOUNDRY_PROJECT_ENDPOINT="https://..."
```

### Production (`.env` on VM)
```env
DATABASE_URL="file:./prod.db"
NEXTAUTH_URL="https://hostamar.com"
NODE_ENV="production"
PORT=3000
```

---

## 🚦 Current Status

### ✅ Completed
- [x] Next.js app with landing page
- [x] Authentication (NextAuth + Prisma)
- [x] Database schema (Customer, Business, Video, Subscription)
- [x] Microsoft Foundry evaluation pipeline
- [x] GCP Mumbai deployment automation
- [x] Nginx + SSL setup scripts
- [x] VS Code Remote SSH configuration
- [x] Health check API endpoint

### 🔄 In Progress
- [ ] Customer dashboard
- [ ] Video script generation API
- [ ] Payment integration (Stripe)
- [ ] Admin panel

### 📅 Planned
- [ ] Video creation workflow
- [ ] Email notifications
- [ ] Automation & scheduling
- [ ] Landing page polish

**Full Roadmap:** See todo list in workspace

---

## 🛠️ Common Commands

### Development
```bash
npm run dev          # Start dev server
npm run build        # Production build
npm run start        # Start production server
```

### Database
```bash
npx prisma generate  # Generate Prisma Client
npx prisma db push   # Apply schema changes
npx prisma studio    # Open database GUI
```

### Deployment
```bash
# Deploy to GCP
bash deploy/gcp-mumbai-deploy.sh

# Update existing deployment
rsync -avzP --exclude 'node_modules' ./ REMOTE_HOST:~/hostamar-platform/
ssh REMOTE_HOST "cd ~/hostamar-platform && npm run build && pm2 restart hostamar"

# View remote logs
ssh REMOTE_HOST "pm2 logs hostamar"
```

**All Commands:** [deploy/CHEATSHEET.md](deploy/CHEATSHEET.md)

---

## 📚 Documentation

| File | Description |
|------|-------------|
| [deploy/README.md](deploy/README.md) | Complete deployment overview |
| [deploy/DEPLOYMENT_GUIDE.md](deploy/DEPLOYMENT_GUIDE.md) | Step-by-step deployment with AI prompts |
| [deploy/CHEATSHEET.md](deploy/CHEATSHEET.md) | Quick command reference |
| [eval/SETUP_COMPLETE.md](eval/SETUP_COMPLETE.md) | AI evaluation setup guide |
| [RESEARCH_PLAN_AZURE_FOUNDRY.md](RESEARCH_PLAN_AZURE_FOUNDRY.md) | Microsoft Foundry research plan |

---

## 🔧 Troubleshooting

### Local Development
**Port 3000 in use:**
```bash
lsof -ti:3000 | xargs kill -9  # macOS/Linux
npx kill-port 3000             # Windows
```

**Database issues:**
```bash
rm -f dev.db
npx prisma db push
```

### Production (GCP)
**SSH connection failed:**
```bash
gcloud compute config-ssh
```

**App not accessible:**
```bash
ssh REMOTE_HOST "pm2 logs hostamar --err"
```

**Full Troubleshooting:** [deploy/DEPLOYMENT_GUIDE.md](deploy/DEPLOYMENT_GUIDE.md#troubleshooting)

---

## 🤝 Contributing

This is a private business project. For internal team collaboration only.

---

## 📄 License

Proprietary - All rights reserved.

---

## 🎯 Next Steps

1. **Run deployment:** `bash deploy/gcp-mumbai-deploy.sh`
2. **Setup DNS:** Point `hostamar.com` to VM IP
3. **Test production:** `curl https://hostamar.com/api/health`
4. **Start building features:** Customer dashboard, video generation, payments

---

*Built with ❤️ using VS Code AI Agent*  
*Deployed on GCP Mumbai (asia-south1-a)*
