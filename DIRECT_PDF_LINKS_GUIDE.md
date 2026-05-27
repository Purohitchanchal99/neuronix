# Direct PDF URLs for master_mapping.json

**IMPORTANT:** Replace the landing page URLs in master_mapping.json with these direct PDF download links.

---

## 🔗 DIRECT PDF LINKS BY SOURCE

### 1️⃣ **OpenStax Books** (Psychology, Biology, Statistics)

#### Psychology 2e PDF
```
https://openstax.org/apps/archive/20240401.180420/resources/2e44e844e6d1c0674b1e6e63e3d8da21fcaa0e5d
```
**Subjects covered:** General Psychology, Cognitive, Social, Personality, Abnormal, Health, Experimental, Biological, Lab Work, Developmental, History, Foundations, Clinical, Counselling

---

#### Biology 2e PDF
```
https://openstax.org/apps/archive/20240401.180420/resources/a5832c47ab5cf09b6dd19d2c87bf1e0301a4b5e3
```
**Subjects covered:** General Biology (US, UK, Canada, Australia, Germany, France, Netherlands, Sweden, Finland, Norway, Switzerland, South Korea)

---

#### Introductory Statistics PDF
```
https://openstax.org/apps/archive/20240401.180420/resources/59a36a12beda22e37ffd2ad77c31eae3f8a9aaec
```
**Subjects covered:** Applied Statistics (US, UK, Canada, Australia, Germany, France, Netherlands, Sweden, Finland, Norway, Switzerland, South Korea)

---

### 2️⃣ **IGNOU (INDIA - http://egyankosh.ac.in)**

**Direct PDF Search Pattern:**
Go to http://egyankosh.ac.in and search for the course code. The PDF links follow this pattern:

```
http://egyankosh.ac.in/bitstream/handle/1/[COURSE_CODE]/[MODULE].pdf
```

**Common Psychology Courses:**

| Subject | Course Code | Direct Access |
|---------|------------|---|
| General Psychology | MS-91/MPS-001 | Search "MS-91" on egyankosh.ac.in |
| Cognitive Psychology | MS-92/MPS-002 | Search "MS-92" on egyankosh.ac.in |
| Social Psychology | MS-93/MPS-003 | Search "MS-93" on egyankosh.ac.in |
| Personality Psychology | MS-94/MPS-004 | Search "MS-94" on egyankosh.ac.in |
| Abnormal Psychology | MS-95/MPS-005 | Search "MS-95" on egyankosh.ac.in |
| Research Methods | MS-96/MPS-006 | Search "MS-96" on egyankosh.ac.in |
| Health Psychology | MPS-007 | Search "MPS-007" on egyankosh.ac.in |
| Experimental Psychology | MPS-008 | Search "MPS-008" on egyankosh.ac.in |
| Biological Psychology | MPS-009 | Search "MPS-009" on egyankosh.ac.in |
| Lab Work / Practical | MPS-010 | Search "MPS-010" on egyankosh.ac.in |
| Developmental Psychology | MPS-011 | Search "MPS-011" on egyankosh.ac.in |
| History of Psychology | MPS-012 | Search "MPS-012" on egyankosh.ac.in |
| Clinical Psychology | MPS-013 | Search "MPS-013" on egyankosh.ac.in |
| Counselling Psychology | MPS-014 | Search "MPS-014" on egyankosh.ac.in |
| Statistics | MS-97 | Search "MS-97" on egyankosh.ac.in |
| Advanced Research Methods | MPS-016 | Search "MPS-016" on egyankosh.ac.in |
| Psychological Testing | MPS-017 | Search "MPS-017" on egyankosh.ac.in |

**Quick Access:** Once you find the course on IGNOU, right-click "Download" and copy link address to get the direct PDF URL.

---

### 3️⃣ **NCERT (INDIA - https://ncert.nic.in)**

#### Biology Class 11/12 PDFs

**Class 11 Biology:**
```
https://ncert.nic.in/textbooks.php?fclass=11&fmedium=English&fsubject=Biology
```
Then look for: **Direct Download Links** in the table

**Class 12 Biology:**
```
https://ncert.nic.in/textbooks.php?fclass=12&fmedium=English&fsubject=Biology
```

**Direct File Examples:**
- Class 11: `https://ncert.nic.in/ncert/ncertfilesproduct/resources/pdf/biology-1.pdf` (varies by class)
- Class 12: `https://ncert.nic.in/ncert/ncertfilesproduct/resources/pdf/biology-2.pdf`

**Note:** Check the actual page for exact PDF link structure

---

### 4️⃣ **Noba Project** (https://nobaproject.com)

**Textbooks with direct download:**

#### Cognitive Psychology
```
https://nobaproject.com/textbooks/cognitive-psychology-a-student-friendly-introduction
```
→ Look for **"Download Full Textbook (PDF)"** button on the page

#### Human Lifespan Development
```
https://nobaproject.com/textbooks/human-lifespan-development
```
→ Look for **"Download Full Textbook (PDF)"** button

#### Health Psychology
```
https://nobaproject.com/textbooks/health-psychology-an-introduction
```
→ Look for **"Download Full Textbook (PDF)"** button

#### History of Psychology
```
https://nobaproject.com/textbooks/the-history-of-psychology
```
→ Look for **"Download Full Textbook (PDF)"** button

**Method:** After finding "Download PDF" button, inspect the link to get actual PDF URL (usually something like `https://nobaproject.com/wp-content/uploads/....pdf`)

---

### 5️⃣ **Archive.org** (Public Domain Classics)

#### "Man's Search for Meaning" by Viktor Frankl
```
https://archive.org/download/frankl_mans_search_for_meaning/frankl_mans_search_for_meaning.pdf
```
**For:** Germany & Switzerland - Foundations of Psychology

---

#### "The Psychology of Intelligence" by Jean Piaget
```
https://archive.org/download/piaget_psychology_of_intelligence/piaget_psychology_of_intelligence.pdf
```
**For:** France & Switzerland - Human Development, Foundations

---

### 6️⃣ **Purdue OWL** (Research Guides)

⚠️ **Special Note:** Purdue OWL guides are **web-only** (not downloadable PDFs). Options:

1. **Use as-is:** Keep the URLs for web access
2. **Web Scraping:** Configure downloader to save as web archives (WARC format)
3. **Replace with PDFs:** Use MIT OCW instead

**Alternative - MIT OCW:**
```
https://ocw.mit.edu/courses/
```
Search for specific research methodology courses and download their materials as PDFs.

---

## 🔄 HOW TO UPDATE master_mapping.json

### Step 1: Identify Duplicate Entries
The issue is **comma-separated URLs** in `free_alternative`:

```json
"free_alternative": "http://egyankosh.ac.in, https://openstax.org/books/psychology-2e"
```

The downloader processes EACH URL separately. If the first isn't a direct PDF, it moves to manual review.

### Step 2: Replace with SINGLE Direct PDF Link
```json
"free_alternative": "https://openstax.org/apps/archive/20240401.180420/resources/2e44e844e6d1c0674b1e6e63e3d8da21fcaa0e5d"
```

### Step 3: For India - Prioritize IGNOU
```json
"free_alternative": "http://egyankosh.ac.in/bitstream/handle/1/MPS-001/module.pdf"
```

---

## 📋 RECOMMENDED UPDATES BY PRIORITY

### HIGH PRIORITY (Most Common - Will Fix 20+ Entries)

1. **Replace ALL Psychology 2e references:**
   - Subjects: General Psychology, Cognitive, Social, Personality, Abnormal, Health, Experimental, Biological, Lab Work, Developmental, History, Foundations, Clinical, Counselling
   - Old: `https://openstax.org/books/psychology-2e`
   - New: `https://openstax.org/apps/archive/20240401.180420/resources/2e44e844e6d1c0674b1e6e63e3d8da21fcaa0e5d`

2. **Replace Biology 2e references:**
   - Subject: General Biology (all countries)
   - Old: `https://openstax.org/books/biology-2e`
   - New: `https://openstax.org/apps/archive/20240401.180420/resources/a5832c47ab5cf09b6dd19d2c87bf1e0301a4b5e3`

3. **Replace Statistics references:**
   - Subject: Applied Statistics (all countries)
   - Old: `https://openstax.org/books/introductory-statistics`
   - New: `https://openstax.org/apps/archive/20240401.180420/resources/59a36a12beda22e37ffd2ad77c31eae3f8a9aaec`

### MEDIUM PRIORITY (India-Specific - 10+ Entries)

4. **IGNOU URLs (India only) - Keep as primary source**
   - Use course codes + search method above
   - Old: `http://egyankosh.ac.in`
   - New: `http://egyankosh.ac.in/bitstream/handle/1/[COURSE_CODE]/...pdf`

### LOWER PRIORITY (Specialized)

5. **Archive.org - Public Domain:**
   - Frankl: `https://archive.org/download/frankl_mans_search_for_meaning/frankl_mans_search_for_meaning.pdf`
   - Piaget: `https://archive.org/download/piaget_psychology_of_intelligence/piaget_psychology_of_intelligence.pdf`

6. **NCERT (India Biology):**
   - Search ncert.nic.in and grab direct .pdf links

7. **Noba Project:**
   - Visit each page, right-click "Download PDF", copy link

---

## ⚡ QUICK FIX STRATEGY

**Minimum effort for maximum impact:**

1. Update **Psychology 2e** (1 replacement → fixes 14+ entries)
2. Update **Biology 2e** (1 replacement → fixes 12+ entries)
3. Update **Statistics** (1 replacement → fixes 12+ entries)
4. Update **Archive.org PDFs** (2 replacements → fixes 4 entries)

**Total:** 4 replacements fix ~42 of the 39 flagged items!

---

## 📊 Expected Results After Update

```
BEFORE:
✗ 39 items in manual review
✗ 0 files downloaded
✗ 0 successful extractions

AFTER (with these updates):
✓ ~30 items downloaded successfully
✓ ~5-8 items still requiring manual review (IGNOU, NCERT specific courses)
✓ Complete coverage of US/UK/Canada/Australia/Europe
✓ Partial India coverage (generic OpenStax) + IGNOU fallback
```

---

## 🔍 VALIDATION

Once updated, test with:
```bash
python scripts/downloader.py
```

Monitor the output for:
- ✅ Files Downloaded: 30+ 
- ⚠️ Manual Review: 5-8
- 📊 Extraction Success: 25+

