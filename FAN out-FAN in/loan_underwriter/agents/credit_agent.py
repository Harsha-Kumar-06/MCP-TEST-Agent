"""
Credit Analysis Agent - Analyzes credit history and debt-to-income ratio.
"""

import asyncio
import random
import time
import logging
import json
from typing import Any, Dict, Optional

import httpx
from google.genai import types

from .base_agent import BaseAgent
from ..config import config, RISK_THRESHOLDS
from ..models import CreditAnalysisResult, RiskLevel

logger = logging.getLogger(__name__)


class CreditAnalysisAgent(BaseAgent):
    """Agent responsible for credit analysis and debt-to-income ratio assessment."""
    
    def __init__(self):
        super().__init__(config.credit_agent)
    
    def _define_tools(self) -> list:
        """Define credit analysis tools."""
        
        # Tool declarations for the agent
        pull_credit_report = types.FunctionDeclaration(
            name="pull_credit_report",
            description="Pull credit report from credit bureaus for an applicant",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "ssn": types.Schema(type=types.Type.STRING, description="Applicant SSN"),
                    "full_name": types.Schema(type=types.Type.STRING, description="Full name"),
                },
                required=["ssn", "full_name"]
            )
        )
        
        calculate_dti = types.FunctionDeclaration(
            name="calculate_debt_to_income",
            description="Calculate debt-to-income ratio based on debts and income",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "monthly_debt": types.Schema(type=types.Type.NUMBER, description="Total monthly debt payments"),
                    "monthly_income": types.Schema(type=types.Type.NUMBER, description="Gross monthly income"),
                },
                required=["monthly_debt", "monthly_income"]
            )
        )
        
        return types.Tool(function_declarations=[pull_credit_report, calculate_dti])
    
    def _get_system_instruction(self) -> str:
        return """You are a Credit Analysis Agent for mortgage underwriting.

Your job is to use your tools to gather credit data, reason over it, and produce a
structured risk assessment. You MUST call tools to gather data before answering.

Tool usage order:
1. Call pull_credit_report to retrieve the applicant's credit bureau data.
2. Call calculate_debt_to_income using the total_debt from the credit report
   (use ~3% of total_debt as monthly payment estimate) and the monthly income
   from the application.
3. After receiving both tool results, reason carefully and output ONLY a JSON object:

{
  "risk_score": <integer 0-100, higher = safer>,
  "risk_level": "<low|medium|high|critical>",
  "analysis_summary": "<2-3 sentence professional summary>",
  "recommendations": ["<specific recommendation>", "..."]
}

Consider: credit score, history length, utilization, late payments, bankruptcies,
collections, DTI ratio, and the proposed loan amount. Output ONLY the JSON — no
markdown, no extra text."""
    
    async def _simulate_credit_bureau_call(self, applicant_data: Dict) -> Dict[str, Any]:
        """Simulate credit bureau API call (replace with real API in production)."""
        # Simulate API latency
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Generate realistic mock credit data
        credit_score = random.randint(580, 850)
        credit_history_years = random.randint(2, 25)
        
        return {
            "credit_score": credit_score,
            "credit_history_length_years": credit_history_years,
            "total_accounts": random.randint(3, 15),
            "open_accounts": random.randint(2, 8),
            "total_debt": round(random.uniform(5000, 150000), 2),
            "available_credit": round(random.uniform(10000, 100000), 2),
            "credit_utilization": round(random.uniform(0.1, 0.7), 2),
            "late_payments_last_24_months": random.randint(0, 5),
            "collections": random.randint(0, 2),
            "bankruptcies": 0 if random.random() > 0.05 else 1,
            "recent_inquiries": random.randint(0, 6),
            "source": "simulated"
        }

    async def _get_experian_access_token(self) -> Optional[str]:
        """Get OAuth access token from Experian using password grant with Basic Auth."""
        client_id = config.experian_client_id
        client_secret = config.experian_client_secret
        username = config.experian_username
        password = config.experian_password
        
        if not all([client_id, client_secret, username, password]):
            logger.info("Experian credentials not fully configured")
            return None
        
        # Determine environment
        env = config.experian_env.lower()
        if env == "sandbox":
            token_url = "https://sandbox-us-api.experian.com/oauth2/v1/token"
        else:
            token_url = "https://us-api.experian.com/oauth2/v1/token"
        
        try:
            import base64
            # Use HTTP Basic Auth for client credentials (as per Experian's OAuth spec)
            auth_string = f"{client_id}:{client_secret}"
            auth_bytes = base64.b64encode(auth_string.encode()).decode()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "password",
                        "username": username,
                        "password": password
                    },
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Authorization": f"Basic {auth_bytes}",
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info("Successfully obtained Experian access token")
                    return data.get("access_token")
                else:
                    logger.warning(f"Experian OAuth failed with status {response.status_code}: {response.text[:200]}")
                    return None
                    
        except Exception as e:
            logger.error(f"Experian OAuth error: {e}")
            return None

    async def _call_experian_credit_report(self, applicant_data: Dict) -> Optional[Dict[str, Any]]:
        """Call Experian API for credit report data."""
        access_token = await self._get_experian_access_token()
        
        if not access_token:
            logger.info("Experian access token not available, using simulated data")
            return None
        
        # Determine environment
        env = config.experian_env.lower()
        if env == "sandbox":
            base_url = "https://sandbox-us-api.experian.com"
            # Experian sandbox requires specific test consumers
            # Using Experian's documented sandbox test data
            first_name = "ALEJANDRO"
            last_name = "HERNANDEZ"
            ssn = "666787028"  # Experian sandbox test SSN
            address_line1 = "8313 WARM SPRINGS"
            city = "LAS VEGAS"
            state = "NV"
            zip_code = "89113"
        else:
            base_url = "https://us-api.experian.com"
            # Extract real applicant information for production
            first_name = applicant_data.get("first_name", "")
            last_name = applicant_data.get("last_name", "")
            ssn = applicant_data.get("ssn", "")
            address = applicant_data.get("current_address", "")
            address_line1 = address[:50] if address else ""
            city = ""
            state = ""
            zip_code = ""
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Experian Consumer Credit Profile API
                request_body = {
                    "consumerPii": {
                        "primaryApplicant": {
                            "name": {
                                "firstName": first_name,
                                "lastName": last_name
                            },
                            "ssn": {
                                "ssn": ssn
                            },
                            "currentAddress": {
                                "line1": address_line1,
                                "city": city,
                                "state": state,
                                "zipCode": zip_code
                            }
                        }
                    },
                    "requestor": {
                        "subscriberCode": config.experian_subscriber_code or "2222222"
                    },
                    "permissiblePurpose": {
                        "type": "3F"
                    },
                    "addOns": {
                        "riskModels": {
                            "modelIndicator": ["V4"],
                            "scorePercentile": "Y"
                        }
                    }
                }
                
                # clientReferenceId must be alphanumeric, max 32 chars
                app_id = applicant_data.get('application_id', 'TEST001')
                client_ref = ''.join(c for c in app_id if c.isalnum())[:32] or 'LOANAPP001'
                
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "companyId": config.experian_company_id or "SBMYSQL",
                    "clientReferenceId": client_ref
                }
                
                logger.info(f"Calling Experian API at {base_url}")
                logger.debug(f"Request headers: companyId={headers.get('companyId')}")
                
                response = await client.post(
                    f"{base_url}/consumerservices/credit-profile/v2/credit-report",
                    json=request_body,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info("Successfully retrieved Experian credit report")
                    
                    # Parse Experian response into our format
                    credit_profile = data.get("creditProfile", {})
                    risk_model = credit_profile.get("riskModel", [{}])[0] if credit_profile.get("riskModel") else {}
                    tradelines = credit_profile.get("tradeline", [])
                    
                    # Calculate totals from tradelines
                    total_debt = sum(t.get("balanceAmount", 0) for t in tradelines)
                    available_credit = sum(t.get("creditLimit", 0) - t.get("balanceAmount", 0) for t in tradelines if t.get("creditLimit"))
                    total_accounts = len(tradelines)
                    open_accounts = len([t for t in tradelines if t.get("accountStatus") == "O"])
                    
                    # Get late payments from payment history
                    late_payments = sum(
                        1 for t in tradelines 
                        for p in t.get("paymentHistory", []) 
                        if p.get("status") in ["30", "60", "90", "120"]
                    )
                    
                    credit_score = risk_model.get("score", 0)
                    
                    return {
                        "credit_score": int(credit_score) if credit_score else random.randint(650, 750),
                        "credit_history_length_years": 5,  # Would need to calculate from oldest account
                        "total_accounts": total_accounts,
                        "open_accounts": open_accounts,
                        "total_debt": round(total_debt, 2),
                        "available_credit": round(available_credit, 2),
                        "credit_utilization": round(total_debt / (total_debt + available_credit), 2) if (total_debt + available_credit) > 0 else 0,
                        "late_payments_last_24_months": late_payments,
                        "collections": len(credit_profile.get("collection", [])),
                        "bankruptcies": len(credit_profile.get("publicRecord", [])),
                        "recent_inquiries": len(credit_profile.get("inquiry", [])),
                        "source": "experian"
                    }
                    
                elif response.status_code == 401:
                    logger.warning("Experian API unauthorized - token may have expired")
                    return None
                else:
                    logger.warning(f"Experian API returned status {response.status_code}: {response.text[:300]}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Experian API timeout")
            return None
        except Exception as e:
            logger.error(f"Experian API error: {e}")
            return None

    # =========================================================================
    # EQUIFAX API INTEGRATION
    # =========================================================================
    
    async def _get_equifax_access_token(self) -> Optional[str]:
        """Get OAuth access token from Equifax using client credentials grant."""
        client_id = config.equifax_client_id
        client_secret = config.equifax_client_secret
        
        if not all([client_id, client_secret]) or client_id == "your_equifax_client_id_here":
            logger.info("Equifax credentials not configured")
            return None
        
        # Determine environment
        env = config.equifax_env.lower()
        if env == "sandbox":
            token_url = "https://api.sandbox.equifax.com/v2/oauth/token"
        else:
            token_url = "https://api.equifax.com/v2/oauth/token"
        
        try:
            import base64
            # Equifax uses client_credentials grant with Basic Auth
            auth_string = f"{client_id}:{client_secret}"
            auth_bytes = base64.b64encode(auth_string.encode()).decode()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "client_credentials",
                        "scope": "https://api.equifax.com/business/prequalification-of-one/v1"
                    },
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Authorization": f"Basic {auth_bytes}"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info("Successfully obtained Equifax access token")
                    return data.get("access_token")
                else:
                    logger.warning(f"Equifax OAuth failed with status {response.status_code}: {response.text[:200]}")
                    return None
                    
        except Exception as e:
            logger.error(f"Equifax OAuth error: {e}")
            return None

    async def _call_equifax_credit_report(self, applicant_data: Dict) -> Optional[Dict[str, Any]]:
        """Call Equifax API for credit report data."""
        access_token = await self._get_equifax_access_token()
        
        if not access_token:
            logger.info("Equifax access token not available")
            return None
        
        # Determine environment
        env = config.equifax_env.lower()
        if env == "sandbox":
            base_url = "https://api.sandbox.equifax.com"
        else:
            base_url = "https://api.equifax.com"
        
        try:
            # Parse applicant data
            first_name = applicant_data.get("first_name", "")
            last_name = applicant_data.get("last_name", "")
            ssn = applicant_data.get("ssn", "").replace("-", "").replace("X", "0")
            
            # Get address components (if available)
            address = applicant_data.get("address", {})
            if isinstance(address, str):
                street = address
                city = applicant_data.get("city", "")
                state = applicant_data.get("state", "")
                zip_code = applicant_data.get("zip_code", "")
            else:
                street = address.get("street", address.get("line1", ""))
                city = address.get("city", "")
                state = address.get("state", "")
                zip_code = address.get("zip_code", address.get("zipCode", ""))
            
            # Build Equifax Prequalification request
            request_body = {
                "consumers": {
                    "name": [
                        {
                            "identifier": "current",
                            "firstName": first_name.upper(),
                            "lastName": last_name.upper()
                        }
                    ],
                    "socialNum": [
                        {
                            "identifier": "current",
                            "number": ssn if len(ssn) == 9 else "000000000"
                        }
                    ],
                    "addresses": [
                        {
                            "identifier": "current",
                            "houseNumber": street.split()[0] if street else "",
                            "streetName": " ".join(street.split()[1:]) if street else "",
                            "city": city.upper(),
                            "state": state.upper(),
                            "zip": zip_code[:5] if zip_code else ""
                        }
                    ]
                },
                "customerConfiguration": {
                    "equifaxUSConsumerCreditReport": {
                        "memberNumber": config.equifax_member_number or "999XX00000",
                        "securityCode": config.equifax_security_code or "XXX",
                        "customerCode": "LOAN",
                        "multipleReportIndicator": "1",
                        "models": {
                            "modelIndicator": [
                                {
                                    "modelNumber": "05953"  # FICO Score
                                }
                            ]
                        },
                        "outputFormat": {
                            "outputFormat": "0F"  # JSON format
                        }
                    }
                }
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            logger.info(f"Calling Equifax API at {base_url}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{base_url}/business/prequalification-of-one/v1/consumer-credit-report",
                    json=request_body,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info("Successfully retrieved Equifax credit report")
                    
                    # Parse Equifax response into our format
                    credit_report = data.get("consumers", {}).get("equifaxUSConsumerCreditReport", [{}])
                    if isinstance(credit_report, list) and credit_report:
                        credit_report = credit_report[0]
                    
                    # Extract credit score from models
                    models = credit_report.get("models", [])
                    credit_score = 0
                    for model in models:
                        if model.get("score"):
                            credit_score = int(model.get("score", 0))
                            break
                    
                    # Extract tradelines
                    tradelines = credit_report.get("trades", [])
                    total_debt = sum(float(t.get("balanceAmount", 0) or 0) for t in tradelines)
                    available_credit = sum(float(t.get("highCredit", 0) or 0) - float(t.get("balanceAmount", 0) or 0) for t in tradelines)
                    
                    return {
                        "credit_score": credit_score if credit_score else random.randint(650, 750),
                        "credit_history_length_years": 5,
                        "total_accounts": len(tradelines),
                        "open_accounts": len([t for t in tradelines if t.get("accountDesignator") == "I"]),
                        "total_debt": round(total_debt, 2),
                        "available_credit": round(available_credit, 2),
                        "credit_utilization": round(total_debt / (total_debt + available_credit), 2) if (total_debt + available_credit) > 0 else 0,
                        "late_payments_last_24_months": 0,
                        "collections": len(credit_report.get("collections", [])),
                        "bankruptcies": len(credit_report.get("bankruptcies", [])),
                        "recent_inquiries": len(credit_report.get("inquiries", [])),
                        "source": "equifax"
                    }
                    
                elif response.status_code == 401:
                    logger.warning("Equifax API unauthorized - token may have expired")
                    return None
                else:
                    logger.warning(f"Equifax API returned status {response.status_code}: {response.text[:300]}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Equifax API timeout")
            return None
        except Exception as e:
            logger.error(f"Equifax API error: {e}")
            return None

    # =========================================================================
    # CREDIT DATA RETRIEVAL (Bureau Selection Logic)
    # =========================================================================
    
    async def _get_credit_data(self, applicant_data: Dict) -> Dict[str, Any]:
        """Get credit data from configured bureau or fallback to simulation."""
        bureau = config.credit_bureau.lower()
        
        logger.info(f"Credit bureau configured: {bureau}")
        
        if bureau == "equifax":
            credit_data = await self._call_equifax_credit_report(applicant_data)
            if credit_data and credit_data.get("source") == "equifax":
                logger.info("Using real Equifax credit data")
                return credit_data
            logger.info("Equifax unavailable, falling back to simulated data")
            
        elif bureau == "experian":
            credit_data = await self._call_experian_credit_report(applicant_data)
            if credit_data and credit_data.get("source") == "experian":
                logger.info("Using real Experian credit data")
                return credit_data
            logger.info("Experian unavailable, falling back to simulated data")
        
        # Default: use simulated data
        logger.info("Using simulated credit data")
        return await self._simulate_credit_bureau_call(applicant_data)
    
    def _calculate_credit_risk_score(self, credit_data: Dict, dti_ratio: float) -> float:
        """Calculate credit risk score (0-100, higher is better)."""
        score = 100.0
        
        # Credit score impact (40% weight)
        credit_score = credit_data["credit_score"]
        if credit_score >= RISK_THRESHOLDS["credit"]["excellent"]:
            score -= 0
        elif credit_score >= RISK_THRESHOLDS["credit"]["good"]:
            score -= 10
        elif credit_score >= RISK_THRESHOLDS["credit"]["fair"]:
            score -= 25
        elif credit_score >= RISK_THRESHOLDS["credit"]["poor"]:
            score -= 40
        else:
            score -= 55
        
        # DTI ratio impact (30% weight)
        if dti_ratio <= 0.28:
            score -= 0
        elif dti_ratio <= 0.36:
            score -= 8
        elif dti_ratio <= 0.43:
            score -= 18
        else:
            score -= 30
        
        # Late payments impact (15% weight)
        late_payments = credit_data["late_payments_last_24_months"]
        score -= min(late_payments * 5, 15)
        
        # Credit history length (10% weight)
        if credit_data["credit_history_length_years"] < 3:
            score -= 10
        elif credit_data["credit_history_length_years"] < 7:
            score -= 5
        
        # Collections and bankruptcies (5% weight)
        if credit_data.get("bankruptcies", 0) > 0:
            score -= 20
        if credit_data.get("collections", 0) > 0:
            score -= credit_data["collections"] * 5
        
        return max(0, min(100, score))
    
    async def _execute_tool(
        self, tool_name: str, args: dict, captured: dict,
        applicant: dict, property_info: dict
    ) -> dict:
        """Execute a credit analysis tool and return its result."""
        if tool_name == "pull_credit_report":
            return await self._get_credit_data(applicant)

        if tool_name == "calculate_debt_to_income":
            monthly_debt = float(args.get("monthly_debt", 0))
            # LLM may pass annual_income directly; convert if so
            monthly_income = float(args.get("monthly_income", 0))
            if monthly_income == 0:
                annual = applicant.get("annual_income", 75000)
                monthly_income = annual / 12

            # Add proposed mortgage to existing debt
            proposed_mortgage = property_info.get("loan_amount", 300000) * 0.006
            total_monthly_debt = monthly_debt + proposed_mortgage

            dti = total_monthly_debt / monthly_income if monthly_income > 0 else 1.0
            return {
                "dti_ratio": round(dti, 4),
                "dti_percent": f"{dti * 100:.1f}%",
                "monthly_existing_debt": round(monthly_debt, 2),
                "proposed_mortgage_payment": round(proposed_mortgage, 2),
                "total_monthly_debt": round(total_monthly_debt, 2),
                "monthly_income": round(monthly_income, 2),
                "assessment": (
                    "excellent" if dti < 0.28 else
                    "good" if dti < 0.36 else
                    "borderline" if dti < 0.43 else
                    "high_risk"
                ),
            }

        return {"error": f"Unknown tool: {tool_name}"}

    async def analyze(self, application_data: Dict[str, Any]) -> CreditAnalysisResult:
        """
        Perform credit analysis — the LLM now drives which tools to call and
        reasons over the results to produce its own risk score and summary.
        """
        start_time = time.time()
        app_id = application_data.get("application_id", "N/A")
        logger.info(f"Starting credit analysis for application {app_id}")

        applicant = application_data.get("applicant", {})
        property_info = application_data.get("property", {})
        annual_income = applicant.get("annual_income", 75000)

        # Build the initial prompt — give the LLM the context it needs
        initial_prompt = f"""Analyze this mortgage application for credit risk.

Applicant: {applicant.get('first_name', '')} {applicant.get('last_name', '')}
SSN (last 4): {applicant.get('ssn', '****')}
Date of Birth: {applicant.get('date_of_birth', 'N/A')}
Employment: {applicant.get('employment_status', 'employed')} at \
{applicant.get('employer_name', 'N/A')} for {applicant.get('years_employed', 0)} years
Annual Income: ${annual_income:,.0f}
Monthly Income: ${annual_income / 12:,.0f}

Loan Request: ${property_info.get('loan_amount', 300000):,.0f} for property at \
{property_info.get('address', 'N/A')}, {property_info.get('city', '')}, \
{property_info.get('state', '')}

INSTRUCTIONS:
1. Call pull_credit_report to retrieve the applicant's credit bureau data.
2. Use the total_debt from the report (apply ~3% as monthly minimum payment) and
   the monthly income above to call calculate_debt_to_income.
3. After both tool results, output your final JSON risk assessment."""

        async def tool_executor(tool_name, args, captured):
            return await self._execute_tool(
                tool_name, args, captured, applicant, property_info
            )

        try:
            llm_text, captured, loop_ms = await self._run_agent_loop(
                initial_prompt, tool_executor
            )
            assessment = self._parse_llm_json(llm_text)
        except Exception as exc:
            logger.error(f"Agent loop failed for credit analysis: {exc}")
            assessment = {}
            captured = {}
            loop_ms = int((time.time() - start_time) * 1000)

        # Pull structured data from captured tool results
        credit_data = captured.get("pull_credit_report", {})
        dti_data = captured.get("calculate_debt_to_income", {})

        # Fallback: if agent loop failed to call tools, fetch data directly
        if not credit_data:
            logger.warning("LLM did not call pull_credit_report — fetching directly")
            credit_data = await self._get_credit_data(applicant)

        monthly_income = annual_income / 12
        if dti_data:
            dti_ratio = dti_data.get("dti_ratio", 0.35)
        else:
            existing = credit_data.get("total_debt", 0) * 0.03
            proposed = property_info.get("loan_amount", 300000) * 0.006
            dti_ratio = (existing + proposed) / monthly_income if monthly_income else 1.0

        # Use LLM's risk assessment; fall back to rule-based if LLM didn't produce one
        risk_score = float(assessment.get("risk_score", 0))
        if risk_score == 0:
            risk_score = self._calculate_credit_risk_score(credit_data, dti_ratio)

        risk_level_str = assessment.get(
            "risk_level", self._calculate_risk_level(risk_score)
        )
        try:
            risk_level = RiskLevel(risk_level_str)
        except ValueError:
            risk_level = RiskLevel(self._calculate_risk_level(risk_score))

        summary = assessment.get(
            "analysis_summary",
            f"Credit score {credit_data.get('credit_score', 'N/A')} with DTI "
            f"{dti_ratio * 100:.1f}%."
        )
        recommendations = assessment.get("recommendations", ["Review credit report"])
        if not isinstance(recommendations, list):
            recommendations = [recommendations]

        processing_time = int((time.time() - start_time) * 1000)

        return CreditAnalysisResult(
            credit_score=credit_data.get("credit_score", 650),
            debt_to_income_ratio=round(dti_ratio, 4),
            total_debt=credit_data.get("total_debt", 0.0),
            available_credit=credit_data.get("available_credit", 0.0),
            credit_history_length_years=credit_data.get("credit_history_length_years", 5),
            late_payments_last_24_months=credit_data.get("late_payments_last_24_months", 0),
            risk_score=round(risk_score, 2),
            risk_level=risk_level,
            analysis_summary=summary,
            recommendations=recommendations,
            processing_time_ms=processing_time,
        )
