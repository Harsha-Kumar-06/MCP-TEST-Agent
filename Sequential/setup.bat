@echo off
REM ============================================
REM AI Research Assistant - Quick Setup Script (Windows)
REM ============================================

echo ============================================
echo 🚀 AI Research Assistant - Quick Setup
echo ============================================
echo.

REM Check Python installation
echo 📋 Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.8 or higher.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Found Python %PYTHON_VERSION%
echo.

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)
echo ✅ Virtual environment created
echo.

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated
echo.

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip --quiet
echo ✅ pip upgraded
echo.

REM Install dependencies
echo 📥 Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed
echo.

REM Check for .env file
echo 🔍 Checking for .env file...
if not exist .env (
    echo 📝 Creating .env file...
    (
        echo # Google API Key - Get yours at: https://aistudio.google.com/app/apikey
        echo GOOGLE_API_KEY=your_google_api_key_here
        echo.
        echo # Optional: Google Custom Search ^(DuckDuckGo is used by default^)
        echo # GOOGLE_CSE_ID=your_custom_search_engine_id
        echo # GOOGLE_CSE_API_KEY=your_custom_search_api_key
    ) > .env
    echo ✅ .env file created
    echo.
    echo ⚠️  IMPORTANT: Edit .env file and add your Google API Key!
    echo    Get your key from: https://aistudio.google.com/app/apikey
) else (
    echo ✅ .env file already exists
)
echo.

REM Setup complete
echo ============================================
echo ✅ Setup Complete!
echo ============================================
echo.
echo 📝 Next Steps:
echo    1. Edit .env file and add your GOOGLE_API_KEY
echo    2. Run: python main.py
echo    3. Open: http://localhost:8000
echo.
echo 💡 Need help? Check README.md for detailed instructions
echo.
pause
