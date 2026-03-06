"""
Aggregator Agent - Combines results from all agents into final decision.
"""

import asyncio
import time
import logging
import json
from typing import Any, Dict

from google.genai import types

from .base_agent import BaseAgent
from .credit_agent import CreditAnalysisAgent
from .property_agent import PropertyValuationAgent
from .fraud_agent import FraudDetectionAgent
from .person_agent import PersonVerificationAgent
from ..config import config, APPROVAL_THRESHOLDS
from ..models import (
    UnderwritingDecision,
    ApplicationStatus,
    CreditAnalysisResult,
    PropertyValuationResult,
    FraudDetectionResult,
    PersonVerificationResult,
)

logger = logging.getLogger(__name__)


class AggregatorAgent(BaseAgent):
    """
    Aggregator Agent that orchestrates the fan-out/fan-in pattern.
    Triggers all analysis agents in parallel and combines their results.
    """
    
    def __init__(self):
        super().__init__(config.aggregator_agent)
        
        # Initialize sub-agents
        self.credit_agent = CreditAnalysisAgent()
        self.property_agent = PropertyValuationAgent()
        self.fraud_agent = FraudDetectionAgent()
        self.person_agent = PersonVerificationAgent()

        logger.info("Aggregator Agent initialized with all sub-agents")
    
    def _define_tools(self) -> list:
        """Define aggregator tools."""
        
        calculate_decision = types.FunctionDeclaration(
            name="calculate_final_decision",
            description="Calculate final underwriting decision based on all four agent risk scores",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "credit_score": types.Schema(type=types.Type.NUMBER, description="Credit risk score 0-100"),
                    "property_score": types.Schema(type=types.Type.NUMBER, description="Property risk score 0-100"),
                    "fraud_score": types.Schema(type=types.Type.NUMBER, description="Fraud risk score 0-100"),
                    "person_score": types.Schema(type=types.Type.NUMBER, description="Person verification risk score 0-100"),
                },
                required=["credit_score", "property_score", "fraud_score", "person_score"]
            )
        )
        
        return types.Tool(function_declarations=[calculate_decision])
    
    def _get_system_instruction(self) -> str:
        return """You are the Master Underwriting Agent for MortgageClear, responsible for final mortgage decisions.

You will receive results from FOUR specialist agents:
- Credit Analysis Agent (35% weight)
- Property Valuation Agent (25% weight)
- Fraud Detection Agent (25% weight)
- Person Verification Agent (15% weight)

Use your calculate_final_decision tool with all four scores, then reason holistically over ALL factors.

IMPORTANT — compensating factors and hard rules:
- A lower credit score offset by a large down payment (>25%) may still merit approval.
- Long, stable employment (10+ years) can compensate for borderline DTI.
- A depreciating market or large valuation gap increases risk regardless of credit.
- Any OFAC/fraud watchlist match → automatic denial, no exceptions.
- Any synthetic identity risk → automatic denial, no exceptions.
- Incomplete documentation → always a condition, never automatic approval.
- Identity inconsistency without explanation → manual_review at minimum.

After calling calculate_final_decision, output ONLY a JSON object:
{
  "decision": "<approved|manual_review|denied>",
  "confidence_score": <number 0-100>,
  "reasoning": "<paragraph explaining decision with specific factors cited>",
  "conditions": ["<specific condition>", "..."],
  "next_steps": ["<step>", "..."]
}

Decision thresholds (after considering compensating factors):
- approved: weighted score >= 82 AND no critical flags
- manual_review: weighted score 58-82 OR borderline factors
- denied: weighted score < 58 OR any critical disqualifying flag

Output ONLY the JSON — no markdown, no extra text."""
    
    async def _fan_out_analysis(self, application_data: Dict[str, Any]) -> tuple:
        """
        Fan-Out Pattern: Execute all agents in parallel using asyncio.
        This dramatically reduces processing time from sequential execution.
        """
        logger.info("Starting fan-out analysis - all agents executing in parallel")
        
        start_time = time.time()
        
        # Create tasks for parallel execution (Fan-Out)
        credit_task = asyncio.create_task(self.credit_agent.analyze(application_data))
        property_task = asyncio.create_task(self.property_agent.analyze(application_data))
        fraud_task = asyncio.create_task(self.fraud_agent.analyze(application_data))
        person_task = asyncio.create_task(self.person_agent.analyze(application_data))

        # Wait for all tasks to complete (Fan-In)
        credit_result, property_result, fraud_result, person_result = await asyncio.gather(
            credit_task, property_task, fraud_task, person_task,
            return_exceptions=True
        )

        # Handle any exceptions
        if isinstance(credit_result, Exception):
            logger.error(f"Credit analysis failed: {credit_result}")
            raise credit_result
        if isinstance(property_result, Exception):
            logger.error(f"Property analysis failed: {property_result}")
            raise property_result
        if isinstance(fraud_result, Exception):
            logger.error(f"Fraud analysis failed: {fraud_result}")
            raise fraud_result
        if isinstance(person_result, Exception):
            logger.error(f"Person verification failed: {person_result}")
            raise person_result

        fan_out_time = int((time.time() - start_time) * 1000)
        logger.info(f"Fan-out analysis completed in {fan_out_time}ms")

        return credit_result, property_result, fraud_result, person_result, fan_out_time
    
    def _calculate_weighted_score(
        self,
        credit_score: float,
        property_score: float,
        fraud_score: float,
        person_score: float,
        fraud_result: "FraudDetectionResult",
        credit_result: "CreditAnalysisResult",
        property_result: "PropertyValuationResult",
        person_result: "PersonVerificationResult",
    ) -> float:
        """Compute weighted score — used as a tool result for the LLM.
        Weights: Credit 35%, Property 25%, Fraud 25%, Person 15%.
        """
        weighted = (
            credit_score * 0.35
            + property_score * 0.25
            + fraud_score * 0.25
            + person_score * 0.15
        )
        # Hard penalties
        if fraud_result.watchlist_match:
            weighted *= 0.5
        if person_result.synthetic_identity_risk:
            weighted *= 0.4
        if credit_result.debt_to_income_ratio > 0.50:
            weighted *= 0.85
        if property_result.valuation_gap_percent > 20:
            weighted *= 0.90
        return round(max(0, min(100, weighted)), 2)

    async def analyze(self, application_data: Dict[str, Any]) -> UnderwritingDecision:
        """
        Orchestrate the entire underwriting process:
        1. FAN-OUT — run Credit, Property, Fraud agents in parallel.
        2. FAN-IN — LLM reasons over all results to make the final decision.
        """
        start_time = time.time()
        application_id = application_data.get("application_id", "UNKNOWN")
        logger.info(f"Starting underwriting analysis for application {application_id}")

        # === FAN-OUT: all three specialist agents run in parallel ===
        credit_result, property_result, fraud_result, person_result, fan_out_time = \
            await self._fan_out_analysis(application_data)

        # ===  FAN-IN: LLM aggregator makes the final decision ===
        logger.info("Fan-in: LLM aggregator reasoning over all results")

        applicant = application_data.get("applicant", {})
        property_info = application_data.get("property", {})
        down_payment = property_info.get("down_payment", 0)
        asking_price = property_info.get("asking_price", 1)
        down_pct = (down_payment / asking_price * 100) if asking_price else 0

        flags_text = (
            "\n  - ".join(fraud_result.flags) if fraud_result.flags else "None"
        )

        person_flags_text = (
            "\n  - ".join(person_result.person_flags) if person_result.person_flags else "None"
        )

        initial_prompt = f"""Make the final underwriting decision for mortgage application {application_id}.

=== CREDIT ANALYSIS ===
Credit Score: {credit_result.credit_score}
DTI Ratio: {credit_result.debt_to_income_ratio * 100:.1f}%
Total Debt: ${credit_result.total_debt:,.0f}
Credit History: {credit_result.credit_history_length_years} years
Late Payments (24 mo): {credit_result.late_payments_last_24_months}
Risk Score: {credit_result.risk_score}/100 ({credit_result.risk_level.value})
Summary: {credit_result.analysis_summary}

=== PROPERTY VALUATION ===
Estimated Value: ${property_result.estimated_value:,.0f}
Asking Price: ${asking_price:,.0f}
Valuation Gap: {property_result.valuation_gap_percent:.1f}%
Market Trend: {property_result.market_trend}
Risk Score: {property_result.risk_score}/100 ({property_result.risk_level.value})
Summary: {property_result.analysis_summary}

=== FRAUD DETECTION ===
Identity Verified: {fraud_result.identity_verified}
Watchlist Match: {fraud_result.watchlist_match}
Doc Authenticity: {fraud_result.document_authenticity_score:.2f}
Doc Completeness: {fraud_result.documentation_completeness_score:.0f}% ({fraud_result.documentation_status})
Fraud Flags:
  - {flags_text}
Risk Score: {fraud_result.risk_score}/100 ({fraud_result.risk_level.value})
Summary: {fraud_result.analysis_summary}

=== PERSON VERIFICATION ===
Age: {person_result.age}
Identity Consistent: {person_result.identity_consistent}
Synthetic Identity Risk: {person_result.synthetic_identity_risk}
Employment Consistent: {person_result.employment_consistent}
Person Flags:
  - {person_flags_text}
Risk Score: {person_result.risk_score}/100 ({person_result.risk_level.value})
Summary: {person_result.analysis_summary}

=== APPLICANT PROFILE ===
Annual Income: ${applicant.get("annual_income", 0):,.0f}
Employment: {applicant.get("employment_status", "N/A")} at \n{applicant.get("employer_name", "N/A")} for {applicant.get("years_employed", 0)} years
Down Payment: ${down_payment:,.0f} ({down_pct:.1f}% of asking price)

INSTRUCTIONS:
1. Call calculate_final_decision with ALL FOUR risk scores to get the weighted score.
2. Consider ALL compensating factors (large down payment, long employment, etc.).
3. Any synthetic_identity_risk=True or watchlist match -> automatic denial.
4. Output your final JSON decision."""

        async def tool_executor(tool_name, args, captured):
            if tool_name == "calculate_final_decision":
                cs = float(args.get("credit_score", credit_result.risk_score))
                ps = float(args.get("property_score", property_result.risk_score))
                fs = float(args.get("fraud_score", fraud_result.risk_score))
                prs = float(args.get("person_score", person_result.risk_score))
                weighted = self._calculate_weighted_score(
                    cs, ps, fs, prs,
                    fraud_result, credit_result, property_result, person_result,
                )
                note_parts = []
                if fraud_result.watchlist_match:
                    note_parts.append("CRITICAL: Watchlist match detected — auto-deny required.")
                if person_result.synthetic_identity_risk:
                    note_parts.append("CRITICAL: Synthetic identity risk detected — auto-deny required.")
                if not note_parts:
                    note_parts.append("Apply compensating factors before finalising decision.")
                return {
                    "weighted_score": weighted,
                    "component_scores": {
                        "credit (35%)": cs,
                        "property (25%)": ps,
                        "fraud (25%)": fs,
                        "person (15%)": prs,
                    },
                    "guidance": (
                        "APPROVED" if weighted >= 82 else
                        "MANUAL_REVIEW" if weighted >= 58 else
                        "DENIED"
                    ),
                    "note": " ".join(note_parts),
                }
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            llm_text, captured, loop_ms = await self._run_agent_loop(
                initial_prompt, tool_executor
            )
            assessment = self._parse_llm_json(llm_text)
        except Exception as exc:
            logger.error(f"Aggregator agent loop failed: {exc}")
            assessment = {}
            captured = {}
            loop_ms = 0

        # Extract weighted score from tool result
        tool_result = captured.get("calculate_final_decision", {})
        confidence_score = float(
            tool_result.get(
                "weighted_score",
                self._calculate_weighted_score(
                    credit_result.risk_score,
                    property_result.risk_score,
                    fraud_result.risk_score,
                    person_result.risk_score,
                    fraud_result, credit_result, property_result, person_result,
                ),
            )
        )
        # Use LLM decision; fall back to threshold-based
        decision_str = assessment.get("decision", "")
        if decision_str not in ("approved", "manual_review", "denied"):
            # Fallback rule
            if fraud_result.watchlist_match or person_result.synthetic_identity_risk:
                decision_str = "denied"
            elif confidence_score >= APPROVAL_THRESHOLDS["auto_approve"]:
                decision_str = "approved"
            elif confidence_score >= APPROVAL_THRESHOLDS["manual_review"]:
                decision_str = "manual_review"
            else:
                decision_str = "denied"

        decision_map = {
            "approved": ApplicationStatus.APPROVED,
            "manual_review": ApplicationStatus.MANUAL_REVIEW,
            "denied": ApplicationStatus.DENIED,
        }
        decision = decision_map.get(decision_str, ApplicationStatus.MANUAL_REVIEW)

        conditions = assessment.get("conditions", [])
        next_steps = assessment.get("next_steps", [])
        decision_summary = assessment.get("reasoning", "")

        # Sensible fallbacks if LLM left these empty
        if not conditions:
            conditions = self._fallback_conditions(credit_result, property_result, fraud_result, person_result)
        if not next_steps:
            next_steps = self._fallback_next_steps(decision, conditions)
        if not decision_summary:
            decision_summary = (
                f"Application {application_id} {decision_str.replace('_', ' ')} "
                f"with a weighted confidence score of {confidence_score:.1f}%. "
                f"{len(conditions)} condition(s) require attention."
            )

        total_processing_time = int((time.time() - start_time) * 1000)
        sequential_estimate = (
            credit_result.processing_time_ms
            + property_result.processing_time_ms
            + fraud_result.processing_time_ms
            + person_result.processing_time_ms
        )
        logger.info(f"Underwriting complete for {application_id}: {decision_str.upper()}")
        logger.info(
            f"Total: {total_processing_time}ms | Sequential estimate: {sequential_estimate}ms | "
            f"Saved: ~{sequential_estimate - fan_out_time}ms via parallel fan-out"
        )

        return UnderwritingDecision(
            application_id=application_id,
            approval_confidence_score=confidence_score,
            decision=decision,
            credit_analysis=credit_result,
            property_valuation=property_result,
            fraud_detection=fraud_result,
            person_verification=person_result,
            weighted_risk_score=confidence_score,
            total_processing_time_ms=total_processing_time,
            decision_summary=decision_summary,
            conditions=conditions,
            next_steps=next_steps,
        )

    def _fallback_conditions(
        self,
        credit_result: CreditAnalysisResult,
        property_result: PropertyValuationResult,
        fraud_result: FraudDetectionResult,
        person_result: "PersonVerificationResult" = None,
    ) -> list:
        """Rule-based conditions used only if LLM returns none."""
        conditions = []
        if credit_result.debt_to_income_ratio > 0.43:
            conditions.append("Require additional income verification or co-borrower")
        if credit_result.late_payments_last_24_months > 2:
            conditions.append("Written explanation for late payments required")
        if credit_result.credit_score < 700:
            conditions.append("Additional reserves verification (6 months PITI)")
        if abs(property_result.valuation_gap_percent) > 10:
            conditions.append("Full appraisal required by certified appraiser")
        if property_result.market_trend == "depreciating":
            conditions.append("Additional 5% down payment recommended")
        if fraud_result.documentation_status in ("insufficient", "incomplete"):
            conditions.append("Submit outstanding income documentation")
        if not fraud_result.identity_verified:
            conditions.append("In-person identity verification required")
        if person_result and not person_result.identity_consistent:
            conditions.append("Identity consistency review required — contact applicant")
        if person_result and not person_result.employment_consistent:
            conditions.append("Employment history verification required")
        return conditions

    def _fallback_next_steps(self, decision: ApplicationStatus, conditions: list) -> list:
        """Rule-based next steps used only if LLM returns none."""
        if decision == ApplicationStatus.APPROVED:
            steps = ["Generate loan commitment letter", "Schedule closing date",
                     "Order title insurance", "Prepare closing documents"]
            if conditions:
                steps.insert(0, "Collect required condition documents")
            return steps
        if decision == ApplicationStatus.MANUAL_REVIEW:
            return ["Route to senior underwriter for review",
                    "Request additional documentation",
                    "Schedule applicant interview if needed",
                    "Complete manual verification checklist"]
        return ["Generate adverse action notice", "Document denial reasons",
                "Provide applicant with credit counseling resources",
                "Allow for appeal submission within 30 days"]
    
    async def process_application(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Public interface for processing a mortgage application.
        Returns the complete underwriting decision as a dictionary.
        """
        result = await self.analyze(application_data)
        return result.to_dict()
