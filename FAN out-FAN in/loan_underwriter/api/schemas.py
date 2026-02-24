"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ApplicantInfoSchema(BaseModel):
    """Schema for applicant information."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    ssn: str = Field(..., min_length=4, max_length=11, description="SSN (last 4 digits or full)")
    date_of_birth: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    current_address: str = Field(..., description="Current residence address")
    employment_status: str = Field(..., description="Employment status (employed, self-employed, retired, etc.)")
    employer_name: str = Field(..., description="Employer name")
    years_employed: int = Field(..., ge=0, description="Years at current employer")
    annual_income: float = Field(..., gt=0, description="Annual gross income")
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Smith",
                "ssn": "1234",
                "date_of_birth": "1985-06-15",
                "email": "john.smith@email.com",
                "phone": "555-123-4567",
                "current_address": "123 Current St, Anytown, ST 12345",
                "employment_status": "employed",
                "employer_name": "Tech Corp Inc",
                "years_employed": 5,
                "annual_income": 125000.00
            }
        }


class PropertyInfoSchema(BaseModel):
    """Schema for property information."""
    address: str = Field(..., description="Property street address")
    city: str = Field(..., description="City")
    state: str = Field(..., min_length=2, max_length=2, description="State (2-letter code)")
    zip_code: str = Field(..., description="ZIP code")
    property_type: str = Field(..., description="Property type (single_family, condo, townhouse, multi_family)")
    year_built: int = Field(..., ge=1800, le=2026, description="Year property was built")
    square_feet: int = Field(..., gt=0, description="Total square footage")
    bedrooms: int = Field(..., ge=0, description="Number of bedrooms")
    bathrooms: float = Field(..., ge=0, description="Number of bathrooms")
    asking_price: float = Field(..., gt=0, description="Property asking price")
    down_payment: float = Field(..., ge=0, description="Down payment amount")
    loan_amount: float = Field(..., gt=0, description="Requested loan amount")
    
    class Config:
        json_schema_extra = {
            "example": {
                "address": "456 Dream Home Ave",
                "city": "Pleasant Valley",
                "state": "CA",
                "zip_code": "90210",
                "property_type": "single_family",
                "year_built": 2015,
                "square_feet": 2500,
                "bedrooms": 4,
                "bathrooms": 2.5,
                "asking_price": 750000.00,
                "down_payment": 150000.00,
                "loan_amount": 600000.00
            }
        }


class IncomeDocsSchema(BaseModel):
    """Schema for income documentation."""
    w2_provided: bool = Field(default=False, description="W2 forms provided")
    tax_returns_years: int = Field(default=0, ge=0, description="Years of tax returns provided")
    pay_stubs_months: int = Field(default=0, ge=0, description="Months of pay stubs provided")
    bank_statements_months: int = Field(default=0, ge=0, description="Months of bank statements provided")
    additional_income_sources: List[str] = Field(default=[], description="Additional income sources")
    
    class Config:
        json_schema_extra = {
            "example": {
                "w2_provided": True,
                "tax_returns_years": 2,
                "pay_stubs_months": 3,
                "bank_statements_months": 3,
                "additional_income_sources": ["rental_income", "investments"]
            }
        }


class ApplicationRequest(BaseModel):
    """Complete mortgage application request schema."""
    application_id: Optional[str] = Field(None, description="Optional application ID (auto-generated if not provided)")
    applicant: ApplicantInfoSchema
    property: PropertyInfoSchema
    income_docs: IncomeDocsSchema
    
    class Config:
        json_schema_extra = {
            "example": {
                "applicant": {
                    "first_name": "John",
                    "last_name": "Smith",
                    "ssn": "1234",
                    "date_of_birth": "1985-06-15",
                    "email": "john.smith@email.com",
                    "phone": "555-123-4567",
                    "current_address": "123 Current St, Anytown, ST 12345",
                    "employment_status": "employed",
                    "employer_name": "Tech Corp Inc",
                    "years_employed": 5,
                    "annual_income": 125000.00
                },
                "property": {
                    "address": "456 Dream Home Ave",
                    "city": "Pleasant Valley",
                    "state": "CA",
                    "zip_code": "90210",
                    "property_type": "single_family",
                    "year_built": 2015,
                    "square_feet": 2500,
                    "bedrooms": 4,
                    "bathrooms": 2.5,
                    "asking_price": 750000.00,
                    "down_payment": 150000.00,
                    "loan_amount": 600000.00
                },
                "income_docs": {
                    "w2_provided": True,
                    "tax_returns_years": 2,
                    "pay_stubs_months": 3,
                    "bank_statements_months": 3,
                    "additional_income_sources": ["rental_income"]
                }
            }
        }


class CreditAnalysisResponse(BaseModel):
    """Response schema for credit analysis results."""
    credit_score: int
    debt_to_income_ratio: float
    total_debt: float
    available_credit: float
    credit_history_length_years: int
    late_payments_last_24_months: int
    risk_score: float
    risk_level: str
    analysis_summary: str
    recommendations: List[str]
    processing_time_ms: int


class PropertyValuationResponse(BaseModel):
    """Response schema for property valuation results."""
    estimated_value: float
    zillow_estimate: float
    redfin_estimate: float
    tax_assessed_value: float
    comparable_sales: List[Dict[str, Any]]
    valuation_gap_percent: float
    market_trend: str
    risk_score: float
    risk_level: str
    analysis_summary: str
    recommendations: List[str]
    processing_time_ms: int


class FraudDetectionResponse(BaseModel):
    """Response schema for fraud detection results."""
    identity_verified: bool
    document_authenticity_score: float
    watchlist_match: bool
    behavioral_risk_score: float
    ip_risk_score: float
    device_risk_score: float
    risk_score: float
    risk_level: str
    flags: List[str]
    analysis_summary: str
    recommendations: List[str]
    processing_time_ms: int




class PersonVerificationResponse(BaseModel):
    """Response schema for person verification results."""
    identity_consistent: bool
    synthetic_identity_risk: bool
    employment_consistent: bool
    age: int
    person_flags: List[str]
    risk_score: float
    risk_level: str
    analysis_summary: str
    recommendations: List[str]
    processing_time_ms: int

class ApplicationResponse(BaseModel):
    """Complete underwriting decision response schema."""
    application_id: str
    approval_confidence_score: float
    decision: str
    credit_analysis: CreditAnalysisResponse
    property_valuation: PropertyValuationResponse
    fraud_detection: FraudDetectionResponse
    person_verification: PersonVerificationResponse
    weighted_risk_score: float
    total_processing_time_ms: int
    decision_summary: str
    conditions: List[str]
    next_steps: List[str]
    processed_at: str


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ApplicationStatusResponse(BaseModel):
    """Simple status response."""
    application_id: str
    status: str
    message: str
