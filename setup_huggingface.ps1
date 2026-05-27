# =====================================================================
# Neuronix HuggingFace Setup Guide - PowerShell
# =====================================================================
# This script helps you:
# 1. Set up your HuggingFace token
# 2. Configure the .env file
# 3. Test the embeddings pipeline
# 4. Run the ingestion monitor

Write-Host "`n" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Green
Write-Host "🧠 NEURONIX - HuggingFace Setup Guide" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Green
Write-Host ""

# Step 1: Check if .env exists and is configured
Write-Host "📋 Step 1: Checking .env configuration..." -ForegroundColor Cyan
$env_file = ".env"

if (Test-Path $env_file) {
    Write-Host "✅ .env file found" -ForegroundColor Green
    
    $content = Get-Content $env_file
    if ($content -like "*HF_TOKEN=*") {
        $hf_token = $content | Select-String "HF_TOKEN" | ForEach-Object { $_.Line.Split("=")[1] }
        
        if ($hf_token -eq "your_huggingface_token_here" -or [string]::IsNullOrWhiteSpace($hf_token)) {
            Write-Host "⚠️  HF_TOKEN is not configured" -ForegroundColor Yellow
        } else {
            Write-Host "✅ HF_TOKEN is configured" -ForegroundColor Green
        }
    } else {
        Write-Host "⚠️  HF_TOKEN not found in .env" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ .env file not found" -ForegroundColor Red
}

# Step 2: Instructions for getting HF Token
Write-Host ""
Write-Host "📚 Step 2: Get Your HuggingFace Token" -ForegroundColor Cyan
Write-Host "   1. Go to: https://huggingface.co/settings/tokens" -ForegroundColor White
Write-Host "   2. Sign up (free) or log in" -ForegroundColor White
Write-Host "   3. Click 'New token'" -ForegroundColor White
Write-Host "   4. Name it 'neuronix' for clarity" -ForegroundColor White
Write-Host "   5. Keep it as 'read' access (fine for downloading models)" -ForegroundColor White
Write-Host "   6. Copy the token" -ForegroundColor White

# Step 3: Set HF_TOKEN in .env
Write-Host ""
Write-Host "🔧 Step 3: Configure HF_TOKEN" -ForegroundColor Cyan

$token = Read-Host "Enter your HuggingFace token (or press Enter to skip)"

if (-not [string]::IsNullOrEmpty($token)) {
    # Update .env file
    if (Test-Path $env_file) {
        $content = Get-Content $env_file
        $updated_content = $content -replace 'HF_TOKEN=.*', "HF_TOKEN=$token"
        $updated_content | Set-Content $env_file
        Write-Host "✅ HF_TOKEN saved to .env" -ForegroundColor Green
    }
    
    # Also set in current PowerShell session
    $env:HF_TOKEN = $token
    Write-Host "✅ HF_TOKEN set in current session" -ForegroundColor Green
} else {
    Write-Host "⚠️  Token not provided - using existing configuration" -ForegroundColor Yellow
}

# Step 4: Show cache folder info
Write-Host ""
Write-Host "💾 Step 4: Cache Configuration" -ForegroundColor Cyan
Write-Host "   Cache folder: ./hf_cache" -ForegroundColor White
Write-Host "   Purpose: Store downloaded HuggingFace models locally" -ForegroundColor White
Write-Host "   Benefit: Avoid repeated 404s and slow downloads" -ForegroundColor White
Write-Host "   Status: Auto-created on first run ✅" -ForegroundColor Green

# Step 5: Configuration summary
Write-Host ""
Write-Host "📊 Step 5: Configuration Summary" -ForegroundColor Cyan
Write-Host ""

$config_summary = @"
🔐 HUGGINGFACE SETUP:
   • Embedding Model: sentence-transformers/all-MiniLM-L6-v2
   • Cache Folder: ./hf_cache (auto-created)
   • HF_TOKEN: Reduces rate-limiting and enables faster downloads

🚀 WHAT'S FIXED:
   ✅ Unauthenticated HuggingFace warnings eliminated
   ✅ 404 errors for processor_config.json eliminated
   ✅ Model caching configured (faster subsequent loads)
   ✅ All embedding initialization standardized

📋 NEXT STEPS:
   1. Start ingestion:
      python scripts/neuronix_ingest.py

   2. Monitor progress (2-minute updates):
      python ingestion_monitor_enhanced.py

   3. Run a query:
      python neuronix_query.py "What is depression?"

   4. Or use chat engine:
      python app.py   (if Streamlit available)
"@

Write-Host $config_summary -ForegroundColor White

# Step 6: Verify Python environment
Write-Host ""
Write-Host "✅ Step 6: Verify Environment" -ForegroundColor Cyan

try {
    python --version
    Write-Host "✅ Python is available" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Python not found in PATH" -ForegroundColor Yellow
}

# Step 7: Offer to run ingestion monitor
Write-Host ""
$run_monitor = Read-Host "Would you like to start the ingestion monitor now? (y/n)"

if ($run_monitor -eq "y" -or $run_monitor -eq "Y") {
    Write-Host ""
    Write-Host "🚀 Starting Ingestion Monitor..." -ForegroundColor Green
    Write-Host "   Reports every 2 minutes" -ForegroundColor Gray
    Write-Host "   Press Ctrl+C to stop" -ForegroundColor Gray
    Write-Host ""
    
    python ingestion_monitor_enhanced.py
} else {
    Write-Host ""
    Write-Host "✅ Setup complete! You're ready to go." -ForegroundColor Green
    Write-Host "   Run when ready:" -ForegroundColor Gray
    Write-Host "   python ingestion_monitor_enhanced.py" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Green
Write-Host "🎉 Neuronix Setup Complete" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Green
Write-Host ""
