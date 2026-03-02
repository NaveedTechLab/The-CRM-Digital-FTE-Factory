# HuggingFace Spaces Deployment

## CRM Digital FTE Factory - Free Deployment

### What's Included
- Web Support Form (Next.js)
- Dashboard API (FastAPI)
- Email ingestion + auto-reply
- WhatsApp webhook + auto-reply
- Ticket management + customer tracking

### Database
Uses **Neon.tech** free PostgreSQL (external, not in container).

---

## Step-by-Step Deployment

### Step 1: Create Neon Database (if you don't have one)

1. Go to [neon.tech](https://neon.tech) and sign up (free)
2. Create a new project
3. Copy the **connection string** (looks like: `postgresql://user:pass@ep-xxx.region.aws.neon.tech/dbname?sslmode=require`)
4. Run the schema SQL from `phase-2-core-infrastructure-database/postgresql/init-scripts/01-init-db.sql` in the Neon SQL editor

### Step 2: Create HuggingFace Space

1. Go to [huggingface.co](https://huggingface.co) and sign up/login
2. Click **"New Space"** (top right + button)
3. Configure:
   - **Space name:** `crm-digital-fte`
   - **SDK:** Select **Docker**
   - **Visibility:** Public (or Private)
   - **Hardware:** Free (CPU basic - 2 vCPU, 16 GB)
4. Click **"Create Space"**

### Step 3: Push Code to Space

```bash
# Clone the HuggingFace Space repo
git clone https://huggingface.co/spaces/<YOUR_USERNAME>/crm-digital-fte
cd crm-digital-fte

# Copy project files from your main repo
cp -r /path/to/The-CRM-Digital-FTE-Factory/* .

# Commit and push
git add .
git commit -m "Deploy CRM Digital FTE Factory"
git push
```

### Step 4: Set Secrets

In the HuggingFace Space settings page:

1. Go to **Settings** tab
2. Scroll to **"Repository secrets"**
3. Add these secrets:

| Secret Name | Value |
|---|---|
| `DATABASE_URL` | Your Neon PostgreSQL connection string |
| `GMAIL_SENDER_EMAIL` | your-email@gmail.com |
| `GMAIL_APP_PASSWORD` | Gmail app password |
| `WHATSAPP_PHONE_NUMBER_ID` | Meta phone number ID |
| `WHATSAPP_ACCESS_TOKEN` | Meta WhatsApp token |
| `WHATSAPP_VERIFY_TOKEN` | Your webhook verify token |

### Step 5: Wait for Build

HuggingFace will auto-build and deploy. Takes ~5-10 minutes.

Watch the **Logs** tab for progress.

### Step 6: Access Your App

Your app will be live at:
```
https://<YOUR_USERNAME>-crm-digital-fte.hf.space
```

| Page | URL |
|---|---|
| Web Form | `https://xxx.hf.space/` |
| Dashboard | `https://xxx.hf.space/dashboard` |
| API Stats | `https://xxx.hf.space/api/stats` |
| Health | `https://xxx.hf.space/health` |
| WhatsApp Webhook | `https://xxx.hf.space/webhook` |
