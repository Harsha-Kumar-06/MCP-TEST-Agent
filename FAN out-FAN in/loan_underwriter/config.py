"""
Configuration settings for the MortgageClear system.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class AgentConfig:
    """Configuration for individual agents."""
    name: str
    model: str = "gemini-2.0-flash"
    temperature: float = 0.1
    max_tokens: int = 4096


@dataclass
class AppConfig:
    """Main application configuration."""
    # Google AI / Vertex AI settings
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_cloud_project: Optional[str] = os.getenv("GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    # API Keys for external services (mock/real)
    rentcast_api_key: str = os.getenv("RENTCAST_API_KEY", "mock_key")
    attom_api_key: str = os.getenv("ATTOM_API_KEY", "mock_key")
    
    # Credit Bureau Selection (options: equifax, experian, simulated)
    credit_bureau: str = os.getenv("CREDIT_BUREAU", "simulated")
    
    # Experian API (Credit Reports & Financial Data)
    experian_client_id: str = os.getenv("EXPERIAN_CLIENT_ID", "")
    experian_client_secret: str = os.getenv("EXPERIAN_CLIENT_SECRET", "")
    experian_username: str = os.getenv("EXPERIAN_USERNAME", "")
    experian_password: str = os.getenv("EXPERIAN_PASSWORD", "")
    experian_env: str = os.getenv("EXPERIAN_ENV", "sandbox")
    experian_company_id: str = os.getenv("EXPERIAN_COMPANY_ID", "SBMYSQL")
    experian_subscriber_code: str = os.getenv("EXPERIAN_SUBSCRIBER_CODE", "2222222")
    
    # Equifax API (Credit Reports & Financial Data - Alternative)
    equifax_client_id: str = os.getenv("EQUIFAX_CLIENT_ID", "")
    equifax_client_secret: str = os.getenv("EQUIFAX_CLIENT_SECRET", "")
    equifax_env: str = os.getenv("EQUIFAX_ENV", "sandbox")
    equifax_member_number: str = os.getenv("EQUIFAX_MEMBER_NUMBER", "")
    equifax_security_code: str = os.getenv("EQUIFAX_SECURITY_CODE", "")
    
    # Persona API (Fraud Detection & Identity Verification)
    persona_api_key: str = os.getenv("PERSONA_API_KEY", "")
    persona_template_id: str = os.getenv("PERSONA_TEMPLATE_ID", "")
    
    # Application settings
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Agent configurations
    credit_agent: AgentConfig = None
    property_agent: AgentConfig = None
    fraud_agent: AgentConfig = None
    person_agent: AgentConfig = None
    aggregator_agent: AgentConfig = None

    def __post_init__(self):
        self.credit_agent = AgentConfig(name="CreditAnalysisAgent")
        self.property_agent = AgentConfig(name="PropertyValuationAgent")
        self.fraud_agent = AgentConfig(name="FraudDetectionAgent")
        self.person_agent = AgentConfig(name="PersonVerificationAgent")
        self.aggregator_agent = AgentConfig(name="AggregatorAgent")


# Global config instance
config = AppConfig()


# Risk score thresholds
RISK_THRESHOLDS = {
    "credit": {
        "excellent": 750,
        "good": 700,
        "fair": 650,
        "poor": 600
    },
    "property": {
        "low_risk": 0.95,  # Within 5% of asking price
        "medium_risk": 0.85,
        "high_risk": 0.75
    },
    "fraud": {
        "low_risk": 0.9,
        "medium_risk": 0.7,
        "high_risk": 0.5
    }
}

# Approval thresholds
APPROVAL_THRESHOLDS = {
    "auto_approve": 85,
    "manual_review": 60,
    "auto_deny": 40
}
