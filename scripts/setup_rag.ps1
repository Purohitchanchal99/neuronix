#!/usr/bin/env powershell
# Quick Setup Script for Neuronix RAG System
# ==========================================
# Use this to set up the RAG pipeline in one command

Write-Host "`n🚀 NEURONIX RAG QUICK SETUP" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Check Python
Write-Host "✓ Checking Python installation..." -ForegroundColor Green
$pythonCmd = "C:\Users\admin\AppData\Local\Programs\Python\Python313\python.exe"

if (-not (Test-Path $pythonCmd)) {
    Write-Host "❌ Python not found at $pythonCmd" -ForegroundColor Red
    exit 1
}

# Set up environment
Write-Host "`n📌 Setting up environment..." -ForegroundColor Green

# Check GOOGLE_API_KEY
if (-not $env:GOOGLE_API_KEY) {
    Write-Host "`n⚠️  GOOGLE_API_KEY not set!" -ForegroundColor Yellow
    Write-Host "Get your key from: https://makersuite.google.com/app/apikey" -ForegroundColor Yellow
    Write-Host "`nSet it with:" -ForegroundColor Yellow
    Write-Host '  $env:GOOGLE_API_KEY = "your-api-key"' -ForegroundColor White
    Write-Host "  [Environment]::SetEnvironmentVariable('GOOGLE_API_KEY', 'your-api-key', 'User')" -ForegroundColor White
} else {
    Write-Host "✓ GOOGLE_API_KEY is set" -ForegroundColor Green
}

# Menu
Write-Host "`n" -ForegroundColor Cyan
Write-Host "Choose an option:" -ForegroundColor Cyan
Write-Host "  1) Show RAG System Status" -ForegroundColor White
Write-Host "  2) Start Vector Database Ingestion (Fast)" -ForegroundColor White
Write-Host "  3) Monitor Ingestion Progress" -ForegroundColor White
Write-Host "  4) Test Query System (Interactive)" -ForegroundColor White
Write-Host "  5) Test Query System (Automated)" -ForegroundColor White
Write-Host "  6) View Documentation" -ForegroundColor White
Write-Host "`n"

$choice = Read-Host "Enter choice (1-6)"

switch ($choice) {
    "1" {
        Write-Host "`n📊 RAG SYSTEM STATUS`n" -ForegroundColor Cyan
        
        # Check components
        if (Test-Path "data\vector_db") {
            Write-Host "✓ Vector Database: EXISTS" -ForegroundColor Green
            $size = (Get-ChildItem -Path "data\vector_db" -Recurse -Force | Measure-Object -Property Length -Sum).Sum / 1MB
            Write-Host "  Size: $([math]::Round($size, 2)) MB" -ForegroundColor White
        } else {
            Write-Host "✗ Vector Database: NOT FOUND" -ForegroundColor Red
        }
        
        $pdfCount = (Get-ChildItem -Path "docs" -Recurse -Filter "*.pdf" | Measure-Object).Count
        Write-Host "`n✓ Downloaded PDFs: $pdfCount" -ForegroundColor Green
        
        if (Test-Path "scripts\query_rag_system.py") {
            Write-Host "✓ Query System: READY" -ForegroundColor Green
        }
        
        if (Test-Path "scripts\fast_ingest.py") {
            Write-Host "✓ Fast Ingestion Script: READY" -ForegroundColor Green
        }
        
        Write-Host "`n"
    }
    
    "2" {
        Write-Host "`n⚡ STARTING FAST INGESTION" -ForegroundColor Cyan
        Write-Host "This will process 279 PDFs and create the vector database.`n" -ForegroundColor Yellow
        
        & $pythonCmd "scripts\fast_ingest.py"
        Write-Host "`n✅ Ingestion complete!`n" -ForegroundColor Green
    }
    
    "3" {
        Write-Host "`n📊 MONITORING INGESTION" -ForegroundColor Cyan
        Write-Host "Checking progress every 2 minutes...`n" -ForegroundColor Yellow
        
        & $pythonCmd "scripts\monitor_ingestion.py"
    }
    
    "4" {
        Write-Host "`n💬 INTERACTIVE QUERY MODE" -ForegroundColor Cyan
        Write-Host "Ask questions about psychology and clinical concepts.`n" -ForegroundColor Yellow
        
        & $pythonCmd "scripts\query_rag_system.py" "interactive"
    }
    
    "5" {
        Write-Host "`n🧪 AUTOMATED QUERY TEST" -ForegroundColor Cyan
        Write-Host "Testing with sample questions...`n" -ForegroundColor Yellow
        
        & $pythonCmd "scripts\query_rag_system.py" "test"
    }
    
    "6" {
        Write-Host "`n📚 RAG SYSTEM DOCUMENTATION" -ForegroundColor Cyan
        Write-Host @"
NEURONIX RAG SYSTEM - Quick Reference
======================================

COMPONENTS:
-----------
1. Vector Database (ChromaDB)
   - Location: data/vector_db
   - Stores 279 PDF books as embeddings
   
2. Ingestion Pipeline (fast_ingest.py)
   - Reads PDFs from docs/
   - Creates text chunks (1000 chars)
   - Generates embeddings (Google Gemini)
   - Stores in ChromaDB

3. Query System (query_rag_system.py)
   - Accepts user questions
   - Retrieves top 5 relevant chunks
   - Generates answers with citations

USAGE FLOW:
-----------
Step 1: Ingest PDFs
   python scripts/fast_ingest.py

Step 2: Query the system
   python scripts/query_rag_system.py interactive

FEATURES:
---------
✓ 279 free psychological/medical textbooks
✓ Semantic search across all documents
✓ Answer generation with citations
✓ Multi-country clinical standards
✓ Safety layer for crisis detection
✓ Hinglish support (Hindi + English)

ENVIRONMENT SETUP:
------------------
Required: GOOGLE_API_KEY
   Get from: https://makersuite.google.com/app/apikey
   Set with: $env:GOOGLE_API_KEY = "sk-..."

TROUBLESHOOTING:
----------------
Issue: "Vector database not populated"
Fix: Run: python scripts/fast_ingest.py

Issue: "GOOGLE_API_KEY not found"
Fix: $env:GOOGLE_API_KEY = "your-key"

Issue: Package conflicts
Fix: Use Python 3.13 from Microsoft Store
"@ -ForegroundColor White
        Write-Host "`n"
    }
    
    default {
        Write-Host "`n❌ Invalid choice`n" -ForegroundColor Red
    }
}
