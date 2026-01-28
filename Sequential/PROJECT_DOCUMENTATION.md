# Research Assistant - Complete Documentation

## 📋 Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Core Features](#core-features)
4. [Agent Pipeline](#agent-pipeline)
5. [Supported File Formats](#supported-file-formats)
6. [API Endpoints](#api-endpoints)
7. [Technical Stack](#technical-stack)
8. [Installation & Setup](#installation--setup)

---

## 🎯 Overview

**Research Assistant** is an advanced multi-agent AI system built with **Google ADK (Agent Development Kit)** using the **SequentialAgent Pattern**. It processes documents of any format and provides comprehensive research analysis through a 5-agent pipeline.

### Key Highlights
- **Framework**: Google ADK with Sequential Agent Pattern
- **LLM**: Google Gemini (Claude Sonnet 4.5)
- **Architecture**: 5 specialized agents working in sequence
- **File Support**: 20+ document formats (PDF, Word, Excel, Code, etc.)
- **Analysis Modes**: Research Assistant, Literature Review, Competitive Analysis
- **Location Tracking**: Precise citation with `[P#:L#-#]` markers
- **Web Integration**: Google Custom Search + DuckDuckGo fallback
- **🆕 Code Fix Generation**: Automatic generation of copy-paste ready fixes for code, grammar, security issues, and more

---

## 🏗️ System Architecture

### Sequential Pipeline Flow

```mermaid
User Request → IntentDetectorAgent → DataProcessorAgent → AnalyzerAgent → ExtractorAgent → ReportGeneratorAgent → Final Report
```

### Agent Communication
- Each agent outputs data that becomes input for the next agent
- Session management via `InMemorySessionService`
- Event-driven architecture with real-time progress tracking

---

## ✨ Core Features

### 1. **Universal File Support**
Supports **ANY** document type:

**Documents**: PDF, Word (.docx), Excel (.xlsx), PowerPoint (.pptx)

**Text Files**: TXT, MD, RST, LOG, INI, CFG, CONF

**Data Files**: CSV, JSON, XML, HTML, HTM

**Code Files**: Python, JavaScript, TypeScript, Java, C++, C, C#, Go, Ruby, PHP, Swift, Kotlin, Rust, SQL, Shell, Batch, PowerShell, YAML, TOML

**Total**: 20+ formats automatically detected and parsed

### 2. **Three Analysis Modes**

#### Mode 1: Research Assistant
- Answer specific questions about documents
- Extract relevant information with citations
- Provide detailed explanations in layman terms

#### Mode 2: Literature Review
- Categorize and analyze themes
- Synthesize information across documents
- Identify gaps and contrasting viewpoints

#### Mode 3: Competitive Analysis
- Compare options, products, or approaches
- Generate markdown comparison tables
- Provide scoring and recommendations

### 3. **Auto-Comprehensive Analysis**
Triggered with `[AUTO-COMPREHENSIVE-ANALYSIS]`:
- Automatically performs all 3 analysis modes
- Generates: Summary → Literature Review → Competitive Analysis → Key Takeaways
- Web search automatically enabled for enhanced context

### 4. **Location Tracking System**
- Every paragraph numbered with `[P#:L#-#]` format
- Precise citations for all findings
- Format: `[P3:L45-52]` = Paragraph 3, Lines 45-52

### 5. **Web Search Integration**
- **Primary**: Google Custom Search API
- **Fallback**: DuckDuckGo (free, no API key needed)
- Enhances research with external context
- Up to 5 search results per query

### 6. **Layman Explanations**
- All technical terms explained simply
- Uses analogies and examples
- Avoids jargon unless necessary
- Clear, actionable insights

---

## 🤖 Agent Pipeline (Detailed)

### Agent 1: **IntentDetectorAgent**

**Purpose**: Analyze user query and determine the type of analysis needed

**Processing Steps**:
1. Analyzes the research question
2. Detects if it's a specific question, review request, or comparison
3. Determines required analysis mode

**Output**:
```json
{
  "analysis_mode": "research|review|comparison",
  "detected_intent": "user_intent_description",
  "suggested_approach": "analysis_strategy"
}
```

**Example**:
- Input: "What are the main security risks?"
- Output: `{"analysis_mode": "research", "detected_intent": "security_analysis"}`

---

### Agent 2: **DataProcessorAgent**

**Purpose**: Parse and index document with location markers

**Processing Steps**:
1. Receives raw document text
2. Splits into paragraphs
3. Adds location markers `[P#:L#-#]` to each paragraph
4. Counts total paragraphs and lines
5. Creates searchable index

**Output**:
```json
{
  "indexed_document": "document_with_location_markers",
  "paragraph_count": 150,
  "line_count": 3000,
  "document_structure": "metadata"
}
```

**Location Marker Format**:
```text
[P1:L1-15] First paragraph content...
[P2:L16-30] Second paragraph content...
[P3:L31-45] Third paragraph content...
```

**Key Functions**:
- Preserves original text integrity
- Enables precise citation
- Maintains document structure

---

### Agent 3: **AnalyzerAgent**

**Purpose**: Perform the actual research, review, or comparison analysis

**Processing Steps**:

#### For Research Mode:
1. Search indexed document for relevant information
2. Extract key facts related to the question
3. Identify relationships and connections
4. Prepare findings with location references

#### For Literature Review Mode:
1. Identify all major themes and topics
2. Categorize information into logical groups
3. Analyze depth and quality of each topic
4. Find connections between different sections
5. Identify gaps or missing information

#### For Competitive Analysis Mode:
1. Identify all entities/options mentioned
2. List features and characteristics of each
3. Score each option on relevant criteria
4. Prepare comparison data for table generation

**Output**:
```json
{
  "analysis_type": "research|review|comparison",
  "findings": [
    {
      "topic": "Security Risks",
      "location": "[P5:L89-103]",
      "content": "extracted_text",
      "significance": "high"
    }
  ],
  "categories": ["theme1", "theme2"],
  "comparisons": [
    {"entity": "Option A", "scores": {...}}
  ]
}
```

**Key Functions**:
- Context-aware analysis
- Multi-dimensional scoring
- Relationship mapping
- Gap identification

---

### Agent 4: **ExtractorAgent**

**Purpose**: Extract citations, scores, structure analysis results, and **generate copy-paste ready fixes**

**Processing Steps**:
1. Receives analysis findings from AnalyzerAgent
2. Extracts exact quotes with location markers
3. Assigns severity/importance ratings
4. Calculates scores for competitive analysis
5. **🆕 Generates actual code/text fixes for identified issues**
6. Structures data for report generation

**Output**:
```json
{
  "citations": [
    {
      "location": "[P5:L89-103]",
      "quote": "exact_text",
      "context": "surrounding_info",
      "severity": "High|Medium|Low",
      "score": 8.5
    }
  ],
  "scores": {
    "Option A": {"quality": 9, "value": 7},
    "Option B": {"quality": 7, "value": 9}
  },
  "fixes": [
    {
      "location": "[P5:L89-91]",
      "severity": "High",
      "issue_type": "Security",
      "problem": "SQL Injection vulnerability",
      "current_code": "query = f\"SELECT * FROM users WHERE id={user_id}\"",
      "fixed_code": "query = \"SELECT * FROM users WHERE id=?\"\ncursor.execute(query, (user_id,))",
      "explanation": "Parameterized queries prevent SQL injection"
    }
  ],
  "recommendations": ["actionable_insights"]
}
```

**Severity Ratings**:
- **High**: Critical issues or key findings
- **Medium**: Important but not critical
- **Low**: Minor observations

**🆕 Fix Generation Types**:
- **Security Issues**: SQL injection, XSS, authentication flaws
- **Code Bugs**: Logic errors, null pointer exceptions, race conditions
- **Performance**: Inefficient algorithms, memory leaks, unnecessary loops
- **Grammar**: Spelling, punctuation, subject-verb agreement
- **Code Style**: Naming conventions, formatting, best practices

**Key Functions**:
- Citation extraction
- Score calculation
- Data structuring
- Recommendation generation

---

### Agent 5: **ReportGeneratorAgent**

**Purpose**: Generate final formatted report in markdown with **copy-paste ready fixes**

**Processing Steps**:

#### For ALL Modes:
1. **🆕 Generate fixes section** with before/after code/text comparisons
2. Include syntax-highlighted code blocks for easy copying
3. Provide detailed explanations for each fix
4. Rate severity (High/Medium/Low)
5. Add location markers for precise reference

#### For Research Assistant Mode:
1. Create clear answer with headings
2. Include all relevant citations
3. Add severity ratings for issues
4. Provide actionable recommendations
5. **Include copy-paste ready fixes** when issues are found
6. Format in easy-to-read markdown

#### For Literature Review Mode:
1. Generate summary section
2. Create categorized analysis
3. Add synthesis of themes
4. Identify gaps and opportunities
5. **Include fixes for any methodological issues**
6. Format with bullet points and headings

#### For Competitive Analysis Mode:
1. Create comparison markdown table
2. Add feature-by-feature breakdown
3. Include scores and ratings
4. Provide winner/recommendation
5. Add pros/cons for each option

**Output Format**:

```markdown
# 📝 SUMMARY
Clear overview of the analysis...

# 🔍 DETAILED FINDINGS

## Finding 1 - [Severity: High]
**Location**: [P5:L89-103]
**Current Text**: "exact quote from document"
**Issue**: Description of the problem
**Recommendation**: How to fix it

## Finding 2 - [Severity: Medium]
...

# 📊 COMPARISON TABLE

| Feature | Option A | Option B | Option C |
|---------|----------|----------|----------|
| Quality | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Price | $$$$ | $$ | $$$ |
| Score | 8/10 | 6/10 | 9/10 |

# 💡 KEY TAKEAWAYS
1. Actionable insight #1
2. Actionable insight #2
3. Actionable insight #3
```

**Key Functions**:
- Markdown formatting
- Table generation
- Citation formatting
- Layman explanations
- Structured output

---

## 📁 Supported File Formats

### Documents (3)
- **PDF** (.pdf) - Via PyPDF2
- **Word** (.docx, .doc) - Via python-docx
- **Excel** (.xlsx, .xls) - Via openpyxl

### Text Files (8)
- **Plain Text** (.txt, .md, .rst)
- **Logs** (.log)
- **Config** (.ini, .cfg, .conf)

### Data Files (5)
- **CSV** (.csv) - Via csv module
- **JSON** (.json) - Native parsing
- **XML** (.xml) - Via BeautifulSoup
- **HTML** (.html, .htm) - Via BeautifulSoup

### Code Files (18)
- **Python** (.py)
- **JavaScript** (.js, .ts)
- **Java** (.java)
- **C/C++** (.c, .cpp, .h)
- **C#** (.cs)
- **Go** (.go)
- **Ruby** (.rb)
- **PHP** (.php)
- **Swift** (.swift)
- **Kotlin** (.kt)
- **Rust** (.rs)
- **SQL** (.sql)
- **Shell** (.sh, .bat, .ps1)
- **Config** (.yaml, .yml, .toml)

**Total**: 20+ formats with automatic detection

---

## 🌐 API Endpoints

### 1. **POST /api/upload**
Upload and parse any document

**Request**:
```python
file: UploadFile
```

**Response**:
```json
{
  "success": true,
  "text": "extracted_text",
  "pages": 10,
  "file_type": "PDF"
}
```

---

### 2. **POST /api/research**
Standard research analysis

**Request**:
```json
{
  "question": "What are the security risks?",
  "document": "document_text",
  "enable_web_search": false
}
```

**Response**:
```json
{
  "success": true,
  "steps": [
    {"agent": "IntentDetectorAgent", "status": "success"},
    {"agent": "DataProcessorAgent", "status": "success"},
    {"agent": "AnalyzerAgent", "status": "success"},
    {"agent": "ExtractorAgent", "status": "success"},
    {"agent": "ReportGeneratorAgent", "status": "success"}
  ],
  "final_output": {
    "status": "success",
    "answer": "formatted_markdown_report",
    "citations": []
  }
}
```

---

### 3. **POST /api/research/enhanced**
Enhanced research with auto-comprehensive analysis

**Request**:
```json
{
  "question": "[AUTO-COMPREHENSIVE-ANALYSIS]",
  "document": "document_text",
  "enable_web_search": true
}
```

**Response**: Same as /api/research but with web-enhanced context

---

### 4. **POST /api/search**
Web search integration

**Request**:
```json
{
  "query": "latest AI trends",
  "num_results": 5
}
```

**Response**:
```json
{
  "success": true,
  "results": [
    {"title": "...", "url": "...", "snippet": "..."}
  ],
  "query": "latest AI trends"
}
```

---

### 5. **POST /api/fetch-url**
Fetch content from any URL

**Request**:
```json
{
  "url": "https://example.com"
}
```

**Response**:
```json
{
  "success": true,
  "text": "extracted_content",
  "title": "Page Title"
}
```

---

### 6. **GET /api/health**
Health check

**Response**:
```json
{
  "status": "healthy",
  "service": "Universal Research Assistant",
  "framework": "Google ADK",
  "pattern": "SequentialAgent",
  "api_key_configured": true,
  "agents": ["IntentDetectorAgent", "DataProcessorAgent", "AnalyzerAgent", "ExtractorAgent", "ReportGeneratorAgent"],
  "modes": ["Research Assistant", "Literature Review", "Competitive Analysis"]
}
```

---

## 🛠️ Technical Stack

### Backend
- **FastAPI** - REST API framework
- **Google ADK** - Agent Development Kit
- **Google Gemini** - LLM (Claude Sonnet 4.5)
- **aiohttp** - Async HTTP client
- **BeautifulSoup4** - HTML parsing
- **PyPDF2** - PDF parsing
- **python-docx** - Word document parsing
- **openpyxl** - Excel parsing

### Frontend
- **HTML5/CSS3** - User interface
- **JavaScript** - Client-side logic
- **Markdown** - Report formatting

### Infrastructure
- **Uvicorn** - ASGI server
- **InMemorySessionService** - Session management
- **Python 3.8+** - Runtime

---

## 🚀 Installation & Setup

### 1. **Prerequisites**
```bash
Python 3.8 or higher
```

### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Configure Environment**
Create `.env` file:
```env
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_SEARCH_API_KEY=your_search_api_key  # Optional
GOOGLE_SEARCH_CX=your_search_cx  # Optional
```

Get API keys:
- Gemini API: https://aistudio.google.com/app/apikey
- Google Search: https://developers.google.com/custom-search

### 4. **Run Server**
```bash
python main.py
```

### 5. **Access Application**
Open browser: http://localhost:8000

---

## 📊 Performance

- **File Processing**: 1-3 seconds
- **Document Indexing**: 2-5 seconds
- **Analysis Pipeline**: 10-20 seconds
- **Total Processing**: 15-30 seconds (average)

---

## 🔒 Security & Privacy

- **No Data Storage**: Sessions are in-memory only
- **API Key Protection**: Environment variables
- **SSL Certificate Handling**: Configured for enterprise environments
- **Content Filtering**: Microsoft content policies enforced

---

## 🎯 Use Cases

1. **Academic Research** - Analyze research papers, extract citations
2. **Document Review** - Review contracts, policies, technical docs
3. **Competitive Analysis** - Compare products, services, solutions
4. **Code Analysis** - Review source code, identify issues
5. **Literature Review** - Synthesize multiple sources
6. **Business Intelligence** - Analyze reports, extract insights

---

## 📝 License

Built with Google ADK - Agent Development Kit
Model: Claude Sonnet 4.5 via Google Gemini API

---

## 🤝 Support

For issues or questions, check the logs in the console output. All agent steps are tracked with timestamps and status updates.
