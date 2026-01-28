# 🚀 Quick Start Guide

This guide will get you up and running in **5 minutes**!

---

## ⚡ Super Quick Setup (Automated)

### Windows Users

1. Open Command Prompt or PowerShell
2. Navigate to the project folder:
   ```cmd
   cd path\to\Sequential
   ```
3. Run the setup script:
   ```cmd
   setup.bat
   ```
4. Edit `.env` file and add your Google API key
5. Run the application:
   ```cmd
   python main.py
   ```

### macOS/Linux Users

1. Open Terminal
2. Navigate to the project folder:
   ```bash
   cd path/to/Sequential
   ```
3. Make setup script executable and run:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
4. Edit `.env` file and add your Google API key
5. Run the application:
   ```bash
   python main.py
   ```

---

## 📝 Manual Setup (Step-by-Step)

### 1. Install Python

- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **macOS**: `brew install python3` or download from python.org
- **Linux**: `sudo apt-get install python3 python3-pip`

Verify installation:
```bash
python --version  # or python3 --version
```

### 2. Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Google API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the generated key

### 5. Configure Environment

Create `.env` file:

**Windows:**
```cmd
type nul > .env
notepad .env
```

**macOS/Linux:**
```bash
touch .env
nano .env
```

Add your API key:
```env
GOOGLE_API_KEY=your_actual_api_key_here
```

Save and close.

### 6. Run the Application

```bash
python main.py
```

### 7. Open in Browser

Navigate to: **http://localhost:8000**

---

## 🎯 First Analysis

1. **Upload a file** or **paste a URL**
2. Leave the question blank for automatic comprehensive analysis
3. Click **"Analyze"**
4. Watch the 5-agent pipeline work in real-time!

### Example Inputs

**URL Example:**
```
https://en.wikipedia.org/wiki/Artificial_intelligence
```

**Question Examples:**
- "What are the main concepts?" (Research mode)
- "Provide a literature review" (Review mode)  
- "Compare the different approaches" (Competitive mode)
- Leave blank for auto-comprehensive analysis

---

## 🛠️ Common Commands

### Activate Virtual Environment

**Windows:**
```cmd
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### Deactivate Virtual Environment

```bash
deactivate
```

### Update Dependencies

```bash
pip install -r requirements.txt --upgrade
```

### Check Installed Packages

```bash
pip list
```

---

## ❓ Quick Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### "API key not configured" warning
Edit `.env` file and add your `GOOGLE_API_KEY`

### Port 8000 already in use
Kill the process:
- **Windows**: `netstat -ano | findstr :8000`, then `taskkill /PID <PID> /F`
- **macOS/Linux**: `lsof -ti:8000 | xargs kill -9`

### Can't activate virtual environment (Windows)
Run PowerShell as Administrator:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API docs at [http://localhost:8000/docs](http://localhost:8000/docs)
- Try different file formats and analysis modes
- Check out [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) for advanced features

---

## 🎓 Learn More

- [Google ADK Documentation](https://ai.google.dev/adk)
- [Sequential Agent Pattern](https://ai.google.dev/adk/docs/agents/sequential)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)

---

**Need Help?** Check the [Troubleshooting section](README.md#-troubleshooting) in README.md

**Ready to go?** Run `python main.py` and open [http://localhost:8000](http://localhost:8000)! 🚀
