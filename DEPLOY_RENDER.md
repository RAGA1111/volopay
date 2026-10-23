# Deploy to Render

Alternative deployment option if you don't want to use Streamlit Cloud.

## Why Render?

- ✅ Free tier (no credit card for free tier)
- ✅ Supports Python/Streamlit apps
- ✅ Auto-deploy from GitHub
- ✅ Modern, fast platform
- ✅ Good for production

## Prerequisites

- GitHub account
- Code pushed to GitHub repository

## Deployment Steps

### 1. Push to GitHub

If you haven't already:

```powershell
.\deploy.ps1
```

This will initialize Git and push to GitHub.

### 2. Sign Up for Render

1. Go to https://render.com
2. Click "Get Started"
3. Sign up with GitHub
4. Authorize Render to access your repositories

### 3. Create New Web Service

1. Click "New +" button
2. Select "Web Service"
3. Connect your GitHub account (if not already)
4. Find and select `revenue-intelligence-inbox` repository
5. Click "Connect"

### 4. Configure Service

Render will auto-detect the `render.yaml` file and configure automatically.

**If you need to configure manually:**

- **Name:** `revenue-intelligence-inbox`
- **Region:** Oregon (or closest to you)
- **Branch:** `main`
- **Runtime:** Python 3
- **Build Command:** 
  ```
  pip install -r requirements.txt
  ```
- **Start Command:**
  ```
  streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
  ```
- **Plan:** Free

### 5. Add Environment Variables (Optional)

In the Environment section, you can add:

```
PYTHON_VERSION=3.11.0
STREAMLIT_SERVER_HEADLESS=true
```

### 6. Deploy

1. Click "Create Web Service"
2. Wait 3-5 minutes for build and deployment
3. Your app will be live at: `https://revenue-intelligence-inbox.onrender.com`

## Important Notes

### Database Persistence

⚠️ **Render free tier may have disk persistence limitations**

Your SQLite database might reset on:
- App restart
- Free tier inactivity (after 15 minutes of no requests)

**For your demo, this is fine** because:
- Reviewers will import their own test data
- Shows the import workflow clearly
- No sensitive data persists

**For production:**
- Upgrade to paid tier ($7/month) for persistent disk
- Or connect to PostgreSQL database (also available on Render)

### Cold Starts

Free tier apps spin down after 15 minutes of inactivity.
- First request after spin-down takes 30-60 seconds
- Subsequent requests are fast
- Keep-alive services can prevent this (not included in free tier)

### Build Time

Initial deployment takes 3-5 minutes:
- Installing Python dependencies
- Building the application
- Starting the server

## Verify Deployment

Once deployed:

1. **Open your Render URL** in browser
2. **Import sample data:**
   - Download `sample_data.csv` from your GitHub repo
   - Upload through the app's Import page
   - Verify it processes correctly

3. **Test all pages:**
   - Overview shows metrics
   - Inbox displays conversations
   - Exports work

4. **Test in private browser:**
   - Verifies public access
   - No authentication issues

## Troubleshooting

### Build Fails

**Check logs in Render dashboard:**
- Click on your service
- Go to "Logs" tab
- Look for Python errors

**Common issues:**
- Missing dependencies: Check `requirements.txt`
- Python version: Ensure 3.8+
- Port binding: Must use `$PORT` environment variable

### App Doesn't Load

**Check start command:**
```
streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```

**Verify health check:**
- Render uses `/_stcore/health` for Streamlit
- Already configured in `render.yaml`

### Database Resets

**Expected on free tier** - file system is ephemeral.

**Solutions:**
- Accept it for demo purposes
- Upgrade to paid tier ($7/month)
- Connect external database

## Updating Your App

After initial deployment, any changes pushed to GitHub will auto-deploy:

```powershell
git add .
git commit -m "Update description"
git push

# Render automatically detects and deploys
# Takes 2-3 minutes
```

## Monitoring

**View in Render dashboard:**
- Deployment status
- Build logs
- Runtime logs
- Metrics (requests, CPU, memory)
- Custom domain setup (paid tier)

## Custom Domain (Optional)

Render allows custom domains on free tier:

1. Go to service settings
2. Click "Custom Domain"
3. Add your domain
4. Update DNS records as shown
5. SSL certificate auto-generated

## Comparison: Render vs Streamlit Cloud

| Feature | Render | Streamlit Cloud |
|---------|--------|-----------------|
| Setup complexity | Medium | Very Easy |
| Configuration | Needs files | Zero config |
| Free tier | Yes | Yes |
| Cold start | Yes (15 min) | Yes |
| Build time | 3-5 minutes | 2-3 minutes |
| Persistence | Limited | Limited |
| Best for | General Python apps | Streamlit apps only |

## Recommendation

For this assignment:
- **Use Streamlit Cloud** if possible (easiest, built for Streamlit)
- **Use Render** if you need alternative platform
- **Both are free and work well for demos**

## Next Steps

After deployment:

1. ✅ Test your live URL
2. ✅ Import sample data
3. ✅ Verify all features work
4. ✅ Add URL to your slide deck
5. ✅ Record demo using live app
6. ✅ Submit assignment

## Support

**Render Documentation:**
- https://render.com/docs/deploy-streamlit
- https://render.com/docs/web-services

**Your Project:**
- Check logs in Render dashboard
- Review `render.yaml` configuration
- Test locally first: `streamlit run app.py`

---

**Ready to deploy on Render? Follow the steps above!**

Or use the easier option: `https://streamlit.io/cloud` 🚀
