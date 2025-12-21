# 🚀 Hostamar Quick Start Guide

**Project Status**: 70% MVP Complete | Ready for Demo/Testing  
**Live URL**: http://34.47.163.149:3001

---

## ⚡ 5-Minute Setup

### For Linux/Mac:
```bash
cd hostamar-platform
chmod +x setup.sh
./setup.sh
npm run dev
```

### For Windows (PowerShell as Admin):
```powershell
cd hostamar-platform
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser
.\setup-windows.ps1
npm run dev
```

Then open http://localhost:3000 in your browser.

---

## 🔑 Essential Environment Variables

Create `.env.local` in the project root:

```env
# MUST HAVE
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_32_char_secret_here  # Generate: openssl rand -base64 32
DATABASE_URL=file:./prisma/dev.db

# STRIPE (for payments)
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLIC_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# EMAIL (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your_app_password
```

**How to get these values:**
1. **Stripe Keys**: https://dashboard.stripe.com/apikeys
2. **Gmail App Password**: https://myaccount.google.com/apppasswords (after enabling 2FA)
3. **NEXTAUTH_SECRET**: Run `openssl rand -base64 32`

---

## 🧪 Testing the App

### Test Account (for login):
```
Email: test@example.com
Password: password123
```

Or create a new account by clicking "Sign Up"

### Test Payment:
1. Go to `/pricing`
2. Click "Start Now" on any plan
3. Use Stripe test card: `4242 4242 4242 4242`
4. Expiry: Any future date (e.g., 12/25)
5. CVC: Any 3 digits (e.g., 123)

### Test Video Generation:
1. After signup, go to `/dashboard`
2. Click "Generate New Video" or goto `/videos/generate`
3. Fill in business name and topic
4. Submit form
5. Video should appear in `/videos` with status "processing"

### Test Email:
1. Sign up with your real email
2. Check inbox for welcome email
3. Go to pricing and complete a payment
4. Check inbox for payment receipt

---

## 📊 Dashboard Overview

Once logged in, you'll see:

```
┌─────────────────────────────────────┐
│ STATS (Top)                         │
├─────────────────────────────────────┤
│ Active Services │ Videos │ Views    │
│ Monthly Spend   │ Storage Used      │
├─────────────────────────────────────┤
│ YOUR SERVICES          QUICK ACTIONS│
├───────────────────┬─────────────────┤
│ VPS Pro ($2500)   │ + New Service   │
│ Web Hosting ($1500) │ + Generate Video │
│                   │ 💳 Billing     │
│ RECENT VIDEOS     │ ⚙️  Settings    │
├───────────────────┼─────────────────┤
│ Video 1 [Play]    │ CURRENT PLAN    │
│ Video 2 [Play]    │ Business        │
│ Video 3 [Process] │ 50 videos/month │
│                   │ 50GB storage    │
│ [See All]         │ [Upgrade Plan]  │
│                   │ SUPPORT         │
│                   │ [Contact Support]
│                   │                 │
└───────────────────┴─────────────────┘
```

---

## 🎬 Pages Overview

| URL | Purpose | Status |
|-----|---------|--------|
| `/` | Landing page | ✅ Ready |
| `/auth/signin` | Login | ✅ Ready |
| `/auth/signup` | Register | ✅ Ready |
| `/dashboard` | Main dashboard | ✅ Ready |
| `/pricing` | Pricing plans | ✅ Ready |
| `/videos` | Video listing | ✅ Ready |
| `/videos/generate` | Create video form | ✅ Ready |
| `/api/auth/*` | Auth routes | ✅ Ready |
| `/api/payment/checkout` | Stripe integration | ✅ Ready |
| `/api/payment/webhook` | Stripe webhook | ✅ Ready |
| `/api/videos` | Video API | ✅ Ready |

---

## 💡 What's Working Now

✅ **User Management**
- Signup with email/password
- Login with credentials
- Session management
- Logout

✅ **Dashboard**
- Display active services
- Show generated videos
- Quick action links
- Plan information

✅ **Pricing**
- 3 plan options (Starter/Business/Enterprise)
- Feature comparison
- FAQ section

✅ **Payments**
- Stripe checkout integration
- Webhook processing
- Subscription creation/update
- Payment receipts via email

✅ **Email Notifications**
- Welcome emails on signup
- Payment receipts on checkout
- Subscription confirmations
- (Video ready emails coming soon)

✅ **Video Management**
- Generate video request form
- Video listing with status
- Mock data display (ready for real data)

---

## 🔧 Common Commands

```bash
# Development
npm run dev          # Start dev server (http://localhost:3000)
npm run build        # Build for production
npm start            # Run production build

# Database
npx prisma db push  # Apply migrations
npx prisma studio  # Open database GUI
npx prisma generate # Regenerate client types

# Other
npm run lint        # Check code style
npm test           # Run tests (when implemented)
```

---

## 🚢 Deploy to Production

### On GCP VM:

```bash
# SSH into VM
gcloud compute ssh migrated-vm-asia --zone=asia-south1-b

# Pull latest code
git pull

# Install dependencies
npm install

# Build
npm run build

# Start with PM2
pm2 start npm --name hostamar -- start

# View logs
pm2 logs hostamar
```

For detailed deployment steps, see `DEPLOYMENT_GUIDE_MVP.md`

---

## 🐛 Troubleshooting

### "Port 3000 already in use"
```bash
# Find what's using port 3000
lsof -i :3000

# Kill the process
kill -9 <PID>

# Or use different port
PORT=3001 npm run dev
```

### "Cannot find module '@/lib/prisma'"
```bash
# Regenerate Prisma client
npx prisma generate

# Restart dev server
npm run dev
```

### "Database.sqlite.lock"
```bash
# Kill all node processes
pkill -f node

# Restart
npm run dev
```

### "Email not sending"
- Check SMTP credentials in `.env.local`
- For Gmail: Enable 2FA and generate app password
- Check console logs: `npm run dev` shows email errors

### "Stripe key not found"
- Add to `.env.local`:
  ```env
  STRIPE_SECRET_KEY=sk_test_xxx
  STRIPE_PUBLIC_KEY=pk_test_xxx
  ```
- Restart dev server

---

## 📱 Test on Mobile

### Local Network:
```bash
# Get your local IP (Mac/Linux)
ipconfig getifaddr en0

# Or Windows
ipconfig

# Visit from phone on same network
http://YOUR_IP:3000
```

### Mobile Responsive:
- Open DevTools (F12)
- Click device icon
- Select iPhone/Android

---

## 🎯 What to Test Next

1. **Authentication**
   - [ ] Sign up successfully
   - [ ] Receive welcome email
   - [ ] Login works
   - [ ] Session persists
   - [ ] Logout works

2. **Dashboard**
   - [ ] All sections visible
   - [ ] Stats display correctly
   - [ ] Services list shows
   - [ ] Videos list shows
   - [ ] Responsive on mobile

3. **Pricing & Payments**
   - [ ] All 3 plans visible
   - [ ] Stripe checkout works
   - [ ] Payment successful
   - [ ] Receipt email received
   - [ ] Plan updates in dashboard

4. **Videos**
   - [ ] Generate form accessible
   - [ ] Can submit video request
   - [ ] Video appears in list
   - [ ] Status tracking shows "processing"

5. **Email System**
   - [ ] Welcome email sent
   - [ ] Payment receipt sent
   - [ ] Upgrade emails sent
   - [ ] Emails are properly formatted

---

## 📈 Next Milestone: 80% MVP

To reach 80% completion, we need:

1. **Video Generation API** (20%)
   - Connect to OpenAI for script generation
   - Setup FFmpeg for rendering
   - Create background job queue
   - Send "video ready" emails

2. **Real Data Integration** (5%)
   - Replace mock data with Prisma queries
   - Real dashboard stats
   - Real video listings

3. **Advanced Features** (5%)
   - Video download endpoint
   - Video sharing functionality
   - Basic video analytics

**Estimated Time**: 2-3 weeks for a small team

---

## 📞 Support

**Issues?** Check:
1. `DEPLOYMENT_GUIDE_MVP.md` - Detailed setup & troubleshooting
2. `MVP_IMPLEMENTATION_SUMMARY.md` - Technical details
3. Logs: `npm run dev` output or PM2 logs
4. Console: Browser DevTools F12

**Stuck?** Create an issue or contact support@hostamar.com

---

**Happy Testing! 🎉**

Start with: `npm run dev` then visit http://localhost:3000
MINIO_SECRET_KEY="your-secret-key"

# Optional: Better Voice Quality
ELEVENLABS_API_KEY="your-key-here"

# Email Notifications
SMTP_HOST="smtp.gmail.com"
SMTP_USER="[email protected]"
SMTP_PASS="your-app-password"

# Payment (Add later)
BKASH_API_KEY=""
SSLCOMMERZ_KEY=""
```

### **Step 3: Setup Database**

```powershell
# Initialize Prisma
npx prisma generate
npx prisma db push

# Open Prisma Studio to view database
npx prisma studio
```

### **Step 4: Run Development Server**

```powershell
npm run dev
```

Visit: http://localhost:3000

---

## 📋 Onboarding Your First Customer (Manual Process)

### **Day 0: Preparation**
1. Create 5-10 video templates (Canva Pro recommended)
2. Prepare background music (royalty-free)
3. Design your logo watermark
4. Write sample scripts for different industries

### **Day 1: Customer Signs Up**
1. Customer visits hostamar.com
2. Fills signup form:
   - Name, email, password
   - Business name
   - Industry (dropdown)
   - Social media links
   - Uploads logo
   - Selects brand color
3. Selects subscription plan
4. Makes payment (bKash/manual for now)

### **Day 2: You Setup Their Business**
1. Login to admin panel
2. Verify payment
3. Activate subscription
4. Generate first 3 videos:
   ```powershell
   npm run video:generate -- --customerId=<id> --topic="Introduction"
   ```
5. Send welcome email with:
   - Login credentials
   - First videos
   - Instructions to download

### **Day 3-7: Automated Videos**
- System generates 2 videos per day
- Customer receives email notifications
- Videos appear in their dashboard
- They download and post on Facebook/Instagram

### **Week 2+: Full Automation**
- Cron job runs daily at 2 AM
- Generates videos for all customers
- Sends notifications
- Tracks analytics

---

## 🎬 Manual Video Generation (While Building Automation)

### **Quick Video Creation Process:**

1. **Get Customer Info:**
   ```sql
   SELECT * FROM "Customer" 
   JOIN "Business" ON "Customer".id = "Business"."customerId"
   WHERE email = '[email protected]';
   ```

2. **Generate Script:**
   - Open ChatGPT or use your GitHub Models
   - Prompt: "Create a 45-second video script for [business name] in [industry]. Topic: [topic]"
   - Save script

3. **Create Video (Canva Method - Fastest):**
   - Open Canva Pro
   - Choose "Video" → Instagram Reel (1080x1920)
   - Use template
   - Replace text with script
   - Add customer logo
   - Apply brand colors
   - Add background music
   - Export as MP4

4. **Upload to Dashboard:**
   - Upload to your MinIO storage
   - Add record to database:
     ```sql
     INSERT INTO "Video" (customerId, title, script, url, status)
     VALUES (...);
     ```
   - Send email notification

5. **Customer Downloads & Posts**

**Time per video:** 10-15 minutes (manual)  
**Time per video:** 2-3 minutes (automated)

---

## 💰 Monetization Strategy

### **Phase 1: Manual Service (Week 1-2)**
**Target:** 5-10 customers

**Your Process:**
1. Onboard customer (15 min)
2. Generate 3 videos manually (30 min)
3. Setup their hosting (30 min)
4. **Total time:** ~75 min per customer
5. **Revenue:** ৳2,000-3,500 per customer
6. **Profit:** ৳1,500-3,000 per customer (after costs)

**Weekly Revenue:** ৳10,000-25,000 (5-10 customers)

---

### **Phase 2: Semi-Automated (Week 3-4)**
**Target:** 20-30 customers

**Your Process:**
1. Customer self-signup (0 min)
2. Videos auto-generated (5 min supervision)
3. Hosting auto-provisioned (0 min)
4. **Your time:** ~5 min per customer

**Weekly Revenue:** ৳40,000-70,000 (20-30 customers)

---

### **Phase 3: Fully Automated (Month 2+)**
**Target:** 50-100 customers

**Your Process:**
1. Everything automated
2. You just monitor and support
3. **Your time:** 1-2 hours per day

**Monthly Revenue:** ৳1,00,000-3,00,000 (50-100 customers)  
**Your Profit:** ~70-80% (৳70,000-2,40,000)

---

## 🎯 Your Immediate Next Steps

### **This Week:**

#### **Day 1 (Today):**
- [ ] Setup hostamar-platform locally
- [ ] Test the landing page
- [ ] Create `.env.local` with your tokens
- [ ] Run `npm install && npm run dev`

#### **Day 2:**
- [ ] Setup database (PostgreSQL on GCP or local)
- [ ] Create Prisma migrations
- [ ] Test customer signup flow
- [ ] Create 5 Canva video templates

#### **Day 3:**
- [ ] Register hostamar.com domain (if not done)
- [ ] Point DNS to your GCP server (34.47.163.149)
- [ ] Setup Nginx reverse proxy
- [ ] Install SSL certificate (Let's Encrypt)

#### **Day 4:**
- [ ] Deploy to production
- [ ] Test full signup → video generation flow
- [ ] Create pricing/terms/privacy pages
- [ ] Setup email notifications

#### **Day 5-7:**
- [ ] Onboard your first 3-5 customers (friends/family)
- [ ] Generate 10 videos for each
- [ ] Collect feedback
- [ ] Fix any issues

### **Week 2:**
- [ ] Automate video generation script
- [ ] Setup cron job for daily videos
- [ ] Add payment gateway (bKash/SSLCommerz)
- [ ] Create admin dashboard
- [ ] Launch publicly!

---

## 📊 Success Metrics

### **Month 1 Goals:**
- ✅ 10 paying customers
- ✅ ৳20,000-30,000 revenue
- ✅ 50+ videos generated
- ✅ 90%+ customer satisfaction

### **Month 3 Goals:**
- ✅ 30-50 customers
- ✅ ৳60,000-1,00,000 revenue
- ✅ Fully automated pipeline
- ✅ 5-star reviews

### **Month 6 Goals:**
- ✅ 100+ customers
- ✅ ৳2,00,000+ revenue
- ✅ Team expansion (1-2 support staff)
- ✅ New service offerings

---

## 🆘 Need Help?

### **Common Issues:**

**Q: Video generation is slow**
A: Use Canva templates initially. Automate later.

**Q: No PostgreSQL database**
A: Use SQLite for quick testing: Change `datasource db` to `provider = "sqlite"`

**Q: MinIO not setup**
A: Use local file storage initially, migrate to MinIO later

**Q: No customers yet**
A: Offer first month free to 5 test users. Get testimonials.

---

## 🎉 You're Ready!

**Your competitive advantages:**
1. ✅ Hybrid cloud infrastructure (already setup)
2. ✅ AI automation expertise
3. ✅ Unique value proposition (hosting + videos)
4. ✅ High profit margins (70-80%)
5. ✅ Scalable system

**Timeline to first paying customer:** 5-7 days  
**Timeline to ৳50,000/month:** 4-6 weeks  
**Timeline to ৳2,00,000/month:** 3-4 months

---

## 🚀 Let's Deploy!

**Want me to:**
1. ✅ Deploy this to your GCP server right now?
2. ✅ Setup the database and migrations?
3. ✅ Create the Nginx configuration?
4. ✅ Generate your first test videos?

**Just say the word and I'll start! 🔥**
