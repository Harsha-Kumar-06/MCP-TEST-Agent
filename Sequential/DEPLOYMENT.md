# 🌐 Deployment Guide

Guide for deploying the AI Research Assistant to production environments.

---

## 🎯 Deployment Options

1. **Local Development** (✅ Default - Already configured)
2. **Cloud Deployment** (Heroku, Railway, Render)
3. **Docker Container** (Containerized deployment)
4. **VPS/Dedicated Server** (AWS EC2, DigitalOcean, etc.)

---

## 🐳 Option 1: Docker Deployment

### Create Dockerfile

Create a file named `Dockerfile` in the project root:

```dockerfile
# Use official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "main.py"]
```

### Create .dockerignore

```
__pycache__/
*.pyc
*.pyo
*.pyd
.env
.git/
.gitignore
venv/
*.md
tests/
.vscode/
```

### Build and Run Docker Container

```bash
# Build image
docker build -t research-assistant .

# Run container
docker run -d \
  -p 8000:8000 \
  -e GOOGLE_API_KEY=your_api_key_here \
  --name research-assistant \
  research-assistant

# View logs
docker logs -f research-assistant

# Stop container
docker stop research-assistant
```

### Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  research-assistant:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - GOOGLE_CSE_ID=${GOOGLE_CSE_ID}
      - GOOGLE_CSE_API_KEY=${GOOGLE_CSE_API_KEY}
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
```

Run with:
```bash
docker-compose up -d
```

---

## ☁️ Option 2: Cloud Platform Deployment

### Heroku

1. **Install Heroku CLI**
   ```bash
   # Windows: Download from https://devcenter.heroku.com/articles/heroku-cli
   # macOS: brew install heroku
   # Linux: snap install heroku --classic
   ```

2. **Create Procfile**
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

3. **Deploy**
   ```bash
   heroku login
   heroku create your-research-assistant
   heroku config:set GOOGLE_API_KEY=your_api_key_here
   git push heroku main
   ```

### Railway.app

1. Visit [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Add environment variables:
   - `GOOGLE_API_KEY`
   - `PORT=8000`
5. Deploy automatically

### Render.com

1. Visit [render.com](https://render.com)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Environment Variables**: Add `GOOGLE_API_KEY`
5. Deploy

---

## 🖥️ Option 3: VPS/Server Deployment

### Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Root or sudo access
- Domain name (optional but recommended)

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx certbot python3-certbot-nginx -y

# Create application user
sudo useradd -m -s /bin/bash appuser
sudo su - appuser
```

### Step 2: Deploy Application

```bash
# Clone repository or upload files
cd ~
# Upload your files here or git clone

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOL
GOOGLE_API_KEY=your_api_key_here
EOL
```

### Step 3: Create Systemd Service

Exit to root/sudo user and create service file:

```bash
sudo nano /etc/systemd/system/research-assistant.service
```

Add:

```ini
[Unit]
Description=AI Research Assistant
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/home/appuser/Sequential
Environment="PATH=/home/appuser/Sequential/venv/bin"
ExecStart=/home/appuser/Sequential/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable research-assistant
sudo systemctl start research-assistant
sudo systemctl status research-assistant
```

### Step 4: Configure Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/research-assistant
```

Add:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 50M;  # Allow large file uploads
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/research-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 5: Enable HTTPS (Optional but Recommended)

```bash
sudo certbot --nginx -d your-domain.com
```

Follow the prompts to set up SSL certificate.

---

## 🔒 Production Best Practices

### 1. Security

```python
# Update main.py for production

# Add CORS middleware if needed
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Add rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/research")
@limiter.limit("10/minute")  # 10 requests per minute
async def research_endpoint(...):
    ...
```

### 2. Environment Variables

Never commit `.env` to version control:

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "*.env" >> .gitignore
```

### 3. Logging

Configure production logging:

```python
import logging
from logging.handlers import RotatingFileHandler

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Configure file handler
handler = RotatingFileHandler(
    "logs/app.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
handler.setFormatter(
    logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### 4. Performance Optimization

```python
# Update main.py

# Add gzip compression
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Increase workers for production
if __name__ == "__main__":
    import multiprocessing
    
    workers = multiprocessing.cpu_count() * 2 + 1
    
    uvicorn.run(
        app,
        host="0.0.0.0",  # Allow external connections
        port=8000,
        workers=workers,  # Multiple workers
        log_level="info"
    )
```

### 5. Monitoring

Set up basic health check:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "api_key_configured": bool(os.getenv("GOOGLE_API_KEY"))
    }
```

Monitor with:
```bash
# Check every 5 minutes
*/5 * * * * curl -f http://localhost:8000/health || systemctl restart research-assistant
```

---

## 📊 Scaling Considerations

### Horizontal Scaling

For high traffic, deploy multiple instances behind a load balancer:

```
Internet → Load Balancer → Instance 1
                       └→ Instance 2
                       └→ Instance 3
```

### Caching

Add Redis for caching responses:

```python
import redis
from functools import lru_cache

redis_client = redis.Redis(host='localhost', port=6379, db=0)

@lru_cache(maxsize=100)
def get_cached_analysis(document_hash: str):
    cached = redis_client.get(f"analysis:{document_hash}")
    if cached:
        return json.loads(cached)
    return None
```

### Database

For persistent storage:

```python
# Add PostgreSQL for storing results
from sqlalchemy import create_engine

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
```

---

## 🔍 Monitoring & Maintenance

### Application Logs

```bash
# View real-time logs
sudo journalctl -u research-assistant -f

# View last 100 lines
sudo journalctl -u research-assistant -n 100

# View errors only
sudo journalctl -u research-assistant -p err
```

### System Monitoring

```bash
# Check CPU/Memory usage
htop

# Check disk space
df -h

# Check network
netstat -tulpn | grep 8000
```

### Backup

Regular backups:

```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf backup_$DATE.tar.gz /home/appuser/Sequential
# Upload to S3 or backup location
```

---

## 🚨 Troubleshooting Production Issues

### Service Not Starting

```bash
# Check service status
sudo systemctl status research-assistant

# Check logs
sudo journalctl -u research-assistant -n 50

# Test manually
sudo su - appuser
cd Sequential
source venv/bin/activate
python main.py
```

### High Memory Usage

```python
# Add memory limits in systemd service
[Service]
MemoryLimit=2G
MemoryMax=2.5G
```

### Slow Response Times

- Enable response caching
- Add more workers
- Use CDN for static files
- Optimize document processing

---

## 📋 Deployment Checklist

- [ ] Environment variables configured
- [ ] API keys securely stored
- [ ] SSL certificate installed
- [ ] Firewall configured (ports 80, 443)
- [ ] Logging enabled
- [ ] Monitoring set up
- [ ] Backup strategy in place
- [ ] Error alerting configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Documentation updated
- [ ] Health check endpoint working

---

## 📞 Support

For deployment issues:
1. Check application logs
2. Verify API key and quotas
3. Test with minimal configuration
4. Review security groups/firewall rules
5. Check server resources (CPU, memory, disk)

---

**Ready to deploy?** Start with Docker for easiest setup, then scale to VPS when needed! 🚀
