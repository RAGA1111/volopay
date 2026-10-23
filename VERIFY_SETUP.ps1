# Revenue Intelligence Inbox - Setup Verification Script
# Run this to verify your project is ready for deployment

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Revenue Intelligence Inbox" -ForegroundColor Cyan
Write-Host "Setup Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Check Python installation
Write-Host "1. Checking Python..." -ForegroundColor Cyan
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    $version = python --version 2>&1
    Write-Host "   ✅ Python installed: $version" -ForegroundColor Green
    
    # Check if version is 3.8+
    if ($version -match "Python 3\.(\d+)") {
        $minorVersion = [int]$matches[1]
        if ($minorVersion -lt 8) {
            Write-Host "   ⚠️  Python 3.8+ recommended (you have $version)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "   ❌ Python not found! Install from python.org" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# Check Git installation
Write-Host "2. Checking Git..." -ForegroundColor Cyan
$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
    $gitVersion = git --version 2>&1
    Write-Host "   ✅ Git installed: $gitVersion" -ForegroundColor Green
} else {
    Write-Host "   ❌ Git not found! Install from git-scm.com" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# Check required files
Write-Host "3. Checking Required Files..." -ForegroundColor Cyan
$requiredFiles = @(
    "app.py",
    "requirements.txt",
    "sample_data.csv",
    "README.md",
    ".gitignore",
    "pages\1_Overview.py",
    "pages\2_Inbox.py",
    "pages\3_Import_Data.py",
    "pages\4_Exports.py",
    "src\database.py",
    "src\readers.py",
    "src\validation.py",
    "src\reconciliation.py",
    "src\routing.py",
    "src\corrections.py",
    "src\metrics.py",
    "src\exports.py",
    "tests\test_imports.py",
    "tests\test_routing.py",
    "tests\test_exports.py"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "   ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file MISSING!" -ForegroundColor Red
        $missingFiles += $file
        $allGood = $false
    }
}
Write-Host ""

# Check if dependencies can be installed
Write-Host "4. Checking Dependencies..." -ForegroundColor Cyan
if (Test-Path "requirements.txt") {
    $requirements = Get-Content requirements.txt
    Write-Host "   📦 Required packages:" -ForegroundColor White
    foreach ($req in $requirements) {
        Write-Host "      - $req" -ForegroundColor Gray
    }
    
    $response = Read-Host "   Install dependencies now? (yes/no)"
    if ($response -eq "yes") {
        Write-Host "   Installing..." -ForegroundColor Cyan
        pip install -r requirements.txt
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Dependencies installed successfully" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  Installation had warnings (check output above)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ⏭️  Skipped installation" -ForegroundColor Yellow
    }
}
Write-Host ""

# Check sample data
Write-Host "5. Checking Sample Data..." -ForegroundColor Cyan
if (Test-Path "sample_data.csv") {
    $lineCount = (Get-Content "sample_data.csv" | Measure-Object -Line).Lines
    $fileSize = (Get-Item "sample_data.csv").Length
    Write-Host "   ✅ Sample data found" -ForegroundColor Green
    Write-Host "      Lines: $lineCount" -ForegroundColor Gray
    Write-Host "      Size: $([math]::Round($fileSize/1KB, 2)) KB" -ForegroundColor Gray
} else {
    Write-Host "   ❌ sample_data.csv missing!" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# Check documentation
Write-Host "6. Checking Documentation..." -ForegroundColor Cyan
$docFiles = @(
    "START_HERE.md",
    "README.md",
    "QUICKSTART.md",
    "DEPLOYMENT.md",
    "DEMO_SCRIPT.md"
)

foreach ($doc in $docFiles) {
    if (Test-Path $doc) {
        Write-Host "   ✅ $doc" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  $doc missing (optional)" -ForegroundColor Yellow
    }
}
Write-Host ""

# Check deployment readiness
Write-Host "7. Deployment Readiness..." -ForegroundColor Cyan
if (Test-Path ".gitignore") {
    Write-Host "   ✅ .gitignore present" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  .gitignore missing" -ForegroundColor Yellow
}

if (Test-Path ".streamlit\config.toml") {
    Write-Host "   ✅ Streamlit config present" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Streamlit config missing (will use defaults)" -ForegroundColor Yellow
}

if (Test-Path ".git") {
    Write-Host "   ✅ Git repository initialized" -ForegroundColor Green
    $remote = git remote get-url origin 2>$null
    if ($remote) {
        Write-Host "   ✅ GitHub remote configured: $remote" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  No GitHub remote configured yet" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️  Git not initialized (run deploy.ps1)" -ForegroundColor Yellow
}
Write-Host ""

# Offer to run local test
Write-Host "8. Local Test..." -ForegroundColor Cyan
$response = Read-Host "   Run app locally to test? (yes/no)"
if ($response -eq "yes") {
    Write-Host "   🚀 Starting Streamlit..." -ForegroundColor Cyan
    Write-Host "   Press Ctrl+C to stop" -ForegroundColor Gray
    Write-Host ""
    streamlit run app.py
} else {
    Write-Host "   ⏭️  Skipped local test" -ForegroundColor Yellow
    Write-Host "   To test later, run: streamlit run app.py" -ForegroundColor Gray
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($allGood) {
    Write-Host "✅ All checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You are ready to deploy! Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Run: .\deploy.ps1 (sets up Git and GitHub)" -ForegroundColor White
    Write-Host "  2. Go to: https://streamlit.io/cloud" -ForegroundColor White
    Write-Host "  3. Deploy your app (takes 3 minutes)" -ForegroundColor White
    Write-Host ""
    Write-Host "📖 Full instructions: See DEPLOYMENT.md" -ForegroundColor Cyan
} else {
    Write-Host "⚠️  Some issues found (see above)" -ForegroundColor Yellow
    Write-Host ""
    if ($missingFiles.Count -gt 0) {
        Write-Host "Missing files:" -ForegroundColor Red
        foreach ($file in $missingFiles) {
            Write-Host "  - $file" -ForegroundColor Red
        }
    }
    Write-Host ""
    Write-Host "Fix these issues before deploying." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📚 Documentation available:" -ForegroundColor Cyan
Write-Host "  - START_HERE.md - Quick orientation" -ForegroundColor White
Write-Host "  - QUICKSTART.md - 10-step walkthrough" -ForegroundColor White
Write-Host "  - DEPLOYMENT.md - Deploy to Streamlit Cloud" -ForegroundColor White
Write-Host "  - DEMO_SCRIPT.md - Record your demo" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to finish"
