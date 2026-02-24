"""
Person Verification Agent - Detects person-level fraud and identity inconsistencies.
"""

import time
import logging
from datetime import datetime, date
from typing import Any, Dict

from google.genai import types

from .base_agent import BaseAgent
from ..config import config
from ..models import PersonVerificationResult, RiskLevel

logger = logging.getLogger(__name__)


class PersonVerificationAgent(BaseAgent):
    """
    Person Verification Agent that detects synthetic identities,
    employment inconsistencies, and cross-field plausibility issues.
    Runs as part of the Fan-Out/Fan-In parallel pipeline.
    """

    def __init__(self):
        super().__init__(config.person_agent)
        logger.info("Person Verification Agent initialized")

    def _define_tools(self) -> list:
        """Define person verification tools."""

        verify_identity = types.FunctionDeclaration(
            name="verify_person_identity",
            description="Verify basic identity fields: age from DOB, name validity, SSN last-4 format",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "first_name": types.Schema(type=types.Type.STRING),
                    "last_name": types.Schema(type=types.Type.STRING),
                    "date_of_birth": types.Schema(
                        type=types.Type.STRING, description="YYYY-MM-DD format"
                    ),
                    "ssn_last4": types.Schema(
                        type=types.Type.STRING, description="Last 4 digits of SSN"
                    ),
                },
                required=["first_name", "last_name", "date_of_birth", "ssn_last4"],
            ),
        )

        check_employment = types.FunctionDeclaration(
            name="check_employment_consistency",
            description=(
                "Validate years employed vs applicant age, income vs employment type plausibility"
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "age": types.Schema(
                        type=types.Type.NUMBER, description="Applicant age in years"
                    ),
                    "years_employed": types.Schema(type=types.Type.NUMBER),
                    "employment_status": types.Schema(type=types.Type.STRING),
                    "annual_income": types.Schema(type=types.Type.NUMBER),
                    "employer_name": types.Schema(type=types.Type.STRING),
                },
                required=[
                    "age",
                    "years_employed",
                    "employment_status",
                    "annual_income",
                    "employer_name",
                ],
            ),
        )

        detect_synthetic = types.FunctionDeclaration(
            name="detect_synthetic_identity",
            description=(
                "Scan for synthetic identity red flags: "
                "improbable data combinations, mismatched patterns"
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "age": types.Schema(type=types.Type.NUMBER),
                    "annual_income": types.Schema(type=types.Type.NUMBER),
                    "years_employed": types.Schema(type=types.Type.NUMBER),
                    "asking_price": types.Schema(type=types.Type.NUMBER),
                    "down_payment": types.Schema(type=types.Type.NUMBER),
                    "ssn_last4": types.Schema(type=types.Type.STRING),
                },
                required=[
                    "age",
                    "annual_income",
                    "years_employed",
                    "asking_price",
                    "down_payment",
                    "ssn_last4",
                ],
            ),
        )

        verify_consistency = types.FunctionDeclaration(
            name="verify_application_consistency",
            description=(
                "Cross-check application fields for plausibility: "
                "address format, email, phone, documentation coverage"
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "current_address": types.Schema(type=types.Type.STRING),
                    "property_state": types.Schema(type=types.Type.STRING),
                    "email": types.Schema(type=types.Type.STRING),
                    "phone": types.Schema(type=types.Type.STRING),
                    "annual_income": types.Schema(type=types.Type.NUMBER),
                    "w2_provided": types.Schema(type=types.Type.BOOLEAN),
                    "tax_returns_years": types.Schema(type=types.Type.NUMBER),
                    "pay_stubs_months": types.Schema(type=types.Type.NUMBER),
                },
                required=[
                    "current_address",
                    "property_state",
                    "email",
                    "phone",
                    "annual_income",
                    "w2_provided",
                    "tax_returns_years",
                    "pay_stubs_months",
                ],
            ),
        )

        return types.Tool(
            function_declarations=[
                verify_identity,
                check_employment,
                detect_synthetic,
                verify_consistency,
            ]
        )

    def _get_system_instruction(self) -> str:
        return """You are the Person Verification Agent for MortgageClear mortgage underwriting.

Your role is to detect person-level fraud, synthetic identities, and application inconsistencies.

Call ALL FOUR verification tools in sequence:
1. verify_person_identity — check age, name, SSN last-4 format
2. check_employment_consistency — validate work history vs age, income plausibility
3. detect_synthetic_identity — scan for synthetic identity patterns
4. verify_application_consistency — cross-check address, email, phone, documentation

After all four tool calls, output ONLY a JSON object:
{
  "risk_score": <number 0-100, where 100 = fully verified, no red flags>,
  "risk_level": "<low|medium|high|critical>",
  "identity_consistent": <true|false>,
  "synthetic_identity_risk": <true|false>,
  "employment_consistent": <true|false>,
  "person_flags": ["<flag>", "..."],
  "analysis_summary": "<paragraph summarizing verification findings>",
  "recommendations": ["<recommendation>", "..."]
}

Scoring guidance:
- Start at 100 (fully verified applicant)
- Deduct 20-30 for each major inconsistency (impossible employment duration, implausible income)
- Deduct 10-15 for minor red flags (incomplete address, suspicious email domain)
- Deduct 40+ for confirmed synthetic identity indicators (age < 18, years_employed > possible)
- Deduct 25 for no documentation despite high income claim (>$100k)
- Any age < 18 → risk_score 0, risk_level "critical", synthetic_identity_risk true

Output ONLY the JSON — no markdown, no extra text."""

    # ─── Tool implementations ──────────────────────────────────────────────────

    def _verify_person_identity(self, applicant: Dict[str, Any]) -> Dict[str, Any]:
        """Compute identity verification checks from raw applicant data."""
        first_name = applicant.get("first_name", "")
        last_name = applicant.get("last_name", "")
        dob_str = applicant.get("date_of_birth", "")
        ssn = applicant.get("ssn", "")

        flags = []

        # Age calculation
        age = None
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            today = date.today()
            age = (
                today.year
                - dob.year
                - ((today.month, today.day) < (dob.month, dob.day))
            )
        except (ValueError, TypeError):
            flags.append("Invalid or missing date of birth")
            age = 35  # neutral default

        if age is not None:
            if age < 18:
                flags.append(f"Applicant age {age} is below legal minimum (18)")
            elif age > 90:
                flags.append(f"Applicant age {age} is unusually high")

        # Name validation
        if not first_name or len(first_name.strip()) < 2:
            flags.append("First name too short or missing")
        if not last_name or len(last_name.strip()) < 2:
            flags.append("Last name too short or missing")

        # SSN last-4 format
        ssn_str = str(ssn).strip() if ssn else ""
        ssn_last4 = ssn_str[-4:] if len(ssn_str) >= 4 else ssn_str
        ssn_valid = len(ssn_last4) == 4 and ssn_last4.isdigit()
        if not ssn_valid:
            flags.append("SSN last-4 digits invalid format")
        elif ssn_last4 in ("0000", "1111", "2222", "3333", "4444",
                           "5555", "6666", "7777", "8888", "9999"):
            flags.append("SSN last-4 digits appear synthetic (all same digit)")

        return {
            "age": age,
            "name_valid": (
                len(first_name.strip()) >= 2 and len(last_name.strip()) >= 2
            ),
            "ssn_format_valid": ssn_valid,
            "flags": flags,
            "identity_check_score": max(0, 100 - len(flags) * 25),
        }

    def _check_employment_consistency(
        self,
        age: int,
        years_employed: int,
        employment_status: str,
        annual_income: float,
        employer_name: str,
    ) -> Dict[str, Any]:
        """Check if employment data is internally consistent."""
        flags = []

        # Cannot have worked more years than (age - 16)
        max_possible_years = max(0, age - 16)
        if years_employed > max_possible_years:
            flags.append(
                f"Years employed ({years_employed}) exceeds maximum possible "
                f"({max_possible_years}) given age {age}"
            )

        # Employment status vs income cross-check
        if employment_status == "employed" and annual_income < 15_000:
            flags.append("Annual income below minimum wage for employed status")
        if employment_status == "retired" and annual_income > 500_000:
            flags.append("Unusually high income for retired applicant")
        if employment_status in ("self-employed", "other") and annual_income > 2_000_000:
            flags.append("Income claim exceeds plausible range for employment type")

        # Employer name sanity
        blank_names = ("n/a", "none", "self", "", "na")
        if not employer_name or employer_name.strip().lower() in blank_names:
            if employment_status == "employed":
                flags.append("No employer name provided for employed applicant")

        # Very short employment + high income
        if years_employed < 1 and annual_income > 250_000:
            flags.append(
                "High income claim ($250k+) with less than 1 year employment"
            )

        return {
            "employment_years_valid": years_employed <= max_possible_years,
            "income_consistent": len(flags) == 0,
            "flags": flags,
            "employment_check_score": max(0, 100 - len(flags) * 20),
        }

    def _detect_synthetic_identity(
        self,
        age: int,
        annual_income: float,
        years_employed: int,
        asking_price: float,
        down_payment: float,
        ssn_last4: str,
    ) -> Dict[str, Any]:
        """Detect synthetic identity patterns."""
        flags = []
        synthetic_risk = False

        # Age < 18 is impossible for a mortgage
        if age < 18:
            flags.append("Applicant age below 18 — automatic disqualifier")
            synthetic_risk = True

        # Impossibly large down payment relative to income
        if annual_income > 0 and down_payment > annual_income * 10:
            flags.append(
                "Down payment exceeds 10× annual income — possible money laundering"
            )
            synthetic_risk = True

        # Very young applicant with high income and many employment years
        if age < 25 and annual_income > 150_000 and years_employed > 8:
            flags.append(
                "Improbable combination: age, income, and employment years are inconsistent"
            )
            synthetic_risk = True

        # Common synthetic SSN patterns
        synthetic_ssn_patterns = ("1234", "0000", "9999", "1111", "1212")
        if ssn_last4 and ssn_last4.isdigit() and ssn_last4 in synthetic_ssn_patterns:
            flags.append(
                f"SSN last-4 '{ssn_last4}' matches known synthetic identity pattern"
            )
            synthetic_risk = True

        # Loan-to-income ratio sanity
        loan_amount = asking_price - down_payment
        if annual_income > 0:
            lti = loan_amount / annual_income
            if lti > 10:
                flags.append(
                    f"Loan-to-income ratio {lti:.1f}× is extremely high (>10×)"
                )

        return {
            "synthetic_risk": synthetic_risk,
            "flags": flags,
            "synthetic_score": max(0, 100 - len(flags) * 30),
        }

    def _verify_application_consistency(
        self,
        current_address: str,
        property_state: str,
        email: str,
        phone: str,
        annual_income: float,
        w2_provided: bool,
        tax_returns_years: int,
        pay_stubs_months: int,
    ) -> Dict[str, Any]:
        """Cross-check application fields for plausibility."""
        flags = []

        # Address checks
        addr = (current_address or "").strip()
        if len(addr) < 10:
            flags.append("Current address appears incomplete")
        if "po box" in addr.lower():
            flags.append(
                "PO Box listed as current address — unusual for mortgage applicant"
            )

        # Email format
        if not email or "@" not in email or "." not in email.split("@")[-1]:
            flags.append("Email address format invalid")

        # Phone format
        digits = "".join(c for c in (phone or "") if c.isdigit())
        if len(digits) < 10:
            flags.append("Phone number appears invalid (fewer than 10 digits)")

        # Documentation consistency vs income
        has_any_docs = w2_provided or tax_returns_years > 0 or pay_stubs_months > 0
        if annual_income > 100_000 and not has_any_docs:
            flags.append(
                "High income claimed but no income documentation provided"
            )
        if annual_income > 200_000 and not w2_provided and tax_returns_years == 0:
            flags.append(
                "Very high income with no W2 or tax returns — documentation gap"
            )

        return {
            "address_valid": len(addr) >= 10 and "po box" not in addr.lower(),
            "contact_valid": "@" in (email or "") and len(digits) >= 10,
            "documentation_consistent": has_any_docs or annual_income <= 100_000,
            "flags": flags,
            "consistency_score": max(0, 100 - len(flags) * 15),
        }

    # ─── Main analysis entry point ─────────────────────────────────────────────

    async def analyze(
        self, application_data: Dict[str, Any]
    ) -> PersonVerificationResult:
        """
        Run person verification checks via a multi-turn LLM agent loop.
        Returns a PersonVerificationResult.
        """
        start_time = time.time()
        applicant = application_data.get("applicant", {})
        property_info = application_data.get("property", {})
        income_docs = application_data.get("income_docs", {})

        # Pre-compute age (needed by tool implementations)
        dob_str = applicant.get("date_of_birth", "")
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            today = date.today()
            age = (
                today.year
                - dob.year
                - ((today.month, today.day) < (dob.month, dob.day))
            )
        except (ValueError, TypeError):
            age = 35  # neutral default

        ssn = applicant.get("ssn", "")
        ssn_str = str(ssn).strip() if ssn else ""
        ssn_last4 = ssn_str[-4:] if len(ssn_str) >= 4 else ssn_str

        initial_prompt = f"""Perform full person verification for this mortgage applicant.

=== APPLICANT ===
Name: {applicant.get('first_name', '')} {applicant.get('last_name', '')}
Date of Birth: {dob_str} (Age: {age})
SSN Last-4: {ssn_last4 or 'N/A'}
Email: {applicant.get('email', 'N/A')}
Phone: {applicant.get('phone', 'N/A')}
Current Address: {applicant.get('current_address', 'N/A')}
Employment: {applicant.get('employment_status', 'N/A')} at \
{applicant.get('employer_name', 'N/A')} \
for {applicant.get('years_employed', 0)} years
Annual Income: ${applicant.get('annual_income', 0):,.0f}

=== PROPERTY ===
State: {property_info.get('state', 'N/A')}
Asking Price: ${property_info.get('asking_price', 0):,.0f}
Down Payment: ${property_info.get('down_payment', 0):,.0f}

=== INCOME DOCS ===
W2 Provided: {income_docs.get('w2_provided', False)}
Tax Returns: {income_docs.get('tax_returns_years', 0)} year(s)
Pay Stubs: {income_docs.get('pay_stubs_months', 0)} month(s)

INSTRUCTIONS:
1. Call verify_person_identity
2. Call check_employment_consistency
3. Call detect_synthetic_identity
4. Call verify_application_consistency
5. Output your JSON assessment."""

        async def tool_executor(
            tool_name: str, args: dict, captured: dict
        ) -> dict:
            if tool_name == "verify_person_identity":
                return self._verify_person_identity(applicant)

            if tool_name == "check_employment_consistency":
                return self._check_employment_consistency(
                    age=age,
                    years_employed=int(applicant.get("years_employed", 0)),
                    employment_status=applicant.get("employment_status", ""),
                    annual_income=float(applicant.get("annual_income", 0)),
                    employer_name=applicant.get("employer_name", ""),
                )

            if tool_name == "detect_synthetic_identity":
                return self._detect_synthetic_identity(
                    age=age,
                    annual_income=float(applicant.get("annual_income", 0)),
                    years_employed=int(applicant.get("years_employed", 0)),
                    asking_price=float(property_info.get("asking_price", 0)),
                    down_payment=float(property_info.get("down_payment", 0)),
                    ssn_last4=ssn_last4,
                )

            if tool_name == "verify_application_consistency":
                return self._verify_application_consistency(
                    current_address=applicant.get("current_address", ""),
                    property_state=property_info.get("state", ""),
                    email=applicant.get("email", ""),
                    phone=applicant.get("phone", ""),
                    annual_income=float(applicant.get("annual_income", 0)),
                    w2_provided=bool(income_docs.get("w2_provided", False)),
                    tax_returns_years=int(income_docs.get("tax_returns_years", 0)),
                    pay_stubs_months=int(income_docs.get("pay_stubs_months", 0)),
                )

            return {"error": f"Unknown tool: {tool_name}"}

        try:
            llm_text, captured, loop_ms = await self._run_agent_loop(
                initial_prompt, tool_executor
            )
            assessment = self._parse_llm_json(llm_text)
        except Exception as exc:
            logger.error(f"PersonVerificationAgent loop failed: {exc}")
            assessment = {}
            captured = {}
            loop_ms = 0

        # ── Fallback: compute directly from tool results ───────────────────────
        id_result = captured.get(
            "verify_person_identity", self._verify_person_identity(applicant)
        )
        emp_result = captured.get(
            "check_employment_consistency",
            self._check_employment_consistency(
                age=age,
                years_employed=int(applicant.get("years_employed", 0)),
                employment_status=applicant.get("employment_status", ""),
                annual_income=float(applicant.get("annual_income", 0)),
                employer_name=applicant.get("employer_name", ""),
            ),
        )
        syn_result = captured.get(
            "detect_synthetic_identity",
            self._detect_synthetic_identity(
                age=age,
                annual_income=float(applicant.get("annual_income", 0)),
                years_employed=int(applicant.get("years_employed", 0)),
                asking_price=float(property_info.get("asking_price", 0)),
                down_payment=float(property_info.get("down_payment", 0)),
                ssn_last4=ssn_last4,
            ),
        )
        con_result = captured.get(
            "verify_application_consistency",
            self._verify_application_consistency(
                current_address=applicant.get("current_address", ""),
                property_state=property_info.get("state", ""),
                email=applicant.get("email", ""),
                phone=applicant.get("phone", ""),
                annual_income=float(applicant.get("annual_income", 0)),
                w2_provided=bool(income_docs.get("w2_provided", False)),
                tax_returns_years=int(income_docs.get("tax_returns_years", 0)),
                pay_stubs_months=int(income_docs.get("pay_stubs_months", 0)),
            ),
        )

        # Aggregate all flags
        all_flags = (
            id_result.get("flags", [])
            + emp_result.get("flags", [])
            + syn_result.get("flags", [])
            + con_result.get("flags", [])
        )

        # Weighted fallback score
        fallback_score = round(
            max(
                0,
                min(
                    100,
                    id_result.get("identity_check_score", 100) * 0.30
                    + emp_result.get("employment_check_score", 100) * 0.25
                    + syn_result.get("synthetic_score", 100) * 0.30
                    + con_result.get("consistency_score", 100) * 0.15,
                ),
            ),
            2,
        )

        # Prefer LLM assessment; fall back to computed values
        risk_score = float(assessment.get("risk_score", fallback_score))
        risk_level_str = assessment.get(
            "risk_level", self._calculate_risk_level(risk_score)
        )
        identity_consistent = bool(
            assessment.get("identity_consistent", len(all_flags) == 0)
        )
        synthetic_identity_risk = bool(
            assessment.get(
                "synthetic_identity_risk", syn_result.get("synthetic_risk", False)
            )
        )
        employment_consistent = bool(
            assessment.get(
                "employment_consistent",
                emp_result.get("income_consistent", True),
            )
        )
        person_flags = assessment.get("person_flags", all_flags)
        recommendations = assessment.get("recommendations", [])
        analysis_summary = assessment.get(
            "analysis_summary",
            (
                "Person verification completed. "
                + (
                    "No red flags detected."
                    if not person_flags
                    else f"{len(person_flags)} issue(s) found: "
                    + "; ".join(person_flags[:2])
                )
            ),
        )

        valid_levels = ("low", "medium", "high", "critical")
        risk_level = (
            RiskLevel(risk_level_str)
            if risk_level_str in valid_levels
            else RiskLevel.MEDIUM
        )

        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"PersonVerificationAgent complete in {processing_time_ms}ms — "
            f"risk: {risk_level_str}, flags: {len(person_flags)}"
        )

        return PersonVerificationResult(
            identity_consistent=identity_consistent,
            synthetic_identity_risk=synthetic_identity_risk,
            employment_consistent=employment_consistent,
            age=age,
            person_flags=person_flags,
            risk_score=risk_score,
            risk_level=risk_level,
            analysis_summary=analysis_summary,
            recommendations=recommendations,
            processing_time_ms=processing_time_ms,
        )
