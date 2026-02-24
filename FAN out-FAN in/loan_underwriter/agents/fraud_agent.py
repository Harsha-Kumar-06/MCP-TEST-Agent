"""
Fraud Detection Agent - Analyzes identity and behavioral patterns for fraud risk.
"""

import asyncio
import random
import time
import logging
import json
from typing import Any, Dict, List

from google.genai import types

from .base_agent import BaseAgent
from ..config import config, RISK_THRESHOLDS
from ..models import FraudDetectionResult, RiskLevel

logger = logging.getLogger(__name__)


class FraudDetectionAgent(BaseAgent):
    """Agent responsible for fraud detection and identity verification."""
    
    def __init__(self):
        super().__init__(config.fraud_agent)
    
    def _define_tools(self) -> list:
        """Define fraud detection tools."""
        
        identity_verify = types.FunctionDeclaration(
            name="verify_identity",
            description="Verify applicant identity against government databases",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "ssn": types.Schema(type=types.Type.STRING, description="Applicant SSN"),
                    "full_name": types.Schema(type=types.Type.STRING, description="Full name"),
                    "dob": types.Schema(type=types.Type.STRING, description="Date of birth"),
                },
                required=["ssn", "full_name", "dob"]
            )
        )
        
        watchlist_check = types.FunctionDeclaration(
            name="check_watchlists",
            description="Check applicant against fraud watchlists and OFAC",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "full_name": types.Schema(type=types.Type.STRING, description="Full name"),
                    "address": types.Schema(type=types.Type.STRING, description="Current address"),
                },
                required=["full_name"]
            )
        )
        
        document_verify = types.FunctionDeclaration(
            name="verify_documents",
            description="Verify authenticity of submitted documents",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "document_type": types.Schema(type=types.Type.STRING, description="Type of document"),
                    "document_hash": types.Schema(type=types.Type.STRING, description="Document hash"),
                },
                required=["document_type"]
            )
        )
        
        behavioral_analysis = types.FunctionDeclaration(
            name="analyze_behavior",
            description="Analyze applicant behavioral patterns for anomalies",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "session_data": types.Schema(type=types.Type.STRING, description="Session behavior data"),
                },
                required=[]
            )
        )
        
        return types.Tool(function_declarations=[identity_verify, watchlist_check, document_verify, behavioral_analysis])
    
    def _get_system_instruction(self) -> str:
        return """You are a Fraud Detection Agent for mortgage underwriting.

You MUST use ALL four tools to gather data before producing your assessment.

Tool usage order:
1. Call verify_identity — confirm the applicant's identity.
2. Call check_watchlists — screen for OFAC, fraud lists, PEP status.
3. Call verify_documents — assess income document authenticity and completeness.
4. Call analyze_behavior — review behavioral session patterns.

After all four tool results, reason over every finding and output ONLY a JSON object:
{
  "risk_score": <integer 0-100, higher = less fraud risk / safer>,
  "risk_level": "<low|medium|high|critical>",
  "identity_verified": <true|false>,
  "fraud_flags": ["<specific flag>", "..."],
  "analysis_summary": "<2-3 sentence professional summary>",
  "recommendations": ["<specific recommendation>", "..."]
}

Be especially vigilant for: identity theft, synthetic identity, document tampering,
application inconsistencies, watchlist matches, and behavioral anomalies.
Output ONLY the JSON — no markdown, no extra text."""
    
    async def _simulate_identity_verification(self, applicant_data: Dict) -> Dict[str, Any]:
        """Simulate identity verification check."""
        await asyncio.sleep(random.uniform(0.3, 0.7))
        
        # 95% of applications pass identity verification
        verified = random.random() < 0.95
        
        return {
            "verified": verified,
            "ssn_match": verified,
            "name_match": verified,
            "dob_match": verified,
            "address_history_match": random.random() < 0.90,
            "confidence_score": round(random.uniform(0.85 if verified else 0.3, 0.99 if verified else 0.6), 2),
            "verification_source": "LexisNexis",
            "last_verified": "2026-02-12"
        }
    
    async def _simulate_watchlist_check(self, applicant_data: Dict) -> Dict[str, Any]:
        """Simulate watchlist check."""
        await asyncio.sleep(random.uniform(0.2, 0.5))
        
        # 0.5% chance of watchlist match (for realistic simulation)
        has_match = random.random() < 0.005
        
        return {
            "ofac_match": has_match,
            "fraud_watchlist_match": random.random() < 0.01,
            "pep_match": random.random() < 0.02,  # Politically Exposed Person
            "adverse_media": random.random() < 0.03,
            "matches": [] if not has_match else [{"list": "Sample Watchlist", "match_score": 0.85}]
        }
    
    def _calculate_documentation_completeness(self, income_docs: Dict, applicant: Dict) -> Dict[str, Any]:
        """Calculate documentation completeness score based on provided documents."""
        
        w2_provided = income_docs.get("w2_provided", False)
        tax_returns_years = income_docs.get("tax_returns_years", 0)
        pay_stubs_months = income_docs.get("pay_stubs_months", 0)
        bank_statements_months = income_docs.get("bank_statements_months", 0)
        employment_status = applicant.get("employment_status", "employed")
        
        # Calculate completeness score (0-100)
        score = 0
        flags = []
        requirements_met = []
        requirements_missing = []
        
        # W2 verification (25 points for employed, 0 for self-employed)
        if employment_status in ["employed", "retired"]:
            if w2_provided:
                score += 25
                requirements_met.append("W2 provided")
            else:
                flags.append("W2 not provided for employed applicant")
                requirements_missing.append("W2 required for employed applicants")
        else:
            # Self-employed doesn't need W2
            score += 15  # Partial credit
            requirements_met.append("W2 not required (self-employed)")
        
        # Tax returns verification (30 points max)
        if employment_status == "self-employed":
            # Self-employed needs 3 years
            if tax_returns_years >= 3:
                score += 30
                requirements_met.append(f"Tax returns: {tax_returns_years} years (meets 3-year requirement)")
            elif tax_returns_years >= 2:
                score += 20
                flags.append("Self-employed: Only 2 years tax returns (3 recommended)")
                requirements_missing.append("Self-employed applicants should provide 3 years tax returns")
            elif tax_returns_years >= 1:
                score += 10
                flags.append("Insufficient tax returns for self-employed (need 3 years)")
                requirements_missing.append("Self-employed: minimum 3 years tax returns required")
            else:
                flags.append("No tax returns provided for self-employed applicant")
                requirements_missing.append("CRITICAL: Self-employed must provide tax returns")
        else:
            # Employed needs 2 years
            if tax_returns_years >= 2:
                score += 30
                requirements_met.append(f"Tax returns: {tax_returns_years} years provided")
            elif tax_returns_years >= 1:
                score += 15
                flags.append("Only 1 year tax returns (2 years recommended)")
                requirements_missing.append("2 years tax returns recommended")
            else:
                score += 0
                flags.append("No tax returns provided")
                requirements_missing.append("Tax returns strongly recommended")
        
        # Pay stubs verification (25 points max)
        if employment_status in ["employed"]:
            if pay_stubs_months >= 3:
                score += 25
                requirements_met.append(f"Pay stubs: {pay_stubs_months} months provided")
            elif pay_stubs_months >= 2:
                score += 18
                flags.append("Only 2 months pay stubs (3 months recommended)")
                requirements_missing.append("3 months of pay stubs recommended")
            elif pay_stubs_months >= 1:
                score += 10
                flags.append("Insufficient pay stubs (only 1 month)")
                requirements_missing.append("Minimum 2 months pay stubs required")
            else:
                flags.append("No pay stubs provided for employed applicant")
                requirements_missing.append("Pay stubs required for employed applicants")
        else:
            # Self-employed/retired don't need pay stubs
            score += 15
            requirements_met.append("Pay stubs not required for employment type")
        
        # Bank statements verification (20 points max)
        if bank_statements_months >= 6:
            score += 20
            requirements_met.append(f"Bank statements: {bank_statements_months} months provided")
        elif bank_statements_months >= 3:
            score += 12
            flags.append("Only 3-5 months bank statements (6 months recommended)")
            requirements_missing.append("6 months bank statements recommended for full verification")
        elif bank_statements_months >= 1:
            score += 5
            flags.append("Insufficient bank statements")
            requirements_missing.append("Minimum 3 months bank statements required")
        else:
            flags.append("No bank statements provided")
            requirements_missing.append("Bank statements required for income verification")
        
        # Determine overall status
        if score >= 85:
            status = "complete"
        elif score >= 60:
            status = "adequate"
        elif score >= 40:
            status = "incomplete"
        else:
            status = "insufficient"
        
        return {
            "completeness_score": score,
            "status": status,
            "flags": flags,
            "requirements_met": requirements_met,
            "requirements_missing": requirements_missing,
            "documents_provided": {
                "w2": w2_provided,
                "tax_returns_years": tax_returns_years,
                "pay_stubs_months": pay_stubs_months,
                "bank_statements_months": bank_statements_months
            },
            "employment_type": employment_status
        }
    
    async def _simulate_document_verification(self, income_docs: Dict, applicant: Dict = None) -> Dict[str, Any]:
        """Simulate document authenticity verification with completeness check."""
        await asyncio.sleep(random.uniform(0.4, 0.8))
        
        if applicant is None:
            applicant = {}
        
        # Calculate documentation completeness
        completeness = self._calculate_documentation_completeness(income_docs, applicant)
        
        # Authenticity score influenced by completeness
        base_authenticity = random.uniform(0.75, 0.99)
        # If documentation is incomplete, slightly lower confidence in authenticity
        completeness_factor = completeness["completeness_score"] / 100
        authenticity_score = base_authenticity * (0.7 + 0.3 * completeness_factor)
        
        # Build documents analyzed list based on what was provided
        documents_analyzed = []
        if income_docs.get("w2_provided"):
            documents_analyzed.append({"type": "W2", "score": round(random.uniform(0.85, 0.99), 2), "verified": True})
        if income_docs.get("tax_returns_years", 0) > 0:
            for i in range(min(income_docs.get("tax_returns_years", 0), 3)):
                documents_analyzed.append({
                    "type": f"Tax Return Year {i+1}", 
                    "score": round(random.uniform(0.85, 0.99), 2),
                    "verified": True
                })
        if income_docs.get("pay_stubs_months", 0) > 0:
            documents_analyzed.append({
                "type": f"Pay Stubs ({income_docs.get('pay_stubs_months')} months)", 
                "score": round(random.uniform(0.85, 0.99), 2),
                "verified": True
            })
        if income_docs.get("bank_statements_months", 0) > 0:
            documents_analyzed.append({
                "type": f"Bank Statements ({income_docs.get('bank_statements_months')} months)", 
                "score": round(random.uniform(0.85, 0.99), 2),
                "verified": True
            })
        
        return {
            "authenticity_score": round(authenticity_score, 2),
            "tampering_detected": authenticity_score < 0.80,
            "metadata_consistent": random.random() < 0.95,
            "font_analysis_pass": random.random() < 0.95,
            "digital_signature_valid": random.random() < 0.90,
            "documents_analyzed": documents_analyzed,
            "documentation_completeness": completeness
        }
    
    async def _simulate_behavioral_analysis(self) -> Dict[str, Any]:
        """Simulate behavioral pattern analysis."""
        await asyncio.sleep(random.uniform(0.2, 0.4))
        
        return {
            "ip_risk_score": round(random.uniform(0.7, 0.98), 2),
            "device_risk_score": round(random.uniform(0.75, 0.99), 2),
            "velocity_check_pass": random.random() < 0.95,
            "typing_pattern_normal": random.random() < 0.92,
            "session_anomalies": random.randint(0, 3),
            "geolocation_consistent": random.random() < 0.90,
            "time_on_application_minutes": random.randint(10, 60),
            "form_fill_pattern": "normal" if random.random() < 0.90 else "suspicious"
        }
    
    def _normalize_name(self, name: str) -> str:
        """Normalize a name for comparison (lowercase, remove extra spaces, handle common variations)."""
        if not name:
            return ""
        # Lowercase, strip, collapse multiple spaces
        normalized = " ".join(name.lower().strip().split())
        # Remove common suffixes
        for suffix in [" jr", " sr", " ii", " iii", " iv"]:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
        return normalized
    
    def _names_match(self, name1: str, name2: str) -> tuple:
        """Check if two names match, returning (match_score, is_match)."""
        n1 = self._normalize_name(name1)
        n2 = self._normalize_name(name2)
        
        if not n1 or not n2:
            return (0, False)
        
        # Exact match
        if n1 == n2:
            return (100, True)
        
        # Check if one contains the other (partial match for "John Smith" vs "John A Smith")
        n1_parts = set(n1.split())
        n2_parts = set(n2.split())
        
        # Calculate overlap
        common = n1_parts.intersection(n2_parts)
        total = n1_parts.union(n2_parts)
        
        if len(total) == 0:
            return (0, False)
            
        overlap_score = (len(common) / len(total)) * 100
        
        # If at least 50% of name parts match, consider it a match
        # (handles "John Smith" vs "John Allen Smith" or "J. Smith" vs "John Smith")
        is_match = overlap_score >= 50 or (len(common) >= 2)
        
        return (overlap_score, is_match)
    
    def _validate_document_identity_consistency(self, income_docs: Dict, applicant: Dict) -> Dict[str, Any]:
        """
        Validate that all uploaded documents belong to the same person.
        Cross-references names and SSN across W2, tax returns, pay stubs, and bank statements.
        """
        applicant_name = f"{applicant.get('first_name', '')} {applicant.get('last_name', '')}".strip()
        applicant_ssn_last4 = applicant.get('ssn', '')[-4:] if applicant.get('ssn') else None
        
        # Get uploaded documents analysis data
        uploaded_docs = income_docs.get("uploaded_documents", {})
        
        # Collect identity info from each document type
        document_identities = []
        identity_sources = []
        
        # W2 documents
        w2_docs = uploaded_docs.get("w2", [])
        for doc in w2_docs:
            if isinstance(doc, dict) and doc.get("analysis"):
                analysis = doc["analysis"]
                name = analysis.get("employee_name", "")
                ssn_last4 = analysis.get("employee_ssn_last4", "")
                if name or ssn_last4:
                    document_identities.append({
                        "source": "W2",
                        "name": name,
                        "ssn_last4": ssn_last4,
                        "filename": doc.get("filename", "unknown")
                    })
                    identity_sources.append("W2")
        
        # Tax returns
        tax_docs = uploaded_docs.get("tax_returns", [])
        for doc in tax_docs:
            if isinstance(doc, dict) and doc.get("analysis"):
                analysis = doc["analysis"]
                # Tax returns might have "taxpayer_name" or similar
                name = analysis.get("taxpayer_name", "") or analysis.get("name", "")
                ssn_last4 = analysis.get("ssn_last4", "")
                if name or ssn_last4:
                    document_identities.append({
                        "source": "Tax Return",
                        "name": name,
                        "ssn_last4": ssn_last4,
                        "filename": doc.get("filename", "unknown")
                    })
                    identity_sources.append("Tax Return")
        
        # Pay stubs
        pay_stub_docs = uploaded_docs.get("pay_stubs", [])
        for doc in pay_stub_docs:
            if isinstance(doc, dict) and doc.get("analysis"):
                analysis = doc["analysis"]
                name = analysis.get("employee_name", "")
                if name:
                    document_identities.append({
                        "source": "Pay Stub",
                        "name": name,
                        "ssn_last4": "",
                        "filename": doc.get("filename", "unknown")
                    })
                    identity_sources.append("Pay Stub")
        
        # Bank statements
        bank_docs = uploaded_docs.get("bank_statements", [])
        for doc in bank_docs:
            if isinstance(doc, dict) and doc.get("analysis"):
                analysis = doc["analysis"]
                name = analysis.get("account_holder", "")
                if name:
                    document_identities.append({
                        "source": "Bank Statement",
                        "name": name,
                        "ssn_last4": "",
                        "filename": doc.get("filename", "unknown")
                    })
                    identity_sources.append("Bank Statement")
        
        # Validation results
        flags = []
        warnings = []
        all_names_match = True
        all_ssn_match = True
        identity_score = 100
        
        if not document_identities:
            return {
                "validated": True,
                "score": 100,
                "message": "No uploaded documents to validate",
                "flags": [],
                "warnings": ["No uploaded documents with extractable identity information"],
                "documents_checked": 0,
                "identity_sources": []
            }
        
        # Check each document against applicant info
        for doc_identity in document_identities:
            doc_name = doc_identity["name"]
            doc_ssn = doc_identity["ssn_last4"]
            source = doc_identity["source"]
            filename = doc_identity["filename"]
            
            # Name check
            if doc_name:
                name_score, name_matches = self._names_match(applicant_name, doc_name)
                if not name_matches:
                    all_names_match = False
                    identity_score -= 25
                    flags.append(f"NAME MISMATCH: {source} ({filename}) shows '{doc_name}' but applicant is '{applicant_name}'")
                elif name_score < 80:
                    warnings.append(f"Name variation in {source}: '{doc_name}' vs '{applicant_name}' (score: {name_score:.0f}%)")
            
            # SSN check (only if document has SSN)
            if doc_ssn and applicant_ssn_last4:
                if doc_ssn != applicant_ssn_last4:
                    all_ssn_match = False
                    identity_score -= 35
                    flags.append(f"SSN MISMATCH: {source} ({filename}) shows SSN ending in '{doc_ssn}' but applicant SSN ends in '{applicant_ssn_last4}'")
        
        # Cross-check documents against each other
        if len(document_identities) >= 2:
            for i, doc1 in enumerate(document_identities):
                for doc2 in document_identities[i+1:]:
                    if doc1["name"] and doc2["name"]:
                        score, matches = self._names_match(doc1["name"], doc2["name"])
                        if not matches:
                            flags.append(f"DOCUMENT NAME CONFLICT: {doc1['source']} shows '{doc1['name']}' but {doc2['source']} shows '{doc2['name']}'")
                            identity_score -= 20
                    
                    if doc1["ssn_last4"] and doc2["ssn_last4"]:
                        if doc1["ssn_last4"] != doc2["ssn_last4"]:
                            flags.append(f"DOCUMENT SSN CONFLICT: {doc1['source']} and {doc2['source']} have different SSN last 4 digits")
                            identity_score -= 30
        
        identity_score = max(0, identity_score)
        
        return {
            "validated": len(flags) == 0,
            "score": identity_score,
            "message": "All documents belong to the same person" if len(flags) == 0 else f"Identity inconsistencies detected across documents",
            "flags": flags,
            "warnings": warnings,
            "documents_checked": len(document_identities),
            "identity_sources": list(set(identity_sources)),
            "all_names_consistent": all_names_match,
            "all_ssn_consistent": all_ssn_match
        }
    
    def _calculate_fraud_risk_score(self, fraud_data: Dict) -> tuple:
        """Calculate fraud risk score (0-100, higher is safer)."""
        score = 100.0
        flags = []
        
        # Identity verification (35% weight)
        if not fraud_data["identity"]["verified"]:
            score -= 40
            flags.append("Identity verification failed")
        elif fraud_data["identity"]["confidence_score"] < 0.9:
            score -= 15
            flags.append("Low identity confidence score")
        
        # Watchlist checks (25% weight)
        watchlist = fraud_data["watchlist"]
        if watchlist["ofac_match"]:
            score -= 50
            flags.append("OFAC watchlist match")
        if watchlist["fraud_watchlist_match"]:
            score -= 30
            flags.append("Fraud watchlist match")
        if watchlist["pep_match"]:
            score -= 10
            flags.append("Politically Exposed Person flag")
        if watchlist["adverse_media"]:
            score -= 5
            flags.append("Adverse media found")
        
        # Document verification (25% weight)
        docs = fraud_data["documents"]
        if docs["tampering_detected"]:
            score -= 35
            flags.append("Document tampering detected")
        elif docs["authenticity_score"] < 0.85:
            score -= 15
            flags.append("Low document authenticity score")
        if not docs["metadata_consistent"]:
            score -= 10
            flags.append("Document metadata inconsistent")
        
        # Documentation completeness (new scoring)
        if "documentation_completeness" in docs:
            doc_completeness = docs["documentation_completeness"]
            completeness_score = doc_completeness.get("completeness_score", 50)
            
            if completeness_score < 40:
                score -= 20
                flags.append("CRITICAL: Insufficient income documentation")
            elif completeness_score < 60:
                score -= 12
                flags.append("Incomplete income documentation")
            elif completeness_score < 85:
                score -= 5
                flags.append("Some documentation missing")
            
            # Add specific documentation flags
            for flag in doc_completeness.get("flags", [])[:3]:  # Limit to 3 flags
                if flag not in flags:
                    flags.append(flag)
        
        # Behavioral analysis (15% weight)
        behavior = fraud_data["behavioral"]
        if behavior["ip_risk_score"] < 0.8:
            score -= 10
            flags.append("High-risk IP address")
        if behavior["device_risk_score"] < 0.8:
            score -= 8
            flags.append("High-risk device fingerprint")
        if not behavior["velocity_check_pass"]:
            score -= 12
            flags.append("Velocity check failed - multiple applications")
        if behavior["form_fill_pattern"] == "suspicious":
            score -= 8
            flags.append("Suspicious form fill pattern")
        if behavior["session_anomalies"] > 2:
            score -= 5
            flags.append("Multiple session anomalies detected")
        
        return max(0, min(100, score)), flags
    
    async def _execute_tool(
        self, tool_name: str, args: dict, captured: dict,
        applicant: dict, income_docs: dict
    ) -> dict:
        """Execute a fraud detection tool and return its result."""
        if tool_name == "verify_identity":
            return await self._simulate_identity_verification(applicant)

        if tool_name == "check_watchlists":
            return await self._simulate_watchlist_check(applicant)

        if tool_name == "verify_documents":
            result = await self._simulate_document_verification(income_docs, applicant)
            # Also run cross-document identity validation
            identity_consistency = self._validate_document_identity_consistency(
                income_docs, applicant
            )
            result["identity_consistency"] = identity_consistency
            return result

        if tool_name == "analyze_behavior":
            return await self._simulate_behavioral_analysis()

        return {"error": f"Unknown tool: {tool_name}"}

    async def analyze(self, application_data: Dict[str, Any]) -> FraudDetectionResult:
        """
        Fraud detection analysis — the LLM drives all four tool calls and
        reasons over every result to identify flags and produce a risk assessment.
        """
        start_time = time.time()
        app_id = application_data.get("application_id", "N/A")
        logger.info(f"Starting fraud detection for application {app_id}")

        applicant = application_data.get("applicant", {})
        income_docs = application_data.get("income_docs", {})

        doc_summary_lines = [
            f"  - W2 Forms: {'Yes' if income_docs.get('w2_provided') else 'No'}",
            f"  - Tax Returns: {income_docs.get('tax_returns_years', 0)} years",
            f"  - Pay Stubs: {income_docs.get('pay_stubs_months', 0)} months",
            f"  - Bank Statements: {income_docs.get('bank_statements_months', 0)} months",
        ]

        initial_prompt = f"""Conduct a fraud risk assessment for this mortgage applicant.

Applicant: {applicant.get('first_name', '')} {applicant.get('last_name', '')}
SSN (last 4): {applicant.get('ssn', '****')}
Date of Birth: {applicant.get('date_of_birth', 'N/A')}
Address: {applicant.get('current_address', 'N/A')}
Employment: {applicant.get('employment_status', 'N/A')} at \
{applicant.get('employer_name', 'N/A')} for {applicant.get('years_employed', 0)} years

Income Documentation Provided:
{chr(10).join(doc_summary_lines)}

INSTRUCTIONS:
1. Call verify_identity to confirm the applicant's identity.
2. Call check_watchlists to screen for OFAC / fraud / PEP matches.
3. Call verify_documents to assess document authenticity and completeness.
4. Call analyze_behavior to check behavioral session patterns.
5. After ALL four results, synthesize your findings into the JSON risk assessment."""

        async def tool_executor(tool_name, args, captured):
            return await self._execute_tool(
                tool_name, args, captured, applicant, income_docs
            )

        try:
            llm_text, captured, loop_ms = await self._run_agent_loop(
                initial_prompt, tool_executor
            )
            assessment = self._parse_llm_json(llm_text)
        except Exception as exc:
            logger.error(f"Agent loop failed for fraud detection: {exc}")
            assessment = {}
            captured = {}
            loop_ms = int((time.time() - start_time) * 1000)

        # Extract captured data from each tool
        identity_data = captured.get("verify_identity", {})
        watchlist_data = captured.get("check_watchlists", {})
        document_data = captured.get("verify_documents", {})
        behavioral_data = captured.get("analyze_behavior", {})

        # Fallback direct fetches if LLM skipped any tool
        if not identity_data:
            logger.warning("LLM skipped verify_identity — fetching directly")
            identity_data = await self._simulate_identity_verification(applicant)
        if not watchlist_data:
            watchlist_data = await self._simulate_watchlist_check(applicant)
        if not document_data:
            document_data = await self._simulate_document_verification(income_docs, applicant)
            document_data["identity_consistency"] = self._validate_document_identity_consistency(
                income_docs, applicant
            )
        if not behavioral_data:
            behavioral_data = await self._simulate_behavioral_analysis()

        identity_consistency = document_data.get("identity_consistency", {})

        # Build combined fraud_data dict for rule-based fallback scorer
        fraud_data = {
            "identity": identity_data,
            "watchlist": watchlist_data,
            "documents": document_data,
            "behavioral": behavioral_data,
        }

        # Use LLM risk score; fall back to rule-based if missing
        risk_score = float(assessment.get("risk_score", 0))
        flags = assessment.get("fraud_flags", [])
        if not isinstance(flags, list):
            flags = [flags] if flags else []

        if risk_score == 0:
            risk_score, flags = self._calculate_fraud_risk_score(fraud_data)
            # Apply identity-consistency penalties
            for flag in identity_consistency.get("flags", []):
                if flag not in flags:
                    flags.insert(0, flag)
                    risk_score -= 15
            risk_score = max(0, min(100, risk_score))

        risk_level_str = assessment.get(
            "risk_level", self._calculate_risk_level(risk_score)
        )
        try:
            risk_level = RiskLevel(risk_level_str)
        except ValueError:
            risk_level = RiskLevel(self._calculate_risk_level(risk_score))

        identity_verified = assessment.get(
            "identity_verified", identity_data.get("verified", False)
        )
        summary = assessment.get(
            "analysis_summary",
            f"Fraud risk score: {risk_score:.0f}. {len(flags)} flag(s) identified."
        )
        recommendations = assessment.get("recommendations", ["Review flagged items"])
        if not isinstance(recommendations, list):
            recommendations = [recommendations]

        doc_completeness = document_data.get("documentation_completeness", {})
        doc_score = doc_completeness.get("completeness_score", 50.0)
        doc_status = doc_completeness.get("status", "unknown")
        identity_consistency_score = identity_consistency.get("score", 100.0)
        identity_docs_validated = identity_consistency.get("validated", True)

        processing_time = int((time.time() - start_time) * 1000)

        return FraudDetectionResult(
            identity_verified=identity_verified,
            document_authenticity_score=document_data.get("authenticity_score", 0.85),
            watchlist_match=(
                watchlist_data.get("ofac_match", False) or
                watchlist_data.get("fraud_watchlist_match", False)
            ),
            behavioral_risk_score=round(
                (behavioral_data.get("ip_risk_score", 0.85) +
                 behavioral_data.get("device_risk_score", 0.85)) / 2 * 100, 2
            ),
            ip_risk_score=round(behavioral_data.get("ip_risk_score", 0.85) * 100, 2),
            device_risk_score=round(behavioral_data.get("device_risk_score", 0.85) * 100, 2),
            risk_score=round(risk_score, 2),
            risk_level=risk_level,
            flags=flags,
            analysis_summary=summary,
            recommendations=recommendations,
            processing_time_ms=processing_time,
            documentation_completeness_score=doc_score,
            documentation_status=doc_status,
            identity_consistency_score=identity_consistency_score,
            identity_documents_validated=identity_docs_validated,
        )
