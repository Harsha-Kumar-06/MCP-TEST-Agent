@echo off
REM Google Cloud Run Deployment Script for Drayvn Agents
REM Usage: deploy_cloud_run.bat [agent-folder] [service-name]
REM Example: deploy_cloud_run.bat portfolio_manager portfolio-manager

setlocal enabledelayedexpansion

REM ============================================
REM CONFIGURE THESE VALUES
REM ============================================
set PROJECT_ID=gcp-drayvn-etoc
set REGION=us-central1
set SERVICE_PREFIX=demo-agents-
REM ^ This prefix keeps all demo agents separate!
REM   Your services will be named: demo-agents-portfolio-manager, demo-agents-access-controller, etc.
REM   Set to empty (SERVICE_PREFIX=) if you don't want a prefix

if "%1"=="" (
    echo.
    echo ========================================
    echo  Drayvn Agents - Cloud Run Deployment
    echo ========================================
    echo  Project: %PROJECT_ID%
    echo  Prefix:  %SERVICE_PREFIX%
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
    echo Services will be deployed as: %SERVICE_PREFIX%[service-name]
    exit /b 1
)

set AGENT_FOLDER=%1
set SERVICE_NAME=%SERVICE_PREFIX%%2

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
    --timeout 300 ^
    --labels "app=drayvn-demo,team=agents,env=demo"

echo.
echo ============================================
echo  Deployment complete!
echo ============================================
echo  Service: %SERVICE_NAME%
echo  URL: https://%SERVICE_NAME%-%PROJECT_ID%.%REGION%.run.app
echo.
echo  To view all demo agents in GCP Console:
echo  https://console.cloud.google.com/run?project=%PROJECT_ID%
echo  Filter by label: app=drayvn-demo
echo ============================================
echo.

cd /d "%~dp0"
