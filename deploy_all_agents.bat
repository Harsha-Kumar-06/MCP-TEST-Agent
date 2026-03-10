@echo off
REM ============================================
REM Drayvn Agents - BULK Deployment to Cloud Run
REM ============================================
REM This script deploys ALL agents at once to get permanent demo URLs
REM 
REM Prerequisites:
REM   1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
REM   2. Run: gcloud auth login
REM   3. Set YOUR_PROJECT_ID below
REM ============================================

setlocal enabledelayedexpansion

REM ============================================
REM CONFIGURE THESE VALUES
REM ============================================
set PROJECT_ID=gcp-drayvn-etoc
set REGION=us-central1
set GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
set SERVICE_PREFIX=demo-agents-
REM ^ This prefix keeps all demo agents in a separate "folder"!
REM   Your services: demo-agents-portfolio-manager, demo-agents-access-controller, etc.
REM   In GCP Console, filter by label "app=drayvn-demo" to see only these

REM Check if project ID is set
if "%PROJECT_ID%"=="YOUR_GCP_PROJECT_ID" (
    echo.
    echo ============================================
    echo  ERROR: Please set your PROJECT_ID first!
    echo ============================================
    echo.
    echo Edit this file and set:
    echo   PROJECT_ID=your-actual-gcp-project-id
    echo   GOOGLE_API_KEY=your-api-key
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Drayvn Agents - Bulk Cloud Run Deployment
echo ============================================
echo  Project: %PROJECT_ID%
echo  Region:  %REGION%
echo ============================================
echo.

REM Enable required APIs
echo Enabling Cloud Run and Cloud Build APIs...
gcloud services enable run.googleapis.com cloudbuild.googleapis.com --project=%PROJECT_ID%

REM Set project
gcloud config set project %PROJECT_ID%

echo.
echo Starting deployment of all agents...
echo.

set DEPLOYED=0
set FAILED=0

REM ============================================
REM DEPLOY EACH AGENT
REM ============================================

REM 1. Access Controller Agent
call :deploy_agent "access_controller_agent" "access-controller" "streamlit_app.py"

REM 2. Campaign Validator Agent
call :deploy_agent "campaign_validator_agent" "campaign-validator" "app.py"

REM 3. Portfolio Manager
call :deploy_agent "portfolio_manager" "portfolio-manager" "streamlit_app.py"

REM 4. PR Code Reviewer
call :deploy_agent "pr_code_reviewer" "pr-code-reviewer" "streamlit_app.py"

REM 5. Research Assistant
call :deploy_agent "research_assistant" "research-assistant" "streamlit_app.py"

REM 6. Loan Underwriter (Fan Out/Fan In)
call :deploy_agent "FAN out-FAN in" "loan-underwriter" "streamlit_app.py"

REM 7. Content Moderator
call :deploy_agent "social_media_content_moderation" "content-moderator" "streamlit_app.py"

REM 8. HelpDesk Bot (Router Pattern)
call :deploy_agent "Router Pattern" "helpdesk-bot" "streamlit_app.py"

REM 9. Social Media Trends
call :deploy_agent "social_media_marketing" "social-media-trends" "streamlit_app.py"

REM 10. Portfolio Swarm
call :deploy_agent "Swarm Pattern" "portfolio-swarm" "streamlit_app.py"

REM ============================================
REM SUMMARY
REM ============================================
echo.
echo ============================================
echo  DEPLOYMENT SUMMARY
echo ============================================
echo  Deployed: %DEPLOYED% agents
echo  Failed:   %FAILED% agents
echo ============================================
echo.
echo Your demo URLs (with prefix %SERVICE_PREFIX%):
echo.
echo   Access Controller:    https://%SERVICE_PREFIX%access-controller-xxx.%REGION%.run.app
echo   Campaign Validator:   https://%SERVICE_PREFIX%campaign-validator-xxx.%REGION%.run.app
echo   Portfolio Manager:    https://%SERVICE_PREFIX%portfolio-manager-xxx.%REGION%.run.app
echo   PR Code Reviewer:     https://%SERVICE_PREFIX%pr-code-reviewer-xxx.%REGION%.run.app
echo   Research Assistant:   https://%SERVICE_PREFIX%research-assistant-xxx.%REGION%.run.app
echo   Loan Underwriter:     https://%SERVICE_PREFIX%loan-underwriter-xxx.%REGION%.run.app
echo   Content Moderator:    https://%SERVICE_PREFIX%content-moderator-xxx.%REGION%.run.app
echo   HelpDesk Bot:         https://%SERVICE_PREFIX%helpdesk-bot-xxx.%REGION%.run.app
echo   Social Media Trends:  https://%SERVICE_PREFIX%social-media-trends-xxx.%REGION%.run.app
echo   Portfolio Swarm:      https://%SERVICE_PREFIX%portfolio-swarm-xxx.%REGION%.run.app
echo.
echo To get exact URLs, run: gcloud run services list --region=%REGION%
echo.
echo In GCP Console, filter by label: app=drayvn-demo
echo https://console.cloud.google.com/run?project=%PROJECT_ID%
echo.
pause
exit /b 0

REM ============================================
REM FUNCTION: Deploy Single Agent
REM ============================================
:deploy_agent
set FOLDER=%~1
set SERVICE=%SERVICE_PREFIX%%~2
set MAIN_FILE=%~3

echo.
echo ------------------------------------------
echo Deploying: %SERVICE%
echo   Folder: %FOLDER%
echo   Main:   %MAIN_FILE%
echo ------------------------------------------

cd /d "%~dp0%FOLDER%"

if errorlevel 1 (
    echo   [ERROR] Folder not found: %FOLDER%
    set /a FAILED+=1
    cd /d "%~dp0"
    exit /b 1
)

REM Create Dockerfile if not exists
if not exist Dockerfile (
    echo FROM python:3.11-slim > Dockerfile
    echo WORKDIR /app >> Dockerfile
    echo RUN apt-get update ^&^& apt-get install -y build-essential ^&^& rm -rf /var/lib/apt/lists/* >> Dockerfile
    echo COPY requirements.txt* ./ >> Dockerfile
    echo RUN pip install --no-cache-dir streamlit requests python-dotenv ^|^| true >> Dockerfile
    echo RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi >> Dockerfile
    echo COPY . . >> Dockerfile
    echo EXPOSE 8080 >> Dockerfile
    echo ENV STREAMLIT_SERVER_PORT=8080 >> Dockerfile
    echo ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0 >> Dockerfile
    echo ENV STREAMLIT_SERVER_HEADLESS=true >> Dockerfile
    echo CMD ["streamlit", "run", "%MAIN_FILE%", "--server.port=8080", "--server.address=0.0.0.0"] >> Dockerfile
    echo   [INFO] Created Dockerfile
)

REM Deploy to Cloud Run
echo   [INFO] Building and deploying to Cloud Run...
gcloud run deploy %SERVICE% ^
    --source . ^
    --region %REGION% ^
    --platform managed ^
    --allow-unauthenticated ^
    --set-env-vars "GOOGLE_API_KEY=%GOOGLE_API_KEY%" ^
    --memory 1Gi ^
    --timeout 300 ^
    --labels "app=drayvn-demo,team=agents,env=demo" ^
    --quiet

if errorlevel 1 (
    echo   [ERROR] Deployment failed for %SERVICE%
    set /a FAILED+=1
) else (
    echo   [SUCCESS] %SERVICE% deployed!
    set /a DEPLOYED+=1
)

cd /d "%~dp0"
exit /b 0
