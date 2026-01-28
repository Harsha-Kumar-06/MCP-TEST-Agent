# 🔬 AI Research Assistant - Multi-Agent Sequential Pipeline

A powerful multi-agent AI research assistant built with **Google ADK (Agent Development Kit)** using the Sequential Agent Pattern. Automatically analyzes documents and provides comprehensive research insights across multiple analysis modes.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Google ADK](https://img.shields.io/badge/Google-ADK-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-teal)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📋 Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [Usage](#-usage)
- [Supported File Formats](#-supported-file-formats)
- [Analysis Modes](#-analysis-modes)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

### 🎯 Core Capabilities
- **5-Agent Sequential Pipeline**: Intent Detection → Data Processing → Analysis → Extraction → Report Generation
- **Universal File Support**: 20+ document formats (PDF, Word, Excel, TXT, Code files, etc.)
- **3 Analysis Modes**: Research Assistant, Literature Review, Competitive Analysis
- **Auto-Comprehensive Analysis**: One-click complete analysis with web search integration
- **Precise Location Tracking**: Citations with `[P#:L#-#]` format for exact source referencing
- **Web Search Integration**: Google Custom Search + DuckDuckGo fallback
- **Real-time Processing**: Live progress tracking with event-driven architecture
- **Code Fix Generation**: Automatic generation of copy-paste ready fixes for code issues

### 🌐 Web Interface Features
- Clean, modern UI with real-time progress visualization
- URL fetching with automatic content extraction
- Drag-and-drop file upload
- Live agent pipeline visualization
- Formatted markdown output with syntax highlighting

---

## 🏗️ System Architecture

### Sequential Agent Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    User Input (URL/File)                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
          ┌─────────────────────────────┐
          │  IntentDetectorAgent        │ ← Detects analysis mode
          │  (Mode: Research/Review/    │
          │   Competitive Analysis)     │
          └──────────────┬──────────────┘
                         │
                         ▼
          ┌─────────────────────────────┐
          │  DataProcessorAgent         │ ← Processes & structures data
          │  (Parse, Clean, Format)     │
          └──────────────┬──────────────┘
                         │
                         ▼
          ┌─────────────────────────────┐
          │  AnalyzerAgent              │ ← Search/Categorize/Compare
          │  (Web Search, Themes,       │
          │   Comparisons)              │
          └──────────────┬──────────────┘
                         │
                         ▼
          ┌─────────────────────────────┐
          │  ExtractorAgent             │ ← Extract citations/synthesis
          │  (Citations, Synthesis,     │
          │   Scores)                   │
          └──────────────┬──────────────┘
                         │
                         ▼
          ┌─────────────────────────────┐
          │  ReportGeneratorAgent       │ ← Final formatted report
          │  (Summary, Tables, Insights)│
          └──────────────┬──────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Final Report │
                  └──────────────┘
```

---

## 🔧 Prerequisites

Before installing, ensure you have:

- **Python 3.8 or higher** installed ([Download Python](https://www.python.org/downloads/))
- **pip** package manager (comes with Python)
- **Google API Key** for Gemini model ([Get API Key](https://aistudio.google.com/app/apikey))
- Internet connection for web search features (optional)

---

## 📥 Installation

### Step 1: Clone or Download the Repository

```bash
# If using Git
git clone <repository-url>
cd drayvn_agents/Sequential

# Or download and extract the ZIP file, then navigate to the Sequential folder
```

### Step 2: Create a Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages:
- Google ADK (Agent Development Kit)
- FastAPI & Uvicorn (Web server)
- Document parsing libraries (PyPDF2, python-docx, openpyxl)
- Web scraping tools (aiohttp, beautifulsoup4)
- And more...

---

## ⚙️ Configuration

### 1. Create Environment File

Create a `.env` file in the project root directory:

```bash
# Windows
type nul > .env

# macOS/Linux
touch .env
```

### 2. Add Your Google API Key

Open the `.env` file in a text editor and add:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

**To get your Google API Key:**
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and paste it in your `.env` file

### 3. Optional: Configure Web Search (Advanced)

For Google Custom Search (optional, DuckDuckGo is used by default):

```env
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_custom_search_engine_id
GOOGLE_CSE_API_KEY=your_custom_search_api_key
```

---

## 🚀 Running the Application

### Start the Server

```bash
python main.py
```

You should see output like:

```
============================================================
🚀 Research Assistant - Google ADK Sequential Pipeline
============================================================

✅ API Key configured successfully
✅ Session service initialized

📍 Open your browser: http://localhost:8000

🤖 Framework: Google ADK (Agent Development Kit)
📋 Pattern: SequentialAgent
⚡ LLM: Google Gemini

🔗 Pipeline Flow:
   1. IntentDetectorAgent → Detect analysis mode
   2. DataProcessorAgent → Process & structure data
   3. AnalyzerAgent → Analyze (search/categorize/compare)
   4. ExtractorAgent → Extract (citations/synthesis/scores)
   5. ReportGeneratorAgent → Generate final report

============================================================

INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Access the Web Interface

Open your browser and navigate to:

```
http://localhost:8000
```

---

## 💡 Usage

### Method 1: Using the Web Interface

1. **Open the application** in your browser
2. **Choose input method**:
   - **URL**: Paste any webpage URL (article, blog, research paper)
   - **File Upload**: Upload a document (PDF, Word, Excel, TXT, etc.)
3. **Optional**: Enter a specific question
4. **Click "Analyze"** - The AI automatically determines the best analysis approach
5. **View results** with real-time progress tracking

### Method 2: Using the API

#### Upload and Analyze a File

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@document.pdf" \
  -F "question=What are the main findings?"
```

#### Fetch and Analyze a URL

```bash
curl -X POST http://localhost:8000/api/fetch-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

#### Perform Research Analysis

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key insights?",
    "document": "Your document text here...",
    "enable_web_search": true
  }'
```

---

## 📄 Supported File Formats

The assistant can process **20+ file formats**:

| Category | Formats |
|----------|---------|
| **Documents** | PDF, DOCX (Word), XLSX (Excel), PPTX (PowerPoint) |
| **Text Files** | TXT, MD (Markdown), RST, LOG, INI, CFG, CONF |
| **Data Files** | CSV, JSON, XML, HTML, HTM |
| **Code Files** | PY, JS, TS, JAVA, CPP, C, CS, GO, RB, PHP, SWIFT, KT, RS, SQL, SH, BAT, PS1, YAML, TOML |

---

## 🎯 Analysis Modes

The system automatically detects the appropriate mode based on your input:

### 🔬 Mode 1: Research Assistant
**Triggered by**: Specific questions about documents
- Answer targeted questions with precise citations
- Extract relevant information with location tracking `[P#:L#-#]`
- Provide detailed explanations in layman terms
- Include web search results when enabled

**Example**: "What are the key findings in this paper?"

### 📚 Mode 2: Literature Review
**Triggered by**: Requests for comprehensive analysis or multiple sources
- Categorize and analyze themes across documents
- Synthesize information from multiple sources
- Identify gaps and contrasting viewpoints
- Generate structured thematic analysis

**Example**: "Provide a literature review of this research area"

### 🏆 Mode 3: Competitive Analysis
**Triggered by**: Comparison requests or market analysis
- Compare products, companies, or approaches
- Generate markdown comparison tables
- Provide scoring and recommendations
- Side-by-side feature comparisons

**Example**: "Compare these three solutions and recommend the best one"

### 🌟 Auto-Comprehensive Analysis
**Triggered by**: `[AUTO-COMPREHENSIVE-ANALYSIS]` or empty question field
- Automatically performs ALL 3 analysis modes
- Generates: Summary → Literature Review → Competitive Analysis → Key Takeaways
- Web search automatically enabled for enhanced context
- Most comprehensive analysis available

---

## 📚 API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve web interface |
| `/api/upload` | POST | Upload and analyze file |
| `/api/research` | POST | Perform research analysis |
| `/api/fetch-url` | POST | Fetch and extract content from URL |
| `/api/web-search` | POST | Perform web search |

---

## 📁 Project Structure

```
Sequential/
├── main.py                          # FastAPI application entry point
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables (create this)
├── README.md                       # This file
│
├── agents/                         # Legacy agent implementations
│   ├── document_processor_agent.py
│   ├── extraction_agent.py
│   ├── search_agent.py
│   └── summary_agent.py
│
├── research_assistant/             # Main multi-agent system
│   ├── agent.py                   # Root SequentialAgent definition
│   └── sub_agents/                # 5-agent pipeline
│       ├── intent_detector.py     # Detects analysis mode
│       ├── data_processor.py      # Processes input data
│       ├── analyzer_agent.py      # Performs analysis
│       ├── extractor_agent.py     # Extracts key information
│       └── report_generator.py    # Generates final report
│
├── models/                         # Data models
│   └── data_models.py
│
├── orchestrator/                   # Pipeline orchestration
│   └── sequential_orchestrator.py
│
├── tools/                          # Utility tools
│   └── web_search.py              # Web search integration
│
└── static/                         # Web interface
    ├── index.html                 # Main UI
    ├── style.css                  # Styling
    └── script.js                  # Frontend logic
```

---

## 🔍 Troubleshooting

### Issue: API Key Error

**Error**: `⚠️ GOOGLE_API_KEY not configured!`

**Solution**:
1. Ensure you created a `.env` file in the project root
2. Add your API key: `GOOGLE_API_KEY=your_actual_key_here`
3. Restart the application

### Issue: Module Not Found

**Error**: `ModuleNotFoundError: No module named 'google.adk'`

**Solution**:
```bash
# Ensure virtual environment is activated
pip install -r requirements.txt --upgrade
```

### Issue: Port Already in Use

**Error**: `OSError: [Errno 48] Address already in use`

**Solution**:
```bash
# Option 1: Kill the process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# macOS/Linux:
lsof -ti:8000 | xargs kill -9

# Option 2: Use a different port
# Edit main.py, line 1062: change port=8000 to port=8001
```

### Issue: SSL Certificate Errors

**Note**: The application disables SSL verification for litellm compatibility. This is expected behavior.

### Issue: File Upload Fails

**Solution**:
- Check file size (recommended < 50MB)
- Ensure file format is supported
- Try converting to PDF or TXT if issues persist

### Issue: Web Search Not Working

**Solution**:
- The system automatically falls back to DuckDuckGo (no API key needed)
- For Google Custom Search, add `GOOGLE_CSE_ID` and `GOOGLE_CSE_API_KEY` to `.env`
- Check internet connection

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **Google ADK**: Agent Development Kit framework
- **Google Gemini**: LLM powering the analysis
- **FastAPI**: High-performance web framework
- **DuckDuckGo**: Free web search fallback

---

## 📞 Support

For questions or issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the API documentation at `http://localhost:8000/docs`
3. Open an issue in the repository

---

## 🎓 Learn More

- [Google ADK Documentation](https://ai.google.dev/adk)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Gemini API](https://ai.google.dev/)

---

**Built with ❤️ using Google ADK and FastAPI**
