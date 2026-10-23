# Revenue Intelligence Inbox - Quick Deploy Script
# Run this script to initialize git and prepare for GitHub/Streamlit deployment

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Revenue Intelligence Inbox" -ForegroundColor Cyan
Write-Host "Quick Deploy Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
$gitInstalled = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitInstalled) {
    Write-Host "❌ Git is not installed!" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "✅ Git is installed" -ForegroundColor Green
Write-Host ""

# Check if already initialized
if (Test-Path .git) {
    Write-Host "⚠️  Git repository already initialized" -ForegroundColor Yellow
    $response = Read-Host "Do you want to reinitialize? This will remove git history. (yes/no)"
    if ($response -eq "yes") {
        Remove-Item -Recurse -Force .git
        Write-Host "✅ Removed existing git repository" -ForegroundColor Green
    } else {
        Write-Host "Keeping existing repository" -ForegroundColor Yellow
        Write-Host ""
    }
}

# Initialize git if needed
if (-not (Test-Path .git)) {
    Write-Host "📦 Initializing Git repository..." -ForegroundColor Cyan
    git init
    git branch -M main
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
    Write-Host ""
}

# Show git status
Write-Host "📊 Current Git Status:" -ForegroundColor Cyan
git status --short
Write-Host ""

# Prompt for GitHub repository URL
Write-Host "================================" -ForegroundColor Cyan
Write-Host "GitHub Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Before continuing, create a GitHub repository:" -ForegroundColor Yellow
Write-Host "1. Go to: https://github.com/new" -ForegroundColor White
Write-Host "2. Repository name: revenue-intelligence-inbox" -ForegroundColor White
Write-Host "3. Make it PUBLIC (required for Streamlit free tier)" -ForegroundColor White
Write-Host "4. Don't add README, .gitignore, or license (we have them)" -ForegroundColor White
Write-Host "5. Click 'Create repository'" -ForegroundColor White
Write-Host "6. Copy the HTTPS URL" -ForegroundColor White
Write-Host ""

$repoUrl = Read-Host "Paste your GitHub repository URL (or press Enter to skip)"

if ($repoUrl) {
    # Check if remote already exists
    $remoteExists = git remote get-url origin 2>$null
    
    if ($remoteExists) {
        Write-Host "⚠️  Remote 'origin' already exists" -ForegroundColor Yellow
        $response = Read-Host "Do you want to update it? (yes/no)"
        if ($response -eq "yes") {
            git remote set-url origin $repoUrl
            Write-Host "✅ Remote URL updated" -ForegroundColor Green
        }
    } else {
        git remote add origin $repoUrl
        Write-Host "✅ Remote 'origin' added" -ForegroundColor Green
    }
    Write-Host ""
}

# Create initial commit
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Creating Initial Commit" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$hasCommits = git rev-parse HEAD 2>$null
if (-not $hasCommits) {
    Write-Host "📝 Adding all files..." -ForegroundColor Cyan
    git add .
    
    Write-Host "💾 Creating initial commit..." -ForegroundColor Cyan
    git commit -m "Initial commit - Revenue Intelligence Inbox MVP

- Complete Streamlit application with 4 pages
- Data import pipeline with reconciliation
- Evidence-based routing and classification
- Manual correction system with audit trail
- Export generation with manifest
- Comprehensive test suite
- Full documentation"
    
    Write-Host "✅ Initial commit created" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "ℹ️  Commits already exist in this repository" -ForegroundColor Yellow
    Write-Host ""
}

# Push to GitHub
if ($repoUrl) {
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "Push to GitHub" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
    
    $response = Read-Host "Ready to push to GitHub? (yes/no)"
    if ($response -eq "yes") {
        Write-Host "🚀 Pushing to GitHub..." -ForegroundColor Cyan
        git push -u origin main
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Your code is now at: $repoUrl" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Push failed. You may need to authenticate." -ForegroundColor Yellow
            Write-Host "Run 'git push -u origin main' manually after setting up credentials." -ForegroundColor Yellow
        }
    }
    Write-Host ""
}

# Next steps
Write-Host "================================" -ForegroundColor Cyan
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. ✅ Code is ready for deployment" -ForegroundColor White
if ($repoUrl) {
    Write-Host "2. ✅ Code is on GitHub: $repoUrl" -ForegroundColor White
} else {
    Write-Host "2. ⚠️  Push to GitHub: git push -u origin main" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Deploy to Streamlit Cloud:" -ForegroundColor Cyan
Write-Host "  1. Go to: https://streamlit.io/cloud" -ForegroundColor White
Write-Host "  2. Sign in with GitHub" -ForegroundColor White
Write-Host "  3. Click 'New app'" -ForegroundColor White
Write-Host "  4. Select your repository" -ForegroundColor White
Write-Host "  5. Main file: app.py" -ForegroundColor White
Write-Host "  6. Click 'Deploy'" -ForegroundColor White
Write-Host "  7. Wait 2-3 minutes" -ForegroundColor White
Write-Host "  8. Your app is live! 🚀" -ForegroundColor White
Write-Host ""
Write-Host "📖 Full instructions: See DEPLOYMENT.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test locally first:" -ForegroundColor Yellow
Write-Host "  streamlit run app.py" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to finish"
