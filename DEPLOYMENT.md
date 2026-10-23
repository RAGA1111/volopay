# Deployment Guide - Streamlit Community Cloud

This guide will get your Revenue Intelligence Inbox live on the internet in under 5 minutes.

---

## Prerequisites

- GitHub account (free)
- Streamlit Community Cloud account (free, sign in with GitHub)

---

## Step 1: Create GitHub Repository

### Option A: Using GitHub Desktop (Easiest)

1. **Download GitHub Desktop**: https://desktop.github.com/
2. **Install and sign in** with your GitHub account
3. Click **"Add"** → **"Add Existing Repository"**
4. Select folder: `C:\Users\RAGA T\OneDrive\Desktop\volopay-Raga T KIT`
5. Click **"Create Repository"**
6. Add description: "Revenue Intelligence Inbox - Sales conversation prioritization tool"
7. Click **"Publish repository"**
8. ✅ Choose **"Public"** (required for Streamlit free tier)
9. Click **"Publish"**

**Done!** Your code is now on GitHub.

### Option B: Using Command Line

Open PowerShell in your project folder:

```powershell
cd "C:\Users\RAGA T\OneDrive\Desktop\volopay-Raga T KIT"

# Initialize git
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit - Revenue Intelligence Inbox MVP"

# Create main branch
git branch -M main

# Add GitHub remote (replace with your repo URL)
git remote add origin https://github.com/YOUR-USERNAME/revenue-intelligence-inbox.git

# Push to GitHub
git push -u origin main
```

**Create the GitHub repo first:**
1. Go to https://github.com/new
2. Name: `revenue-intelligence-inbox`
3. Public repository
4. Don't add README, .gitignore, or license (we already have them)
5. Click "Create repository"
6. Copy the HTTPS URL and use it in the `git remote add` command above

---

## Step 2: Deploy to Streamlit Cloud

1. **Go to**: https://streamlit.io/cloud

2. **Sign in** with your GitHub account

3. **Click "New app"** (big button top right)

4. **Configure your app:**
   - Repository: `your-username/revenue-intelligence-inbox`
   - Branch: `main`
   - Main file path: `app.py`
   - App URL (optional): Choose a custom subdomain or keep default

5. **Click "Deploy!"**

6. **Wait 2-3 minutes** while it builds...

7. **🎉 Your app is live!**

Your URL will be:
```
https://your-username-revenue-intelligence-inbox.streamlit.app
```

---

## Step 3: Test Your Deployment

1. **Open the live URL** in an incognito/private browser window

2. **Import sample data:**
   - Click "Import Data"
   - Download `sample_data.csv` from your GitHub repo
   - Upload it to the app
   - Complete the import workflow

3. **Test all pages:**
   - ✅ Overview shows metrics
   - ✅ Inbox displays conversations
   - ✅ Import accepts new files
   - ✅ Exports generate downloads

4. **Verify routing:**
   - Check that high-priority conversations show evidence
   - Review rationale explanations
   - Test manual corrections

---

## Step 4: Share Your Links

Add to your slide deck and README:

**Live Demo:**
```
https://your-username-revenue-intelligence-inbox.streamlit.app
```

**Source Code:**
```
https://github.com/your-username/revenue-intelligence-inbox
```

**Sample Data:**
```
https://github.com/your-username/revenue-intelligence-inbox/blob/main/sample_data.csv
```

---

## Important Notes for Streamlit Cloud

### Data Persistence

⚠️ **Streamlit Cloud apps restart periodically**, which clears the SQLite database.

**For your demo, this is fine because:**
- Reviewers will import their own test data
- Shows the import workflow clearly
- No sensitive data is permanently stored

**During your recorded demo:**
1. Start with empty app
2. Import sample_data.csv
3. Show the workflow from scratch
4. This demonstrates the full import process

### Database Note for Reviewers

Add this to your README or demo notes:

> **Note:** This is a demo deployment on Streamlit Community Cloud. The SQLite database 
> resets on app restart (by design for the free tier). For production use, connect to 
> PostgreSQL, MySQL, or another persistent database. The code is database-agnostic and 
> ready for production deployment.

---

## Troubleshooting

### Build Fails

**Check requirements.txt:**
- Versions are pinned (not using `>=`)
- No extra dependencies
- All packages are compatible

**Check logs in Streamlit Cloud:**
- Click "Manage app" → "Logs"
- Look for Python errors
- Most common: missing package or version conflict

### App Loads But Crashes

**Database initialization:**
- SQLite should work out of the box
- Check that `src/database.py` creates tables automatically
- Verify file paths use `Path(__file__).parent`

### Upload Not Working

**File size limit:**
- Streamlit Cloud: 200MB max (already configured in `.streamlit/config.toml`)
- Sample data is only 5KB, no issues

### Slow Performance

**First load (cold start):**
- Can take 30-60 seconds if app hasn't been used recently
- This is normal for free tier
- Subsequent loads are fast

---

## Optional: Custom Domain

If you want a custom domain:

1. **Upgrade to Streamlit Cloud Team plan** (optional, not needed for assignment)
2. **Or use a reverse proxy:**
   - Deploy behind Cloudflare
   - Point your domain to the Streamlit URL
   - Use CNAME record

For this assignment, the default `.streamlit.app` domain is perfect.

---

## Deployment Checklist

Before sharing your demo:

- [ ] App is deployed and accessible in private browser
- [ ] Sample data imports successfully
- [ ] All 4 pages load without errors
- [ ] Dashboard shows charts and metrics
- [ ] Inbox displays conversations with evidence
- [ ] Manual corrections work
- [ ] Exports generate and download
- [ ] Tests pass locally (`python tests/run_all_tests.py`)
- [ ] README has live demo link
- [ ] Slide deck includes deployment URL
- [ ] 3-minute demo video recorded with live app

---

## Monitoring Your App

**View app analytics:**
- Streamlit Cloud dashboard shows:
  - Visitor count
  - Resource usage
  - Error logs
  - Deployment history

**Check logs:**
- Click "Manage app" → "Logs"
- Real-time Python output
- Useful for debugging

---

## Updating Your App

After deployment, any changes you push to GitHub will auto-deploy:

```powershell
# Make your changes locally
# Then:

git add .
git commit -m "Description of changes"
git push

# Streamlit Cloud will auto-deploy in 1-2 minutes
```

**Or use GitHub web interface:**
- Edit files directly on GitHub
- Commit changes
- Auto-deploys immediately

---

## Production Deployment (Future)

When you're ready to move beyond the MVP:

### 1. Add Persistent Database

**Option A: Supabase (PostgreSQL, Free)**
```python
# Update src/database.py
import os
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///revenue_intelligence.db')
```

**Option B: PlanetScale (MySQL, Free)**
- Connect via connection string
- Same approach as above

**Option C: Neon (PostgreSQL, Free)**
- Serverless PostgreSQL
- Good for Streamlit apps

### 2. Environment Variables

In Streamlit Cloud:
- Go to "App settings" → "Secrets"
- Add:
```toml
DATABASE_URL = "postgresql://user:pass@host:5432/db"
```

### 3. Production Checklist

- [ ] Migrate to PostgreSQL/MySQL
- [ ] Add authentication (Streamlit auth or external)
- [ ] Enable HTTPS (automatic on Streamlit Cloud)
- [ ] Set up monitoring/alerts
- [ ] Regular backups of database
- [ ] Rate limiting for uploads
- [ ] Add user roles/permissions

---

## Support Resources

**Streamlit Documentation:**
- Deployment: https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app
- Secrets: https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management

**Community:**
- Forum: https://discuss.streamlit.io/
- Discord: https://discord.gg/streamlit

**Your Project:**
- Open an issue on your GitHub repo
- Check test output for debugging

---

## Success Criteria

Your deployment is successful when:

✅ App loads at public URL  
✅ Works in private/incognito browser (tests sharing)  
✅ Sample data imports without errors  
✅ Dashboard displays metrics and charts  
✅ Inbox shows prioritized conversations  
✅ Routing includes evidence and rationale  
✅ Manual corrections persist (until app restart)  
✅ Exports download successfully  
✅ No console errors in browser dev tools  
✅ App is responsive (not timing out)  

---

## Final Note

**For your assignment submission:**

Your Streamlit Cloud deployment demonstrates:
- ✅ Full-stack development (UI + backend + database)
- ✅ Deployment capability (DevOps awareness)
- ✅ Cloud platform experience
- ✅ Professional presentation (live demo URL)
- ✅ Production-ready code (works in real environment)

This is a strong signal for a Growth Associate role! 🚀

---

**Ready to deploy? Follow Step 1 above and you'll be live in 5 minutes!**
