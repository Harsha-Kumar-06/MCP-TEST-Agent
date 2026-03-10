@echo off
REM ============================================
REM Create Dockerfiles for all agents
REM Run this before docker-compose up
REM ============================================

echo Creating Dockerfiles for all agents...

REM Access Controller Agent
echo Creating Dockerfile for access_controller_agent...
(
echo FROM python:3.11-slim
echo WORKDIR /app
echo RUN apt-get update ^&^& apt-get install -y build-essential ^&^& rm -rf /var/lib/apt/lists/*
echo COPY requirements.txt* ./
echo RUN pip install --no-cache-dir streamlit requests python-dotenv google-generativeai ^|^| true
echo RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
echo COPY . .
echo EXPOSE 8501
echo ENV STREAMLIT_SERVER_PORT=8501
echo ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
echo ENV STREAMLIT_SERVER_HEADLESS=true
echo CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
) > access_controller_agent\Dockerfile

REM Portfolio Manager
echo Creating Dockerfile for portfolio_manager...
(
echo FROM python:3.11-slim
echo WORKDIR /app
echo RUN apt-get update ^&^& apt-get install -y build-essential ^&^& rm -rf /var/lib/apt/lists/*
echo COPY requirements.txt* ./
echo RUN pip install --no-cache-dir streamlit requests python-dotenv google-generativeai ^|^| true
echo RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
echo COPY . .
echo EXPOSE 8501
echo ENV STREAMLIT_SERVER_PORT=8501
echo ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
echo ENV STREAMLIT_SERVER_HEADLESS=true
echo CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
) > portfolio_manager\Dockerfile

REM Campaign Validator (uses app.py)
echo Creating Dockerfile for campaign_validator_agent...
(
echo FROM python:3.11-slim
echo WORKDIR /app
echo RUN apt-get update ^&^& apt-get install -y build-essential ^&^& rm -rf /var/lib/apt/lists/*
echo COPY requirements.txt* ./
echo RUN pip install --no-cache-dir streamlit requests python-dotenv google-generativeai ^|^| true
echo RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
echo COPY . .
echo EXPOSE 8501
echo ENV STREAMLIT_SERVER_PORT=8501
echo ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
echo ENV STREAMLIT_SERVER_HEADLESS=true
echo CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
) > campaign_validator_agent\Dockerfile

REM PR Code Reviewer
echo Creating Dockerfile for pr_code_reviewer...
(
echo FROM python:3.11-slim
echo WORKDIR /app
echo RUN apt-get update ^&^& apt-get install -y build-essential ^&^& rm -rf /var/lib/apt/lists/*
echo COPY requirements.txt* ./
echo RUN pip install --no-cache-dir streamlit requests python-dotenv google-generativeai ^|^| true
echo RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
echo COPY . .
echo EXPOSE 8501
echo ENV STREAMLIT_SERVER_PORT=8501
echo ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
echo ENV STREAMLIT_SERVER_HEADLESS=true
echo CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
) > pr_code_reviewer\Dockerfile

REM Research Assistant
echo Creating Dockerfile for research_assistant...
(
echo FROM python:3.11-slim
echo WORKDIR /app
echo RUN apt-get update ^&^& apt-get install -y build-essential ^&^& rm -rf /var/lib/apt/lists/*
echo COPY requirements.txt* ./
echo RUN pip install --no-cache-dir streamlit requests python-dotenv google-generativeai ^|^| true
echo RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
echo COPY . .
echo EXPOSE 8501
echo ENV STREAMLIT_SERVER_PORT=8501
echo ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
echo ENV STREAMLIT_SERVER_HEADLESS=true
echo CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
) > research_assistant\Dockerfile

REM Loan Underwriter (FAN out-FAN in)
echo Creating Dockerfile for FAN out-FAN in...
(
echo FROM python:3.11-slim
echo WORKDIR /app
echo RUN apt-get update ^&^& apt-get install -y build-essential ^&^& rm -rf /var/lib/apt/lists/*
echo COPY requirements.txt* ./
echo RUN pip install --no-cache-dir streamlit requests python-dotenv google-generativeai ^|^| true
echo RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
echo COPY . .
echo EXPOSE 8501
echo ENV STREAMLIT_SERVER_PORT=8501
echo ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
echo ENV STREAMLIT_SERVER_HEADLESS=true
echo CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
) > "FAN out-FAN in\Dockerfile"

REM Content Moderator
echo Creating Dockerfile for social_media_content_moderation...
(
echo FROM python:3.11-slim
echo WORKDIR /app
echo RUN apt-get update ^&^& apt-get install -y build-essential ^&^& rm -rf /var/lib/apt/lists/*
echo COPY requirements.txt* ./
echo RUN pip install --no-cache-dir streamlit requests python-dotenv google-generativeai ^|^| true
echo RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
echo COPY . .
echo EXPOSE 8501
echo ENV STREAMLIT_SERVER_PORT=8501
echo ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
echo ENV STREAMLIT_SERVER_HEADLESS=true
echo CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
) > social_media_content_moderation\Dockerfile

REM HelpDesk Bot (Router Pattern)
echo Creating Dockerfile for Router Pattern...
(
echo FROM python:3.11-slim
echo WORKDIR /app
echo RUN apt-get update ^&^& apt-get install -y build-essential ^&^& rm -rf /var/lib/apt/lists/*
echo COPY requirements.txt* ./
echo RUN pip install --no-cache-dir streamlit requests python-dotenv google-generativeai ^|^| true
echo RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
echo COPY . .
echo EXPOSE 8501
echo ENV STREAMLIT_SERVER_PORT=8501
echo ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
echo ENV STREAMLIT_SERVER_HEADLESS=true
echo CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
) > "Router Pattern\Dockerfile"

REM Social Media Trends
echo Creating Dockerfile for social_media_marketing...
(
echo FROM python:3.11-slim
echo WORKDIR /app
echo RUN apt-get update ^&^& apt-get install -y build-essential ^&^& rm -rf /var/lib/apt/lists/*
echo COPY requirements.txt* ./
echo RUN pip install --no-cache-dir streamlit requests python-dotenv google-generativeai ^|^| true
echo RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
echo COPY . .
echo EXPOSE 8501
echo ENV STREAMLIT_SERVER_PORT=8501
echo ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
echo ENV STREAMLIT_SERVER_HEADLESS=true
echo CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
) > social_media_marketing\Dockerfile

REM Portfolio Swarm
echo Creating Dockerfile for Swarm Pattern...
(
echo FROM python:3.11-slim
echo WORKDIR /app
echo RUN apt-get update ^&^& apt-get install -y build-essential ^&^& rm -rf /var/lib/apt/lists/*
echo COPY requirements.txt* ./
echo RUN pip install --no-cache-dir streamlit requests python-dotenv google-generativeai ^|^| true
echo RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
echo COPY . .
echo EXPOSE 8501
echo ENV STREAMLIT_SERVER_PORT=8501
echo ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
echo ENV STREAMLIT_SERVER_HEADLESS=true
echo CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
) > "Swarm Pattern\Dockerfile"

echo.
echo ============================================
echo  Dockerfiles created for all agents!
echo ============================================
echo.
echo Now you can run:
echo   docker-compose up --build
echo.
pause
