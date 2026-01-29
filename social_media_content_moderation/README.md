# Social Media Content Moderator

## 🟢 High-Level Overview
This agent acts as a Compliance Officer for user-generated content. Instead of a human checking every post, this AI automatically scans posts for violations.

### What it does
It checks three things simultaneously:
1. **Text**: Is the caption hateful, violent, or spammy?
2. **Images**: Does the picture contain adult content or violence?
3. **Links**: Do shared URLs lead to malicious or phishing sites?

**Result**: It returns a concise "Approved" or "Rejected" verdict with reasons.

## ⚙️ Technical Deep Dive
**Architecture**: Parallel Swarm (Map-Reduce Pattern)

### Entry Point (`server.py`)
- A FastAPI server runs a `POST /moderate` endpoint.
- Accepts JSON: `{"text": "...", "image_url": "...", "links": ["..."]}`.

### The Swarm (`agent.py`)
- Uses `ParallelAgent` from the Google ADK.
- This "manager" takes the request and splits it into three tasks running at the same time (parallel).

### Sub-Agents (`sub_agents/`)
- **description_moderator.py**: A text-specialist LLM (Gemini) that reads the caption.
- **image_moderator.py**: A vision-capable LLM that looks at the provided image URL.
- **link_moderator.py**: A specialist that uses Tools. It has a custom python function (`tools.py`) that actually visits the website to scrape its content before deciding if it's safe.

### Tools (`tools.py`)
- Contains `fetch_url_content(url)`. This functional tool allows the AI to "step out" of the chat and browse the web to verify links.

## Setup & Running
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set up environment variables in `.env`:
   ```env
   GOOGLE_API_KEY=your_key
   GEMINI_MODEL=gemini-2.0-flash
   ```
3. Run the server:
   ```bash
   uvicorn server:app --reload
   ```
