"""Pydantic models for validation reports and human decisions."""

from pydantic import BaseModel, Field
from datetime import datetime


class CheckResult(BaseModel):
    """Single attribute check result from the AI."""
    attribute: str
    status: str = Field(description="pass, fail, or doubt")
    reasoning: str = Field(default="")


class ValidationReport(BaseModel):
    """Full AI validation report for a post."""
    checks: list[CheckResult] = Field(default_factory=list)
    overall_status: str = Field(description="approved, rejected, or needs_review")
    summary: str = Field(default="")


class HumanDecision(BaseModel):
    """Human reviewer's decision on a flagged post."""
    verdict: str = Field(description="approve or reject")
    feedback: str = Field(default="")
    influencer: str = Field(default="")
    failed_checks: list[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
