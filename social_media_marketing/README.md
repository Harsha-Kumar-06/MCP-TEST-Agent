# Social Media Trends Agent

A single agent system for aggregating and analyzing trends across social media platforms (Instagram, TikTok, and YouTube). This agent researches trending topics, popular content creators, and provides insights for marketing decisions about ad placement and influencer partnerships.

## Features

- **Multi-Platform Analysis**: Monitors trends across Instagram, TikTok, and YouTube
- **Content Creator Discovery**: Identifies rising and established content creators gaining attention
- **Trend Intelligence**: Researches trending topics, hashtags, and content themes
- **Flexible Filtering**: Filter trends by platform, category, or country
- **Marketing Insights**: Provides relevant metrics and audience profiles for campaign planning

## Requirements

- Python 3.12+
- Google ADK (>=1.23.0)
- Uvicorn (>=0.40.0)
- Google API credentials (for search and Gemini model access)

## Installation

1. **Clone the repository**:
   ```bash
   cd social-media-marketing
   ```

2. **Install dependencies** using `uv` (recommended):
   ```bash
   uv sync
   ```

   Or using pip:
   ```bash
   pip install -e .
   ```

3. **Set up environment variables**:

   Create a `.env` file in the project root with the following variables:

   ```bash
   # Required
   GOOGLE_API_KEY=your_google_api_key_here
   
   # Optional
   ROOT_AGENT_MODEL=gemini-2.5-flash  # Default model (can be changed)
   PORT=8080                           # Server port (default: 8080)
   SERVE_WEB_INTERFACE=False          # Enable web interface (True/False)
   SESSION_SERVICE_URI=                # Optional session service URL
   ```

   To get a Google API key:
   - Visit [Google AI Studio](https://aistudio.google.com/apikey)
   - Create an API key with access to Google Search and Gemini APIs

## Running the Application

### Start the Agent Server

```bash
python main.py
```

The agent will start on `http://localhost:8080` by default. You can change the port by setting the `PORT` environment variable.

### Using the Web Interface (Optional)

To enable the web interface, set `SERVE_WEB_INTERFACE=True` in your `.env` file:

```bash
SERVE_WEB_INTERFACE=True python main.py
```

## API Endpoints

The application provides REST endpoints through FastAPI. Once running, you can access:

### Example Usage

Or use curl to query the agent:

1. Setup a session
```bash
curl -X POST "http://localhost:8080/apps/social_media_marketing/users/{{userId}}/sessions/{{sessionId}}" \
  -H "Content-Type: application/json" \
```

2. Query the agent
```bash
curl -X POST "http://localhost:8080/run" \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "social_media_agent",
    "userId": "{{userId}}",
    "sessionId": "{{sessionId}}",
    "newMessage": {
        "role": "user",
        "parts": [{ "text": "Get latest trends on TikTok for France in fashion category"}]
    }
}'
```

## Project Structure

```
social-media-marketing/
├── main.py                      # Entry point - starts the FastAPI server
├── pyproject.toml              # Project configuration and dependencies
├── README.md                   # This file
├── .env                        # Environment variables (create this)
└── social_media_marketing/
    ├── __init__.py
    └── agent.py                # Agent definition and configuration
```

## Troubleshooting


### Missing Dependencies

Ensure all dependencies are installed:

```bash
uv sync
```

Or update existing installations:

```bash
pip install --upgrade google-adk uvicorn python-dotenv
```

### API Key Issues

- Verify your `GOOGLE_API_KEY` is correctly set in the `.env` file
- Ensure the API key has access to Google Search and Gemini APIs
- Check that the key hasn't been revoked or expired

## License

This project is part of the Google ADK ecosystem.

## Support

For issues with Google ADK, visit the [Google ADK Documentation](https://ai.google.dev/adk).
