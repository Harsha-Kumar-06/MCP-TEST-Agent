# Unified Dockerfile - All Drayvn Agents in One Cloud Run
# Routes: /access-controller, /portfolio-manager, /loan-underwriter, etc.

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including nginx and supervisor
RUN apt-get update && apt-get install -y \
    build-essential \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy all agent folders
COPY access_controller_agent/ /app/access_controller_agent/
COPY portfolio_manager/ /app/portfolio_manager/
COPY campaign_validator_agent/ /app/campaign_validator_agent/
COPY pr_code_reviewer/ /app/pr_code_reviewer/
COPY research_assistant/ /app/research_assistant/
COPY FAN\ out-FAN\ in/ /app/loan_underwriter/
COPY social_media_content_moderation/ /app/content_moderator/
COPY Router\ Pattern/ /app/helpdesk_bot/
COPY social_media_marketing/ /app/social_media_trends/
COPY Swarm\ Pattern/ /app/portfolio_swarm/

# Copy unified deployment configs
COPY unified_deployment/nginx.conf /etc/nginx/nginx.conf
COPY unified_deployment/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY unified_deployment/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install each agent's requirements
RUN for dir in access_controller_agent portfolio_manager campaign_validator_agent \
    pr_code_reviewer research_assistant loan_underwriter content_moderator \
    helpdesk_bot social_media_trends portfolio_swarm; do \
    if [ -f /app/$dir/requirements.txt ]; then \
        pip install --no-cache-dir -r /app/$dir/requirements.txt || true; \
    fi; \
done

# Copy the landing page
COPY unified_deployment/landing_page.py /app/landing_page.py

EXPOSE 8080

# Start supervisor (which starts nginx + all streamlit apps)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
