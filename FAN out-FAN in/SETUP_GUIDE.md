# 📖 Complete Setup Guide - Loan Underwriter AI System

This comprehensive guide will help you set up and run the Loan Underwriter Multi-Agent System from scratch. Follow these steps carefully.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Application](#running-the-application)
5. [Using the Web UI](#using-the-web-ui)
6. [API Usage](#api-usage)
7. [Troubleshooting](#troubleshooting)
8. [Production Deployment](#production-deployment)
9. [FAQ](#frequently-asked-questions)

---

## Prerequisites

### Required Software

1. **Python 3.10 or higher**
   - Download from: https://www.python.org/downloads/
   - Verify installation: `python --version`

2. **pip** (Python package manager)
   - Usually included with Python
   - Verify: `pip --version`

3. **Google AI API Key**
   - Get your free API key from: https://aistudio.google.com/app/apikey
   - This is required for the AI agents to function

### System Requirements

- **OS**: Windows 10/11, macOS 10.15+, or Linux
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk**: ~500MB for dependencies
- **Network**: Internet connection for API calls

---

## Installation

### Step 1: Navigate to Project Directory

```bash
cd "c:\Users\Harsha Kumar\Desktop\DRAVYN\Agents\FAN out-FAN in"
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv
```

### Step 3: Activate Virtual Environment

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal.

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `google-genai` - Google ADK for AI agents
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `jinja2` - Template engine
- `pydantic` - Data validation
- `python-dotenv` - Environment management

### Step 5: Verify Installation

```bash
pip list | findstr google
pip list | findstr fastapi
```

---

## Configuration

### Step 1: Create Environment File

**Windows (Command Prompt):**
```cmd
copy .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**macOS/Linux:**
```bash
cp .env.example .env
```

### Step 2: Get Your FREE Google API Key

This is the **only required step** - the app uses simulated data for everything else.

#### Detailed Instructions with Screenshots

**2.1 Open Google AI Studio**
```
https://aistudio.google.com/app/apikey
```

**2.2 Sign In**
- Use any Google/Gmail account
- If you don't have one, create at: https://accounts.google.com/signup

**2.3 Create API Key**
- Look for a blue button: **"Create API key"** or **"+ Create API key in new project"**
- Click it
- A new key will be generated

**2.4 Copy Your Key**
- You'll see a key that looks like: `AIzaSyD-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- It's approximately 39 characters long
- It always starts with `AIza`
- Click the **copy icon** 📋 next to the key

**2.5 Paste in .env File**
- Open the `.env` file you created in Step 1
- Find this line: `GOOGLE_API_KEY=your_google_api_key_here`
- Replace `your_google_api_key_here` with your actual key
- Save the file

#### Example .env File (After Configuration)

```env
# ✅ CORRECT - Real API key (yours will be different)
GOOGLE_API_KEY=AIzaSyDk7hF9xxxxxxxxxxxxxxxxxxxxxxxxxxx

# ❌ WRONG - Still has placeholder
GOOGLE_API_KEY=your_google_api_key_here
```

### Step 3: Verify Your Configuration

Run this command to check your setup:

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); key=os.getenv('GOOGLE_API_KEY',''); print('✅ API Key configured!' if key.startswith('AIza') else '❌ API Key missing or invalid')"
```

### Configuration Reference

| Variable | Required | Description | How to Get |
|----------|----------|-------------|------------|
| `GOOGLE_API_KEY` | ✅ Yes | Google Gemini AI API key | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| `DEBUG` | No | Enable debug mode | Set to `true` or `false` |
| `HOST` | No | Server address | Default: `127.0.0.1` |
| `PORT` | No | Server port | Default: `8000` |

### Optional: External API Keys (Production Only)

These are **NOT required** for the demo. The app uses simulated data by default.

| API | Purpose | Where to Get | Notes |
|-----|---------|--------------|-------|
| RentCast API | Property values | [rentcast.io](https://developers.rentcast.io) | Free tier available |
| Experian API | Credit reports | [developer.experian.com](https://developer.experian.com) | Requires business verification |
| Equifax API | Credit reports | [developer.equifax.com](https://developer.equifax.com) | Requires business verification |
| Persona API | Fraud detection | [withpersona.com](https://withpersona.com) | Free sandbox for testing |

---

## Complete API Keys Reference

This section provides detailed instructions for obtaining **all** API keys used in the project.

### 1. Google API Key (REQUIRED)

The **only required key** to run the application.

**Purpose:** Powers the AI agents using Google Gemini models.

**Cost:** FREE with generous limits (15 requests/minute, 1,500 requests/day)

**Step-by-Step Instructions:**

1. **Go to Google AI Studio**
   ```
   https://aistudio.google.com/app/apikey
   ```

2. **Sign in with Google Account**
   - Use any Gmail account
   - No credit card required
   - No special permissions needed

3. **Create API Key**
   - Click the blue **"Create API key"** button
   - Or click **"+ Create API key in new project"**
   - Wait a few seconds for generation

4. **Copy the Key**
   - Your key looks like: `AIzaSyD-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - Always starts with `AIza`
   - Approximately 39 characters long
   - Click the copy icon 📋

5. **Add to .env File**
   ```env
   GOOGLE_API_KEY=AIzaSyDk7hF9xxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

**Troubleshooting:**
- If key doesn't work, ensure you copied the full key (no spaces)
- Check that you're using the AI Studio key, not Cloud Console key
- Regenerate the key if issues persist

---

### 2. Google Cloud / Vertex AI (OPTIONAL - Enterprise)

For enterprise deployments with advanced features, compliance requirements, or higher rate limits.

**Purpose:** Enterprise-grade AI with SLA guarantees, VPC support, and advanced monitoring.

**Cost:** Pay-per-use (has free tier: $300 credit for new accounts)

**Step-by-Step Instructions:**

1. **Create Google Cloud Account**
   ```
   https://cloud.google.com
   ```
   - Click "Get started for free"
   - Requires credit card (for verification, won't be charged for free tier)

2. **Create a New Project**
   - Go to [Cloud Console](https://console.cloud.google.com)
   - Click project dropdown → "New Project"
   - Name it (e.g., "loan-underwriter")
   - Note your **Project ID** (e.g., `loan-underwriter-12345`)

3. **Enable Vertex AI API**
   - Go to [Vertex AI API](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com)
   - Click **"Enable"**
   - Wait for activation

4. **Set Up Authentication**
   - Go to [IAM & Admin → Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
   - Click **"Create Service Account"**
   - Name: `loan-underwriter-agent`
   - Grant role: `Vertex AI User`
   - Create and download JSON key file

5. **Add to .env File**
   ```env
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
   ```

---

### 3. Zillow API Key (OPTIONAL - Property Valuation)

For real property valuation data instead of simulated estimates.

**Purpose:** Get real-time property value estimates, comparable sales, and market data.

**Cost:** Free tier available (limited calls), paid plans for production

**Step-by-Step Instructions:**

1. **Go to Zillow Developer Portal**
   ```
   https://www.zillow.com/howto/api/APIOverview.htm
   ```
   > Note: Zillow's public API has been deprecated. Consider alternatives below.

2. **Alternative: Bridge Interactive (Zillow Partner)**
   ```
   https://www.bridgeinteractive.com
   ```
   - Sign up for developer account
   - Request API access
   - Typical approval: 1-3 business days

3. **Alternative: ATTOM Data**
   ```
   https://www.attomdata.com
   ```
   - More comprehensive property data
   - Sign up at: https://api.attomdata.com/signup
   - Free trial available (1,000 calls)

4. **Alternative: Realty Mole**
   ```
   https://www.realtymole.com
   ```
   - Sign up for free account
   - Get API key from dashboard
   - Free tier: 50 calls/month

5. **Add to .env File**
   ```env
   ZILLOW_API_KEY=your_property_api_key_here
   ```

---

### 4. Credit Bureau API (OPTIONAL - Credit Reports)

For real credit report data. **Requires business verification.**

**Purpose:** Pull real credit scores, payment history, and credit reports.

**Cost:** Per-pull pricing (typically $1-5 per report), requires business account

**Important:** Credit bureau APIs require:
- Registered business entity
- Permissible purpose documentation
- Compliance with FCRA (Fair Credit Reporting Act)
- Security audit/certification

**Credit Bureau Selection:**

Set `CREDIT_BUREAU` in your `.env` file to choose the data source:
```env
CREDIT_BUREAU=simulated   # Use simulated data (default, recommended for demos)
CREDIT_BUREAU=experian    # Use Experian API
CREDIT_BUREAU=equifax     # Use Equifax API
```

**Option A: Experian**

1. **Go to Experian Developer Portal**
   ```
   https://developer.experian.com
   ```

2. **Create Developer Account**
   - Click "Sign Up"
   - Provide business information
   - Requires business email (not Gmail)

3. **Apply for API Access**
   - Select "Credit Services" → "Consumer Credit"
   - Submit business documentation
   - Compliance review: 2-4 weeks

4. **Add to .env File**
   ```env
   CREDIT_BUREAU=experian
   EXPERIAN_CLIENT_ID=your_client_id
   EXPERIAN_CLIENT_SECRET=your_client_secret
   EXPERIAN_ENVIRONMENT=sandbox   # or production
   EXPERIAN_BIN=your_bin_number
   EXPERIAN_SUB_CODE=your_sub_code
   ```

**Option B: Equifax**
```
https://developer.equifax.com
```
1. Sign up at Equifax Developer Portal
2. Create an application to get credentials
3. Apply for Consumer Credit Report API access

4. **Add to .env File**
   ```env
   CREDIT_BUREAU=equifax
   EQUIFAX_CLIENT_ID=your_client_id
   EQUIFAX_CLIENT_SECRET=your_client_secret
   EQUIFAX_ENVIRONMENT=sandbox   # or production
   EQUIFAX_MEMBER_NUMBER=your_member_number
   EQUIFAX_SECURITY_CODE=your_security_code
   ```

**Option C: TransUnion**
```
https://developer.transunion.com
```
- TrueVision API for credit data
- Requires business agreement

**Option D: Simulated Data (Recommended for Development)**
```env
CREDIT_BUREAU=simulated
```
- No API keys required
- Generates realistic mock credit data
- Perfect for demos and development

---

### 5. Fraud Detection API (OPTIONAL - Identity Verification)

For real identity verification and fraud screening.

**Purpose:** Verify identity documents, check watchlists, detect synthetic identities.

**Cost:** Per-verification pricing (typically $1-10 per check)

**Option A: Jumio**

1. **Go to Jumio Developer Portal**
   ```
   https://www.jumio.com/developers/
   ```

2. **Request Demo/API Access**
   - Click "Request Demo"
   - Fill in business information
   - Sales team will contact you

3. **Get API Credentials**
   - After approval, access Developer Portal
   - Get API Token and API Secret
   - Sandbox environment for testing

4. **Add to .env File**
   ```env
   FRAUD_DETECTION_API_KEY=your_jumio_api_token
   ```

**Option B: Onfido**

1. **Sign Up**
   ```
   https://onfido.com/signup/
   ```

2. **Get API Token**
   - Dashboard → Developers → Tokens
   - Create sandbox token (free testing)
   - Create live token (requires approval)

3. **Add to .env File**
   ```env
   FRAUD_DETECTION_API_KEY=your_onfido_api_token
   ```

**Option C: IDology (Now part of GBG)**
```
https://www.gbgplc.com/en/products/idology/
```
- Enterprise identity verification
- Contact sales for API access

**Option D: Persona (Easier Alternative)**
```
https://withpersona.com
```
1. Sign up at https://app.withpersona.com/sign-up
2. Free sandbox with 50 test verifications
3. Get API key from Dashboard → API Keys
4. Good documentation and easy integration

---

### Quick Reference: All Environment Variables

```env
# ═══════════════════════════════════════════════════════════════
# REQUIRED (Must have this to run the app)
# ═══════════════════════════════════════════════════════════════
GOOGLE_API_KEY=AIzaSyD...your_key_here

# ═══════════════════════════════════════════════════════════════
# OPTIONAL - Google Cloud (Enterprise deployments)
# ═══════════════════════════════════════════════════════════════
# GOOGLE_CLOUD_PROJECT=your-project-id
# GOOGLE_CLOUD_LOCATION=us-central1

# ═══════════════════════════════════════════════════════════════
# OPTIONAL - External APIs (Production only - app works without these)
# ═══════════════════════════════════════════════════════════════

# Credit Bureau Selection (simulated, experian, or equifax)
CREDIT_BUREAU=simulated

# Property Data API (RentCast)
RENTCAST_API_KEY=your_rentcast_key

# Experian API (if CREDIT_BUREAU=experian)
EXPERIAN_CLIENT_ID=your_client_id
EXPERIAN_CLIENT_SECRET=your_client_secret
EXPERIAN_ENVIRONMENT=sandbox
EXPERIAN_BIN=your_bin
EXPERIAN_SUB_CODE=your_sub_code

# Equifax API (if CREDIT_BUREAU=equifax)
EQUIFAX_CLIENT_ID=your_client_id
EQUIFAX_CLIENT_SECRET=your_client_secret
EQUIFAX_ENVIRONMENT=sandbox
EQUIFAX_MEMBER_NUMBER=your_member_number
EQUIFAX_SECURITY_CODE=your_security_code

# Fraud Detection (Persona API)
PERSONA_API_KEY=your_persona_key
PERSONA_ENVIRONMENT=sandbox

# ═══════════════════════════════════════════════════════════════
# APPLICATION SETTINGS
# ═══════════════════════════════════════════════════════════════
DEBUG=true
HOST=127.0.0.1
PORT=8000
```

---

### API Providers Comparison Table

| Feature | Provider | Cost | Ease of Setup | Best For |
|---------|----------|------|---------------|----------|
| **AI/LLM** | Google AI Studio | Free | ⭐⭐⭐⭐⭐ | Development, demos |
| **AI/LLM** | Google Vertex AI | Pay-per-use | ⭐⭐⭐ | Enterprise, production |
| **Property** | RentCast | Free tier | ⭐⭐⭐⭐ | Startups, testing |
| **Property** | ATTOM Data | Paid | ⭐⭐⭐ | Production |
| **Credit** | Simulated | Free | ⭐⭐⭐⭐⭐ | Development, demos |
| **Credit** | Experian | Paid | ⭐⭐ | Enterprise |
| **Fraud** | Persona | Free sandbox | ⭐⭐⭐⭐ | Startups, SMB |
| **Fraud** | Jumio | Paid | ⭐⭐ | Enterprise |

---

## Running the Application

### Option 1: Production Mode

```bash
python main.py
```

### Option 2: Development Mode (with auto-reload)

```bash
python run.py
```

### Expected Output

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🏦 LOAN UNDERWRITER - AI MULTI-AGENT SYSTEM 🤖         ║
║                                                           ║
║   Fan-Out/Fan-In Architecture for Rapid Processing       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Starting server at http://127.0.0.1:8000
API Documentation: http://127.0.0.1:8000/docs
Debug Mode: True

INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

## Using the Web UI

### Access the Application

Open your browser and navigate to: **http://localhost:8000**

### Home Page Features

1. **Overview**: System architecture explanation
2. **Run Demo**: Quick demo with sample data
3. **New Application**: Submit your own application

### Submitting an Application

1. Click "New Application" in navigation
2. Fill in applicant information:
   - Personal details (name, SSN last 4, DOB)
   - Employment information
   - Property details
   - Loan amount
3. Click "Submit Application"
4. Wait for processing (~30-60 seconds)
5. View results with risk scores

### Understanding Results

The results page shows:

- **Approval Confidence Score**: 0-100%
- **Decision**: Approved / Manual Review / Denied
- **Credit Analysis**: Credit score, DTI ratio, risk level
- **Property Valuation**: Estimated value, valuation gap
- **Fraud Detection**: Identity verification, watchlist status
- **Conditions**: Any requirements for approval
- **Next Steps**: Recommended actions

---

## API Usage

### Interactive API Documentation

Visit **http://localhost:8000/docs** for Swagger UI.

### Quick Start - Run Demo

```bash
curl -X POST "http://localhost:8000/api/v1/applications/demo" \
     -H "Content-Type: application/json"
```

### Submit Custom Application

```bash
curl -X POST "http://localhost:8000/api/v1/applications/process" \
     -H "Content-Type: application/json" \
     -d '{
       "applicant": {
         "first_name": "John",
         "last_name": "Smith",
         "ssn": "1234",
         "date_of_birth": "1985-06-15",
         "email": "john@example.com",
         "phone": "555-123-4567",
         "current_address": "123 Main St, City, ST 12345",
         "employment_status": "employed",
         "employer_name": "Tech Corp",
         "years_employed": 5,
         "annual_income": 125000
       },
       "property": {
         "address": "456 Oak Ave",
         "city": "Pleasant Valley",
         "state": "CA",
         "zip_code": "90210",
         "property_type": "single_family",
         "year_built": 2015,
         "square_feet": 2500,
         "bedrooms": 4,
         "bathrooms": 2.5,
         "asking_price": 750000,
         "down_payment": 150000,
         "loan_amount": 600000
       },
       "income_docs": {
         "w2_provided": true,
         "tax_returns_years": 2,
         "pay_stubs_months": 3,
         "bank_statements_months": 3,
         "additional_income_sources": []
       }
     }'
```

### Get Application Result

```bash
curl "http://localhost:8000/api/v1/applications/APP-XXXXXXXX"
```

---

## Troubleshooting

### Common Issues

#### 1. "GOOGLE_API_KEY not set"

**Solution**: Ensure `.env` file exists and contains valid API key.

```bash
# Check if .env exists
dir .env

# Verify content
type .env
```

#### 2. "Module not found" errors

**Solution**: Ensure virtual environment is activated and dependencies installed.

```bash
# Reactivate venv
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 3. Port already in use

**Solution**: Change port in `.env` file or kill existing process.

```bash
# Change port
PORT=8001

# Or find and kill process (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

#### 4. API returns 500 error

**Solution**: Check API key validity and enable debug mode.

```bash
# Enable debug
DEBUG=true

# Check logs in terminal for details
```

#### 5. Slow processing

**Solution**: This is normal on first run as models initialize. Subsequent runs are faster.

### Debug Mode

Enable detailed logging:

```env
DEBUG=true
```

Then check terminal output for detailed logs.

---

## Production Deployment

### Using Gunicorn (Linux/macOS)

```bash
pip install gunicorn
gunicorn loan_underwriter.app:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "main.py"]
```

Build and run:

```bash
docker build -t loan-underwriter .
docker run -p 8000:8000 --env-file .env loan-underwriter
```

### Environment Variables for Production

```env
DEBUG=false
HOST=0.0.0.0
PORT=8000
GOOGLE_API_KEY=your_key
```

### Security Checklist

- [ ] Disable DEBUG mode
- [ ] Use HTTPS (add SSL certificate)
- [ ] Implement authentication
- [ ] Add rate limiting
- [ ] Set up logging and monitoring
- [ ] Use secrets management for API keys

---

## Next Steps

1. **Customize Agents**: Modify agent prompts in `loan_underwriter/agents/`
2. **Add Real APIs**: Replace mock API calls with real integrations
3. **Enhance UI**: Customize templates in `loan_underwriter/templates/`
4. **Add Database**: Replace in-memory storage with PostgreSQL/MongoDB
5. **Add Authentication**: Implement user authentication

---

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review API documentation at `/docs`
3. Check terminal logs for error details

---

## Frequently Asked Questions

### Q: Is the Google API key free?
**A:** Yes! Google provides a free tier for the Gemini API. Get yours at https://aistudio.google.com/app/apikey

### Q: Does this use real credit bureau data?
**A:** No, this demo uses simulated/mock data. For production, you would integrate with actual credit bureau APIs.

### Q: Can I use this for real loan processing?
**A:** This is a demonstration project. For production use, you would need to:
- Integrate real credit bureau APIs
- Add authentication and security measures
- Comply with financial regulations
- Add proper data encryption

### Q: How do I change the AI model?
**A:** Edit `loan_underwriter/config.py` and change the `model` parameter in `AgentConfig`:
```python
model: str = "gemini-2.0-flash"  # Change to your preferred model
```

### Q: Can I add more agents?
**A:** Yes! Create a new agent file in `loan_underwriter/agents/` following the pattern of existing agents, then add it to the aggregator.

### Q: How do I deploy this to production?
**A:** See the [Production Deployment](#production-deployment) section above. Use Docker or Gunicorn with proper security configurations.

---

## 📚 Additional Resources

- **[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)** - Comprehensive technical documentation
- **[README.md](README.md)** - Quick start guide
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- **Visual Diagrams** (in `docs/` folder):
  - [architecture.svg](docs/architecture.svg) - Fan-Out/Fan-In pattern
  - [data-flow.svg](docs/data-flow.svg) - Processing pipeline
  - [tech-stack.svg](docs/tech-stack.svg) - Technology layers
  - [api-integrations.svg](docs/api-integrations.svg) - External API connections

---

**Happy Underwriting! 🏦🤖**

If this guide helped you, please consider starring the repository!
