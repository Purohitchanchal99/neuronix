# Failed PDF Retry Guide (Sirf Naazukh PDFs)

## 📋 Failed PDFs Status

2 PDFs failed during ingestion:

| PDF Name | Error | Retries | Status |
|----------|-------|---------|--------|
| Abnormal Psychology_Psychology2e_WEB.pdf | ChromaDB HNSW indexing error | 1 | ❌ Failed |
| Applied Statistics_IntroductoryStatistics-OP.pdf | ChromaDB HNSW indexing error | 1 | ❌ Failed |

## 🔄 How to Retry (Sirf Failed PDFs)

### Option 1: Run Batch File (Easiest)
```bash
retry_failed_pdfs_only.bat
```
Double-click this file to retry ONLY the failed PDFs.

### Option 2: Run Python Script
```bash
python retry_failed_pdfs_only.py
```

### Option 3: From Python Terminal
```python
from scripts.neuronix_ingest import NeuronixIngestion
ingestion = NeuronixIngestion()
ingestion.retry_failed_pdfs()  # Retry ONLY failed PDFs
```

## ✅ What Happens

1. **Loads** failed_files.json (containing 2 PDFs)
2. **Skips** all already-processed PDFs (no duplication)
3. **Retries** only the 2 failed PDFs
4. **Removes** each PDF from failed list once successfully processed
5. **Saves** progress checkpoint after each retry

## 🚨 Chrome DB Error Details

Error: `Error in compaction: Error constructing hnsw segme`

**Cause:** HNSW (Hierarchical Navigable Small World) vector index corruption during chunk storage

**Fix Applied:** 
- Refreshing the vector store
- Re-chunking the PDFs
- Attempting storage again with fresh index

## 📊 Expected Results

**Before Retry:**
- Failed PDFs: 2
- Vector DB status: Partial (some chunks missing)

**After Successful Retry:**
- Failed PDFs: 0
- Both PDFs successfully stored
- ~N/A chunks added to vector DB
- Ready for queries

## 🔄 Resume Capability

If the retry process crashes:
- Progress is saved after EACH PDF
- Next run will resume from where it left off
- Already-recovered PDFs won't be re-processed

## 📁 Related Files

- Failed tracking: `data/checkpoints/failed_files.json`
- Failed PDF copies: `data/failed_pdfs/` (for manual inspection)
- Ingestion logs: `scripts/neuronix_ingest.log`
- Retry logs: Also in `scripts/neuronix_ingest.log`

## 💡 Tips

1. **Run during low-CPU times** (retry process is CPU-intensive)
2. **Check logs** if retry fails: `scripts/neuronix_ingest.log`
3. **Monitor progress** with: `ingestion_monitor_enhanced.py`
4. **After success:** Vector DB will be ready for queries

---

**Last Updated:** {{DATE}}
**Status:** Ready to retry
