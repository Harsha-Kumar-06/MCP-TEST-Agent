@echo off
REM Google Cloud Run Deployment Script for Drayvn Agents
REM Usage: deploy_cloud_run.bat [agent-folder] [service-name]
REM Example: deploy_cloud_run.bat portfolio_manager portfolio-manager

setlocal enabledelayedexpansion

set PROJECT_ID=YOUR_GCP_PROJECT_ID
set REGION=us-central1

if "%1"=="" (
    echo.
    echo ========================================
    echo  Drayvn Agents - Cloud Run Deployment
    echo ========================================
    echo.
    echo Usage: deploy_cloud_run.bat [agent-folder] [service-name]
    echo.
    echo Available agents:
    echo   access_controller_agent    access-controller
    echo   campaign_validator_agent   campaign-validator
    echo   portfolio_manager          portfolio-manager
    echo   pr_code_reviewer           pr-code-reviewer
    echo   research_assistant         research-assistant
    echo   "FAN out-FAN in"           loan-underwriter
    echo   social_media_content_moderation  content-moderator
    echo   "Router Pattern"           helpdesk-bot
    echo   social_media_marketing     social-media-trends
    echo   "Swarm Pattern"            portfolio-swarm
    echo.
    echo Example:
    echo   deploy_cloud_run.bat portfolio_manager portfolio-manager
    echo.
    echo First, set your PROJECT_ID in this script!
    exit /b 1
)

set AGENT_FOLDER=%1
set SERVICE_NAME=%2

echo.
echo Deploying %SERVICE_NAME% from %AGENT_FOLDER%...
echo.

REM Navigate to agent folder
cd /d "%~dp0%AGENT_FOLDER%"

REM Copy Dockerfile if not exists
if not exist Dockerfile (
    copy "%~dp0Dockerfile.streamlit" Dockerfile
)

REM Build and deploy to Cloud Run
echo Building and deploying to Cloud Run...
gcloud run deploy %SERVICE_NAME% ^
    --source . ^
    --region %REGION% ^
    --platform managed ^
    --allow-unauthenticated ^
    --set-env-vars "GOOGLE_API_KEY=YOUR_API_KEY" ^
    --memory 1Gi ^
    --timeout 300

echo.
echo Deployment complete!
echo Your app URL: https://%SERVICE_NAME%-%PROJECT_ID%.%REGION%.run.app
echo.

cd /d "%~dp0"
