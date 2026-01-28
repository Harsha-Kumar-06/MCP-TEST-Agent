# 🧪 Testing Guide

Quick guide to test your AI Research Assistant installation.

---

## ✅ Pre-Flight Checks

### 1. Verify Installation

```bash
# Check Python version
python --version  # Should be 3.8+

# Check if virtual environment is activated
# You should see (venv) in your terminal prompt

# Verify packages are installed
pip list | grep google-adk
pip list | grep fastapi
```

### 2. Verify API Key

```bash
# Windows PowerShell
Get-Content .env | Select-String GOOGLE_API_KEY

# Windows CMD
type .env | findstr GOOGLE_API_KEY

# macOS/Linux
cat .env | grep GOOGLE_API_KEY
```

Make sure the key is not `your_google_api_key_here`.

---

## 🚀 Basic Functionality Tests

### Test 1: Start the Server

```bash
python main.py
```

**Expected Output:**
```
============================================================
🚀 Research Assistant - Google ADK Sequential Pipeline
============================================================

✅ API Key configured successfully
✅ Session service initialized

📍 Open your browser: http://localhost:8000
```

**If you see:** `⚠️ GOOGLE_API_KEY not configured!`
- Edit your `.env` file
- Add your actual API key
- Restart the server

---

### Test 2: Access Web Interface

1. Open browser
2. Navigate to: http://localhost:8000
3. You should see the Research Assistant UI

**Expected:** Clean interface with URL/File upload options

---

### Test 3: Test File Upload (Using Existing Test File)

The project includes a test file. Let's use it:

1. In the web interface, click **"Upload File"** tab
2. Upload: `test_document.txt` from the project folder
3. Leave question blank (for auto analysis)
4. Click **"Analyze"**

**Expected:**
- Progress bar showing 5 agents working
- Each agent completes: IntentDetector → DataProcessor → Analyzer → Extractor → ReportGenerator
- Final formatted report appears

---

### Test 4: Test URL Fetching

1. In the web interface, switch to **"URL Link"** tab
2. Enter: `https://en.wikipedia.org/wiki/Python_(programming_language)`
3. Leave question blank
4. Click **"Analyze"**

**Expected:**
- URL content fetched successfully
- Comprehensive analysis generated
- Report includes sections: Summary, Literature Review, Competitive Analysis

---

### Test 5: API Endpoint Test

Test the API directly using curl or Python:

**Using curl:**

```bash
# Test web search endpoint
curl -X POST http://localhost:8000/api/web-search \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence", "num_results": 3}'
```

**Using Python:**

```python
import requests

# Test URL fetch
response = requests.post(
    "http://localhost:8000/api/fetch-url",
    json={"url": "https://example.com"}
)
print(response.json())
```

---

## 🎯 Feature-Specific Tests

### Test Different File Formats

Try uploading different file types:

- **PDF**: Any PDF document
- **Word**: Any .docx file
- **Excel**: Any .xlsx file
- **Text**: .txt, .md files
- **Code**: .py, .js, .java files

**All should parse successfully**

---

### Test Analysis Modes

#### Research Mode
- **Input**: Upload file + Question: "What are the main points?"
- **Expected**: Detailed answer with citations in `[P#:L#-#]` format

#### Literature Review Mode
- **Input**: Upload file + Question: "Provide a literature review"
- **Expected**: Thematic analysis with categories

#### Competitive Analysis Mode
- **Input**: Upload file + Question: "Compare the options"
- **Expected**: Comparison table with scores

#### Auto-Comprehensive Mode
- **Input**: Upload file + Leave question blank
- **Expected**: All 3 modes combined automatically

---

### Test Web Search Integration

1. Upload a document about a technical topic
2. Enable web search (if available in UI)
3. Ask: "What are recent developments in this field?"
4. **Expected**: Answer includes both document content and web search results

---

## 🐛 Debugging Tests

### Test Error Handling

#### Invalid API Key
1. Edit `.env`: Set `GOOGLE_API_KEY=invalid_key_12345`
2. Restart server
3. Try analysis
4. **Expected**: Graceful error message (not crash)

#### Large File
1. Try uploading a very large file (>50MB)
2. **Expected**: Warning or graceful handling

#### Malformed Request
```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{}'
```
**Expected**: 422 Validation Error (not 500 crash)

---

## 📊 Performance Tests

### Response Time
- **Small document** (<10 pages): Should complete in 10-30 seconds
- **Medium document** (10-50 pages): Should complete in 30-60 seconds
- **Large document** (50+ pages): May take 1-3 minutes

### Concurrent Requests
Open 2-3 browser tabs and run analyses simultaneously.
**Expected**: All complete successfully (may be slower)

---

## ✅ Success Criteria

Your installation is working correctly if:

- [x] Server starts without errors
- [x] Web interface loads at localhost:8000
- [x] File upload works for at least PDF, DOCX, TXT
- [x] URL fetching extracts content successfully
- [x] All 5 agents execute in sequence
- [x] Final report is generated and formatted correctly
- [x] Citations include location markers `[P#:L#-#]`
- [x] Auto-comprehensive analysis includes all 3 modes

---

## 🔧 Troubleshooting Failed Tests

### Server won't start
```bash
# Check if port is in use
netstat -ano | findstr :8000  # Windows
lsof -ti:8000                  # macOS/Linux

# Try different port
# Edit main.py line 1062: port=8001
```

### Imports failing
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Agent pipeline fails
- Check logs in terminal for specific error
- Verify API key is valid and has quota remaining
- Check internet connection (needed for Gemini API)

### Web search not working
- This is optional and uses DuckDuckGo fallback
- Should not prevent other features from working

---

## 📈 Advanced Testing

### Load Testing

Create a simple load test:

```python
import concurrent.futures
import requests

def test_request():
    response = requests.post(
        "http://localhost:8000/api/research",
        json={
            "question": "What is this about?",
            "document": "Test document content here.",
            "enable_web_search": False
        }
    )
    return response.status_code

# Run 5 concurrent requests
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(test_request) for _ in range(5)]
    results = [f.result() for f in futures]
    print(f"Results: {results}")
```

---

## 📝 Test Log

Keep track of your tests:

```
✅ Server startup: PASS
✅ Web interface: PASS
✅ File upload (PDF): PASS
✅ URL fetch: PASS
✅ Agent pipeline: PASS
✅ Auto analysis: PASS
✅ Citations format: PASS
```

---

## 🎓 Next Steps

After all tests pass:

1. Try with your own documents
2. Experiment with different question types
3. Compare the 3 analysis modes
4. Integrate with your workflow

---

**All tests passing?** 🎉 You're ready to use the Research Assistant!

**Some tests failing?** Check the [Troubleshooting section](README.md#-troubleshooting) in README.md
