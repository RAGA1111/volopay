# Pre-Deployment Checklist ✅

Complete this checklist before deploying to ensure everything works perfectly.

---

## Local Testing (5 minutes)

### 1. Install and Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
- [ ] App starts without errors
- [ ] Opens in browser at http://localhost:8501

### 2. Test Import Pipeline
- [ ] Navigate to "Import Data"
- [ ] Upload `sample_data.csv`
- [ ] Validation shows 15 valid records
- [ ] Reconciliation shows 15 new records
- [ ] Commit completes successfully
- [ ] Analysis runs on all records

### 3. Test Dashboard
- [ ] Navigate to "Overview"
- [ ] See "Total Conversations: 15"
- [ ] Priority distribution chart displays
- [ ] Activity by type shows data
- [ ] Category distribution visible
- [ ] No errors in console

### 4. Test Inbox
- [ ] Navigate to "Inbox"
- [ ] See 15 conversations listed
- [ ] Filter by priority "high" works
- [ ] Select a conversation
- [ ] See evidence quoted in classification
- [ ] Rationale is clear and readable
- [ ] Next action is specific

### 5. Test Manual Corrections
- [ ] In Inbox, select any conversation
- [ ] Click "Edit Classification"
- [ ] Change priority to "low"
- [ ] Add reason: "Test override"
- [ ] Apply override successfully
- [ ] See override reflected immediately

### 6. Test Re-Import (Critical!)
- [ ] Go back to "Import Data"
- [ ] Upload `sample_data.csv` again
- [ ] Reconciliation shows: **0 new, 15 unchanged**
- [ ] No duplicates created ✅
- [ ] Your manual override from step 5 still active

### 7. Test Exports
- [ ] Navigate to "Exports"
- [ ] Set format: CSV
- [ ] Filter: Priority = "high"
- [ ] Click "Generate Export"
- [ ] Download CSV file
- [ ] Download manifest JSON
- [ ] Open manifest - verify checksums present

### 8. Run Test Suite
```bash
python tests/run_all_tests.py
```
- [ ] All import tests pass ✅
- [ ] All routing tests pass ✅
- [ ] All export tests pass ✅
- [ ] No errors or failures

---

## Code Quality (2 minutes)

### 9. File Structure
- [ ] All 4 page files exist in `pages/`
- [ ] All 9 module files exist in `src/`
- [ ] All 4 test files exist in `tests/`
- [ ] `requirements.txt` has exact versions
- [ ] `.gitignore` excludes `.db` and `__pycache__`
- [ ] `sample_data.csv` is included

### 10. Documentation
- [ ] `README.md` complete with deployment section
- [ ] `QUICKSTART.md` exists
- [ ] `DEPLOYMENT.md` has Streamlit Cloud instructions
- [ ] `PROJECT_SUMMARY.md` complete
- [ ] Code has inline comments

---

## Git Setup (3 minutes)

### 11. Initialize Repository

**Option A: Using the script (easier)**
```powershell
.\deploy.ps1
```

**Option B: Manual**
```bash
git init
git add .
git commit -m "Initial commit - Revenue Intelligence Inbox MVP"
git branch -M main
```

- [ ] Git repository initialized
- [ ] All files committed
- [ ] On main branch

### 12. Create GitHub Repository
1. Go to https://github.com/new
2. Name: `revenue-intelligence-inbox`
3. Public repository ✅ (required for free Streamlit)
4. Don't add README, .gitignore, license
5. Create repository
6. Copy HTTPS URL

- [ ] GitHub repo created
- [ ] Set to PUBLIC
- [ ] URL copied

### 13. Push to GitHub
```bash
git remote add origin YOUR-GITHUB-URL
git push -u origin main
```

- [ ] Remote added successfully
- [ ] Pushed to GitHub
- [ ] Code visible at github.com/your-username/revenue-intelligence-inbox

---

## Streamlit Cloud Deployment (5 minutes)

### 14. Deploy Application
1. Go to https://streamlit.io/cloud
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Branch: `main`
6. Main file: `app.py`
7. Click "Deploy"

- [ ] Signed into Streamlit Cloud
- [ ] Repository selected
- [ ] Deployment started
- [ ] Build completes (watch logs)
- [ ] App is live at your URL

### 15. Test Deployed App
**Open in PRIVATE/INCOGNITO browser** (tests public access)

- [ ] App loads at your Streamlit URL
- [ ] No errors on landing page
- [ ] Can navigate between pages
- [ ] Import Data page accessible
- [ ] Download sample_data.csv from GitHub
- [ ] Upload sample data to deployed app
- [ ] Import completes successfully
- [ ] Dashboard shows metrics
- [ ] Inbox displays conversations
- [ ] Exports work and download

---

## Final Verification (2 minutes)

### 16. Browser Console Check
Open browser dev tools (F12):
- [ ] No red errors in Console tab
- [ ] No 404 or 500 errors in Network tab
- [ ] All pages load < 3 seconds (after warm-up)

### 17. Demo Preparation
- [ ] Copy your live Streamlit URL
- [ ] Test URL in 3+ browsers
- [ ] URL works on mobile (bonus)
- [ ] Sample data file accessible
- [ ] GitHub repo is public

---

## Assignment Submission Checklist

### 18. Required Links
Add these to your slide deck:

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

- [ ] All three URLs added to slides
- [ ] All URLs tested in private browser
- [ ] URLs formatted as clickable links

### 19. 3-Minute Demo Video
Record your screen showing:
- [ ] 0:00-0:25 - Overview and business purpose
- [ ] 0:25-1:05 - Inbox with evidence-based routing
- [ ] 1:05-1:40 - A difficult routing decision explained
- [ ] 1:40-2:30 - Import workflow and reconciliation
- [ ] 2:30-3:00 - Exports and manifest

**Recording tips:**
- Use the LIVE deployed app (not localhost)
- Have sample data pre-downloaded
- Close other browser tabs
- Test audio before recording
- Keep cursor movements smooth

### 20. Five-Slide Deck
- [ ] Slide 1: Problem, user, product, workflow
- [ ] Slide 2: Dashboard metrics with screenshot
- [ ] Slide 3: Routing example with evidence
- [ ] Slide 4: Test results (duplicate handling, overrides)
- [ ] Slide 5: Three findings + one rejected decision

Each slide includes:
- [ ] Screenshot from live app
- [ ] Clear data/evidence
- [ ] Brief explanation

---

## Final Checklist Summary

Before you submit:

### Technical
✅ Local app works perfectly  
✅ All tests pass  
✅ Deployed to Streamlit Cloud  
✅ Works in private browser  
✅ No console errors  

### Content
✅ Sample data imports successfully  
✅ Dashboard shows metrics  
✅ Routing shows evidence  
✅ Duplicate handling tested  
✅ Manual overrides work  
✅ Exports download  

### Submission
✅ Live URL in slide deck  
✅ GitHub URL in slide deck  
✅ 3-minute demo recorded  
✅ Five slides complete  
✅ All links tested  

---

## Troubleshooting

### "Import doesn't work on deployed app"
- Check Streamlit Cloud logs
- Verify file upload size < 200MB
- Check browser console for errors

### "Database resets between visits"
- **This is expected!** Streamlit Cloud free tier
- Mention in your demo: "Fresh import each time"
- Shows the import workflow clearly

### "Charts not displaying"
- Check plotly is installed
- Verify data has values for that chart
- Check browser console

### "Can't find my app on Streamlit Cloud"
- Go to https://share.streamlit.io/
- Click your avatar → "Manage apps"
- Find your app in the list

---

## You're Ready! 🚀

If you've checked all the boxes above, you're ready to:
1. Submit your assignment
2. Share your demo
3. Show off your work

**Great job building a complete, production-ready MVP!**

---

## Post-Deployment

After submission, you can:
- Share on LinkedIn with live demo link
- Add to your portfolio
- Extend with additional features
- Deploy to production with PostgreSQL
- Use as a reference for future projects

**This is a solid portfolio piece. Well done! 🎉**
