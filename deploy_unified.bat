@echo off
REM ============================================
REM Drayvn Agents - UNIFIED Cloud Run Deployment
REM ============================================
REM Deploys ALL agents in ONE Cloud Run service
REM Access via routes: /access-controller, /portfolio-manager, etc.
REM ============================================

setlocal enabledelayedexpansion

REM ============================================
REM CONFIGURE THESE VALUES
REM ============================================
set PROJECT_ID=gcp-drayvn-etoc
set REGION=us-central1
set SERVICE_NAME=drayvn-agents-demo
set GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY

echo.
echo ============================================
echo  Drayvn Agents - Unified Deployment
echo ============================================
echo  Project: %PROJECT_ID%
echo  Service: %SERVICE_NAME%
echo  Region:  %REGION%
echo ============================================
echo.

REM Check if project ID is set
if "%PROJECT_ID%"=="YOUR_GCP_PROJECT_ID" (
    echo ERROR: Please set your PROJECT_ID first!
    pause
    exit /b 1
)

REM Set project
gcloud config set project %PROJECT_ID%

REM Enable required APIs
echo Enabling required APIs...
gcloud services enable run.googleapis.com cloudbuild.googleapis.com --project=%PROJECT_ID%

echo.
echo Building and deploying unified container...
echo This may take 5-10 minutes...
echo.

REM Backup existing Dockerfile if it exists and use unified one
if exist Dockerfile (
    copy Dockerfile Dockerfile.backup >nul
)
copy Dockerfile.unified Dockerfile >nul

REM Deploy from the root directory
gcloud run deploy %SERVICE_NAME% ^
    --source . ^
    --region %REGION% ^
    --platform managed ^
    --allow-unauthenticated ^
    --set-env-vars "GOOGLE_API_KEY=%GOOGLE_API_KEY%" ^
    --memory 4Gi ^
    --cpu 2 ^
    --timeout 300 ^
    --min-instances 0 ^
    --max-instances 3 ^
    --labels "app=drayvn-demo,type=unified"

set DEPLOY_RESULT=%errorlevel%

REM Restore original Dockerfile
if exist Dockerfile.backup (
    move /Y Dockerfile.backup Dockerfile >nul
) else (
    del Dockerfile >nul 2>&1
)

if %DEPLOY_RESULT% neq 0 (
    echo.
    echo [ERROR] Deployment failed!
    pause
    exit /b 1
)

echo.
echo ============================================
echo  DEPLOYMENT SUCCESSFUL!
echo ============================================
echo.
echo Your unified demo URL:
echo   https://%SERVICE_NAME%-%PROJECT_ID%.%REGION%.run.app
echo.
echo Routes available:
echo   /                    - Landing Page (all agents)
echo   /access-controller   - Access Controller Agent
echo   /portfolio-manager   - Portfolio Manager
echo   /campaign-validator  - Campaign Validator
echo   /pr-code-reviewer    - PR Code Reviewer
echo   /research-assistant  - Research Assistant
echo   /loan-underwriter    - Loan Underwriter
echo   /content-moderator   - Content Moderator
echo   /helpdesk-bot        - HelpDesk Bot
echo   /social-media-trends - Social Media Trends
echo   /portfolio-swarm     - Portfolio Swarm
echo.
echo To get exact URL:
echo   gcloud run services describe %SERVICE_NAME% --region=%REGION% --format="value(status.url)"
echo.
pause
