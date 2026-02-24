"""
Data models for the MortgageClear system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class ApplicationStatus(Enum):
    """Status of a loan application."""
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    DENIED = "denied"
    MANUAL_REVIEW = "manual_review"


class RiskLevel(Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ApplicantInfo:
    """Applicant personal information."""
    first_name: str
    last_name: str
    ssn: str  # Last 4 digits only for display
    date_of_birth: str
    email: str
    phone: str
    current_address: str
    employment_status: str
    employer_name: str
    years_employed: int
    annual_income: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "ssn_last4": self.ssn[-4:] if len(self.ssn) >= 4 else "****",
            "date_of_birth": self.date_of_birth,
            "email": self.email,
            "phone": self.phone,
            "current_address": self.current_address,
            "employment_status": self.employment_status,
            "employer_name": self.employer_name,
            "years_employed": self.years_employed,
            "annual_income": self.annual_income
        }


@dataclass
class PropertyInfo:
    """Property information for the mortgage."""
    address: str
    city: str
    state: str
    zip_code: str
    property_type: str  # single_family, condo, townhouse, multi_family
    year_built: int
    square_feet: int
    bedrooms: int
    bathrooms: float
    asking_price: float
    down_payment: float
    loan_amount: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "property_type": self.property_type,
            "year_built": self.year_built,
            "square_feet": self.square_feet,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "asking_price": self.asking_price,
            "down_payment": self.down_payment,
            "loan_amount": self.loan_amount
        }


@dataclass
class IncomeDocuments:
    """Income verification documents."""
    w2_provided: bool = False
    tax_returns_years: int = 0
    pay_stubs_months: int = 0
    bank_statements_months: int = 0
    additional_income_sources: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "w2_provided": self.w2_provided,
            "tax_returns_years": self.tax_returns_years,
            "pay_stubs_months": self.pay_stubs_months,
            "bank_statements_months": self.bank_statements_months,
            "additional_income_sources": self.additional_income_sources
        }


@dataclass
class MortgageApplication:
    """Complete mortgage application."""
    application_id: str = field(default_factory=lambda: f"APP-{uuid.uuid4().hex[:8].upper()}")
    applicant: ApplicantInfo = None
    property: PropertyInfo = None
    income_docs: IncomeDocuments = None
    submitted_at: datetime = field(default_factory=datetime.now)
    status: ApplicationStatus = ApplicationStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "application_id": self.application_id,
            "applicant": self.applicant.to_dict() if self.applicant else None,
            "property": self.property.to_dict() if self.property else None,
            "income_docs": self.income_docs.to_dict() if self.income_docs else None,
            "submitted_at": self.submitted_at.isoformat(),
            "status": self.status.value
        }


@dataclass
class CreditAnalysisResult:
    """Result from credit analysis agent."""
    credit_score: int
    debt_to_income_ratio: float
    total_debt: float
    available_credit: float
    credit_history_length_years: int
    late_payments_last_24_months: int
    risk_score: float  # 0-100
    risk_level: RiskLevel
    analysis_summary: str
    recommendations: List[str]
    processing_time_ms: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "credit_score": self.credit_score,
            "debt_to_income_ratio": self.debt_to_income_ratio,
            "total_debt": self.total_debt,
            "available_credit": self.available_credit,
            "credit_history_length_years": self.credit_history_length_years,
            "late_payments_last_24_months": self.late_payments_last_24_months,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "analysis_summary": self.analysis_summary,
            "recommendations": self.recommendations,
            "processing_time_ms": self.processing_time_ms
        }


@dataclass
class PropertyValuationResult:
    """Result from property valuation agent."""
    estimated_value: float
    zillow_estimate: float
    redfin_estimate: float
    tax_assessed_value: float
    comparable_sales: List[Dict[str, Any]]
    valuation_gap_percent: float
    market_trend: str  # appreciating, stable, depreciating
    risk_score: float  # 0-100
    risk_level: RiskLevel
    analysis_summary: str
    recommendations: List[str]
    processing_time_ms: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "estimated_value": self.estimated_value,
            "zillow_estimate": self.zillow_estimate,
            "redfin_estimate": self.redfin_estimate,
            "tax_assessed_value": self.tax_assessed_value,
            "comparable_sales": self.comparable_sales,
            "valuation_gap_percent": self.valuation_gap_percent,
            "market_trend": self.market_trend,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "analysis_summary": self.analysis_summary,
            "recommendations": self.recommendations,
            "processing_time_ms": self.processing_time_ms
        }


@dataclass
class FraudDetectionResult:
    """Result from fraud detection agent."""
    identity_verified: bool
    document_authenticity_score: float
    watchlist_match: bool
    behavioral_risk_score: float
    ip_risk_score: float
    device_risk_score: float
    risk_score: float  # 0-100
    risk_level: RiskLevel
    flags: List[str]
    analysis_summary: str
    recommendations: List[str]
    processing_time_ms: int
    documentation_completeness_score: float = 50.0  # 0-100, completeness of income docs
    documentation_status: str = "unknown"  # complete, adequate, incomplete, insufficient
    identity_consistency_score: float = 100.0  # 0-100, cross-document identity match
    identity_documents_validated: bool = True  # True if all docs belong to same person
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity_verified": self.identity_verified,
            "document_authenticity_score": self.document_authenticity_score,
            "watchlist_match": self.watchlist_match,
            "behavioral_risk_score": self.behavioral_risk_score,
            "ip_risk_score": self.ip_risk_score,
            "device_risk_score": self.device_risk_score,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "flags": self.flags,
            "analysis_summary": self.analysis_summary,
            "recommendations": self.recommendations,
            "processing_time_ms": self.processing_time_ms,
            "documentation_completeness_score": self.documentation_completeness_score,
            "documentation_status": self.documentation_status,
            "identity_consistency_score": self.identity_consistency_score,
            "identity_documents_validated": self.identity_documents_validated
        }



@dataclass
class PersonVerificationResult:
    """Result from person verification agent."""
    identity_consistent: bool
    synthetic_identity_risk: bool
    employment_consistent: bool
    age: int
    person_flags: List[str]
    risk_score: float  # 0-100
    risk_level: RiskLevel
    analysis_summary: str
    recommendations: List[str]
    processing_time_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity_consistent": self.identity_consistent,
            "synthetic_identity_risk": self.synthetic_identity_risk,
            "employment_consistent": self.employment_consistent,
            "age": self.age,
            "person_flags": self.person_flags,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "analysis_summary": self.analysis_summary,
            "recommendations": self.recommendations,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class UnderwritingDecision:
    """Final aggregated underwriting decision."""
    application_id: str
    approval_confidence_score: float  # 0-100
    decision: ApplicationStatus
    credit_analysis: CreditAnalysisResult
    property_valuation: PropertyValuationResult
    fraud_detection: FraudDetectionResult
    person_verification: PersonVerificationResult
    weighted_risk_score: float
    total_processing_time_ms: int
    decision_summary: str
    conditions: List[str]
    next_steps: List[str]
    processed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "application_id": self.application_id,
            "approval_confidence_score": self.approval_confidence_score,
            "decision": self.decision.value,
            "credit_analysis": self.credit_analysis.to_dict(),
            "property_valuation": self.property_valuation.to_dict(),
            "fraud_detection": self.fraud_detection.to_dict(),
            "person_verification": self.person_verification.to_dict(),
            "weighted_risk_score": self.weighted_risk_score,
            "total_processing_time_ms": self.total_processing_time_ms,
            "decision_summary": self.decision_summary,
            "conditions": self.conditions,
            "next_steps": self.next_steps,
            "processed_at": self.processed_at.isoformat(),
        }
