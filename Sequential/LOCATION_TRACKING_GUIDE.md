# 📍 Location Tracking Feature - Testing Guide

## 🎯 What's New?

The research assistant now provides **precise location references** for all findings, issues, and recommendations. When analyzing documents, it will cite exact paragraph and line numbers.

## 🔍 How It Works

### Location Format: `[P#:L#-#]`
- **P#** = Paragraph number
- **L#-#** = Line range (start-end)
- Example: `[P3:L15-20]` means Paragraph 3, Lines 15-20

## 📮 Testing in Postman

### Step 1: Start the Server
```bash
python main.py
```
Server will run at: `http://localhost:8000`

### Step 2: Upload a Document
**Endpoint**: `POST http://localhost:8000/api/upload`

**Body**: form-data
- Key: `file`
- Value: [Select your PDF/Word/Text file]

**Response**:
```json
{
  "success": true,
  "text": "Your extracted document text...",
  "pages": 5,
  "file_type": "PDF"
}
```

### Step 3: Research with Location Tracking
**Endpoint**: `POST http://localhost:8000/api/research`

**Headers**:
- Content-Type: `application/json`

**Body**:
```json
{
  "question": "What improvements are needed in this document?",
  "document": "<paste the extracted text from step 2>",
  "enable_web_search": false
}
```

**Expected Response** (with location references):
```json
{
  "success": true,
  "final_output": {
    "status": "success",
    "answer": "## KEY FINDINGS:\n\n1. **Outdated Statistics** - Found at [P2:L10-15]: \"The 2020 data shows...\"\n   - Issue: Contains outdated information\n   - Recommendation: Update with 2025 statistics\n   - Severity: High\n\n2. **Grammar Error** - Found at [P5:L23-25]: \"The team are working\"\n   - Issue: Subject-verb disagreement\n   - Recommendation: Change to \"The team is working\"\n   - Severity: Low\n\n..."
  }
}
```

## 📊 Example Test Queries

### 1. Finding Issues
```json
{
  "question": "What sections need improvement and exactly where?",
  "document": "...",
  "enable_web_search": false
}
```

### 2. Literature Review
```json
{
  "question": "Compare the different methodologies discussed and cite their locations",
  "document": "...",
  "enable_web_search": false
}
```

### 3. Competitive Analysis
```json
{
  "question": "Compare Product A vs Product B with specific references to where each feature is mentioned",
  "document": "...",
  "enable_web_search": false
}
```

## 🎨 Sample Document for Testing

Create a text file with this content:

```
Introduction to AI Healthcare
==============================

Artificial intelligence is transforming healthcare in 2020. The market size was $50M.

Benefits of AI
==============

AI improves diagnostic accuracy by 30%. Studies show significant improvements.
The team are working on new algorithms for patient care.

Challenges
==========

Data privacy remains a concern. Healthcare providers need better training.
Implementation costs is high for small clinics.

Conclusion
==========

AI has great potential but needs careful implementation.
```

Save this as `test_document.txt` and upload it to test the location tracking feature.

## ✅ Expected Behavior

The AI will now return responses like:

```
## ANALYSIS COMPLETE

KEY FINDINGS WITH LOCATIONS:
1. Outdated Data - Location: [P1:L3-4]
   Current Text: "in 2020. The market size was $50M"
   Recommendation: Update with current 2025 data
   Severity: High

2. Grammar Error - Location: [P2:L2-3]
   Current Text: "The team are working"
   Recommendation: Change to "The team is working"
   Severity: Medium

3. Grammar Error - Location: [P3:L2-3]
   Current Text: "Implementation costs is high"
   Recommendation: Change to "Implementation costs are high"
   Severity: Medium
```

## 🚀 Quick Test Commands

### Option 1: Using cURL
```bash
# Upload file
curl -X POST http://localhost:8000/api/upload -F "file=@test_document.txt"

# Research (copy text from upload response)
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"question": "What needs to be fixed?", "document": "YOUR_TEXT_HERE"}'
```

### Option 2: Using Postman Collection
Import these endpoints:
1. `POST /api/upload` - Upload document
2. `POST /api/research` - Analyze with locations
3. `POST /api/fetch-url` - Fetch from URL
4. `GET /api/health` - Health check

## 🎯 Benefits

✅ **Precise Citations**: Know exactly where each finding is located  
✅ **Actionable Feedback**: Clear instructions on what to fix and where  
✅ **Easy Navigation**: Jump directly to relevant sections in your document  
✅ **Better Reviews**: Perfect for document review and quality assurance  
✅ **Audit Trail**: Track all references back to source locations  

## 🔧 Troubleshooting

**Issue**: No location markers in response
- **Solution**: Make sure you're using the `/api/research` endpoint (not the old one)

**Issue**: Location markers show as `[P0:L0-0]`
- **Solution**: Document might be empty or improperly formatted

**Issue**: Locations don't match document
- **Solution**: Ensure you're passing the same text that was uploaded

---

**Ready to test?** Start the server with `python main.py` and try it out! 🚀
