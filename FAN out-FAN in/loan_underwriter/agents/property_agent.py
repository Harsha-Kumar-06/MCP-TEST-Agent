"""
Property Valuation Agent - Analyzes property value using multiple data sources.
"""

import asyncio
import random
import time
import logging
import json
from typing import Any, Dict, List, Optional

import httpx
from google.genai import types

from .base_agent import BaseAgent
from ..config import config, RISK_THRESHOLDS
from ..models import PropertyValuationResult, RiskLevel

logger = logging.getLogger(__name__)


class PropertyValuationAgent(BaseAgent):
    """Agent responsible for property valuation and market analysis."""
    
    def __init__(self):
        super().__init__(config.property_agent)
    
    def _define_tools(self) -> list:
        """Define property valuation tools."""
        
        zillow_estimate = types.FunctionDeclaration(
            name="get_zillow_estimate",
            description="Get Zillow Zestimate for a property",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "address": types.Schema(type=types.Type.STRING, description="Property address"),
                    "zip_code": types.Schema(type=types.Type.STRING, description="ZIP code"),
                },
                required=["address", "zip_code"]
            )
        )
        
        redfin_estimate = types.FunctionDeclaration(
            name="get_redfin_estimate",
            description="Get Redfin estimate for a property",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "address": types.Schema(type=types.Type.STRING, description="Property address"),
                    "zip_code": types.Schema(type=types.Type.STRING, description="ZIP code"),
                },
                required=["address", "zip_code"]
            )
        )
        
        tax_records = types.FunctionDeclaration(
            name="get_tax_assessment",
            description="Get tax assessment value from local records",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "address": types.Schema(type=types.Type.STRING, description="Property address"),
                    "county": types.Schema(type=types.Type.STRING, description="County name"),
                },
                required=["address"]
            )
        )
        
        comparable_sales = types.FunctionDeclaration(
            name="get_comparable_sales",
            description="Get recent comparable sales in the area",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "address": types.Schema(type=types.Type.STRING, description="Property address"),
                    "radius_miles": types.Schema(type=types.Type.NUMBER, description="Search radius"),
                },
                required=["address"]
            )
        )
        
        return types.Tool(function_declarations=[zillow_estimate, redfin_estimate, tax_records, comparable_sales])
    
    def _get_system_instruction(self) -> str:
        return """You are a Property Valuation Agent for mortgage underwriting.

You MUST use your tools to gather valuation data before answering. Call ALL four
valuation tools to get a comprehensive picture.

Tool usage order:
1. Call get_zillow_estimate for the Zillow Zestimate.
2. Call get_redfin_estimate for the Redfin estimate.
3. Call get_tax_assessment for the tax-assessed value.
4. Call get_comparable_sales for recent nearby sales.

After receiving all tool results, reason carefully about:
- Average estimated value vs. asking price (valuation gap)
- What comparable sales tell you about the market
- Whether the asking price is justified
- Market trend (appreciating/stable/depreciating)

Output ONLY a JSON object — no markdown, no extra text:
{
  "risk_score": <integer 0-100, higher = safer>,
  "risk_level": "<low|medium|high|critical>",
  "market_trend": "<appreciating|stable|depreciating>",
  "analysis_summary": "<2-3 sentence professional summary>",
  "recommendations": ["<specific recommendation>", "..."]
}"""
    
    async def _simulate_zillow_api(self, property_data: Dict) -> Dict[str, Any]:
        """Simulate Zillow API call."""
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        asking_price = property_data.get("asking_price", 400000)
        # Simulate Zillow estimate within ±15% of asking
        variance = random.uniform(-0.15, 0.15)
        
        return {
            "zestimate": round(asking_price * (1 + variance), 0),
            "zestimate_high": round(asking_price * (1 + variance + 0.05), 0),
            "zestimate_low": round(asking_price * (1 + variance - 0.05), 0),
            "last_updated": "2026-02-10"
        }
    
    async def _simulate_redfin_api(self, property_data: Dict) -> Dict[str, Any]:
        """Simulate Redfin API call."""
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        asking_price = property_data.get("asking_price", 400000)
        variance = random.uniform(-0.12, 0.12)
        
        return {
            "estimate": round(asking_price * (1 + variance), 0),
            "estimate_high": round(asking_price * (1 + variance + 0.04), 0),
            "estimate_low": round(asking_price * (1 + variance - 0.04), 0),
            "confidence_score": round(random.uniform(0.7, 0.95), 2)
        }
    
    async def _simulate_tax_records(self, property_data: Dict) -> Dict[str, Any]:
        """Simulate tax records lookup."""
        await asyncio.sleep(random.uniform(0.2, 0.5))
        
        asking_price = property_data.get("asking_price", 400000)
        # Tax assessments typically lag market value by 10-30%
        variance = random.uniform(-0.30, -0.10)
        
        return {
            "assessed_value": round(asking_price * (1 + variance), 0),
            "assessment_year": 2025,
            "tax_rate": round(random.uniform(0.008, 0.025), 4),
            "annual_tax": round(asking_price * (1 + variance) * random.uniform(0.008, 0.025), 2)
        }
    
    async def _simulate_comparable_sales(self, property_data: Dict) -> List[Dict[str, Any]]:
        """Simulate comparable sales search."""
        await asyncio.sleep(random.uniform(0.4, 0.9))
        
        asking_price = property_data.get("asking_price", 400000)
        sq_ft = property_data.get("square_feet", 2000)
        
        comps = []
        for i in range(random.randint(3, 6)):
            variance = random.uniform(-0.15, 0.15)
            sq_ft_variance = random.randint(-300, 300)
            
            comps.append({
                "address": f"{random.randint(100, 9999)} {random.choice(['Oak', 'Maple', 'Pine', 'Cedar', 'Elm'])} {random.choice(['St', 'Ave', 'Dr', 'Ln'])}",
                "sale_price": round(asking_price * (1 + variance), 0),
                "sale_date": f"2025-{random.randint(10, 12):02d}-{random.randint(1, 28):02d}",
                "square_feet": max(800, sq_ft + sq_ft_variance),
                "bedrooms": property_data.get("bedrooms", 3) + random.randint(-1, 1),
                "bathrooms": property_data.get("bathrooms", 2),
                "distance_miles": round(random.uniform(0.1, 2.0), 2)
            })
        
        return comps

    async def _call_rentcast_api(self, property_data: Dict) -> Optional[Dict[str, Any]]:
        """Call RentCast API for real property valuation data."""
        api_key = config.rentcast_api_key
        
        if not api_key or api_key == "mock_key":
            logger.info("RentCast API key not configured, using simulated data")
            return None
        
        address = property_data.get("address", "")
        city = property_data.get("city", "")
        state = property_data.get("state", "")
        zip_code = property_data.get("zip_code", "")
        
        # Build full address for API call
        full_address = f"{address}, {city}, {state} {zip_code}".strip(", ")
        
        if not full_address:
            logger.warning("No address provided for RentCast API call")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # RentCast Property Valuation API
                response = await client.get(
                    "https://api.rentcast.io/v1/avm/value",
                    params={
                        "address": full_address,
                    },
                    headers={
                        "X-Api-Key": api_key,
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"RentCast API returned property valuation for: {full_address}")
                    return {
                        "price": data.get("price"),
                        "priceRangeLow": data.get("priceRangeLow"),
                        "priceRangeHigh": data.get("priceRangeHigh"),
                        "pricePerSquareFoot": data.get("pricePerSquareFoot"),
                        "rentEstimate": data.get("rentEstimate"),
                        "latitude": data.get("latitude"),
                        "longitude": data.get("longitude"),
                        "source": "rentcast"
                    }
                elif response.status_code == 404:
                    logger.warning(f"RentCast: Property not found - {full_address}")
                    return None
                else:
                    logger.warning(f"RentCast API returned status {response.status_code}: {response.text[:200]}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("RentCast API timeout")
            return None
        except Exception as e:
            logger.error(f"RentCast API error: {e}")
            return None

    async def _call_rentcast_comparables(self, property_data: Dict) -> Optional[List[Dict[str, Any]]]:
        """Call RentCast API for comparable sales data."""
        api_key = config.rentcast_api_key
        
        if not api_key or api_key == "mock_key":
            return None
        
        address = property_data.get("address", "")
        city = property_data.get("city", "")
        state = property_data.get("state", "")
        zip_code = property_data.get("zip_code", "")
        
        full_address = f"{address}, {city}, {state} {zip_code}".strip(", ")
        
        if not full_address:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # RentCast Comparable Sales API
                response = await client.get(
                    "https://api.rentcast.io/v1/avm/sale-comparables",
                    params={
                        "address": full_address,
                        "limit": 6
                    },
                    headers={
                        "X-Api-Key": api_key,
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    comparables = data.get("comparables", [])
                    logger.info(f"RentCast API returned {len(comparables)} comparable sales")
                    
                    # Format comparables to match our structure
                    formatted_comps = []
                    for comp in comparables:
                        formatted_comps.append({
                            "address": comp.get("formattedAddress", comp.get("addressLine1", "Unknown")),
                            "sale_price": comp.get("price", 0),
                            "sale_date": comp.get("listedDate", comp.get("lastSeenDate", "2025-01-01")),
                            "square_feet": comp.get("squareFootage", 0),
                            "bedrooms": comp.get("bedrooms", 0),
                            "bathrooms": comp.get("bathrooms", 0),
                            "distance_miles": comp.get("distance", 0),
                            "correlation": comp.get("correlation", 0),
                            "source": "rentcast"
                        })
                    
                    return formatted_comps if formatted_comps else None
                else:
                    logger.warning(f"RentCast comparables API returned status {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"RentCast comparables API error: {e}")
            return None
    
    def _calculate_property_risk_score(self, valuation_data: Dict, asking_price: float) -> float:
        """Calculate property risk score (0-100, higher is better)."""
        score = 100.0
        
        # Calculate average estimated value
        estimates = [
            valuation_data["zillow"]["zestimate"],
            valuation_data["redfin"]["estimate"]
        ]
        avg_estimate = sum(estimates) / len(estimates)
        
        # Valuation gap impact (50% weight)
        gap_percent = abs(asking_price - avg_estimate) / avg_estimate
        
        if gap_percent <= RISK_THRESHOLDS["property"]["low_risk"] - 0.95:  # Within 5%
            score -= 0
        elif gap_percent <= 1 - RISK_THRESHOLDS["property"]["medium_risk"]:  # Within 15%
            score -= 15
        elif gap_percent <= 1 - RISK_THRESHOLDS["property"]["high_risk"]:  # Within 25%
            score -= 30
        else:
            score -= 50
        
        # If asking is significantly above estimates, higher risk
        if asking_price > avg_estimate * 1.1:
            score -= 15
        
        # Tax assessment comparison (20% weight)
        tax_value = valuation_data["tax_records"]["assessed_value"]
        if asking_price > tax_value * 1.5:
            score -= 10  # Large gap between asking and tax assessment
        
        # Comparable sales analysis (30% weight)
        comps = valuation_data["comparable_sales"]
        if comps:
            comp_prices = [c["sale_price"] for c in comps]
            avg_comp = sum(comp_prices) / len(comp_prices)
            comp_gap = abs(asking_price - avg_comp) / avg_comp
            
            if comp_gap > 0.2:
                score -= 15
            elif comp_gap > 0.1:
                score -= 8
        
        return max(0, min(100, score))
    
    def _determine_market_trend(self, comparable_sales: List[Dict]) -> str:
        """Determine market trend based on comparable sales."""
        if not comparable_sales:
            return "stable"
        
        # Simple trend analysis based on sale dates and prices
        recent_sales = sorted(comparable_sales, key=lambda x: x["sale_date"], reverse=True)
        
        if len(recent_sales) >= 2:
            recent_avg = sum(s["sale_price"] for s in recent_sales[:2]) / 2
            older_avg = sum(s["sale_price"] for s in recent_sales[2:]) / max(1, len(recent_sales) - 2)
            
            if older_avg > 0:
                change = (recent_avg - older_avg) / older_avg
                if change > 0.03:
                    return "appreciating"
                elif change < -0.03:
                    return "depreciating"
        
        return "stable"
    
    async def _execute_tool(
        self, tool_name: str, args: dict, captured: dict, property_info: dict
    ) -> dict:
        """Execute a property valuation tool and return its result."""
        if tool_name == "get_zillow_estimate":
            rentcast = await self._call_rentcast_api(property_info)
            if rentcast and rentcast.get("price"):
                return {
                    "zestimate": rentcast["price"],
                    "zestimate_high": rentcast.get("priceRangeHigh", rentcast["price"] * 1.05),
                    "zestimate_low": rentcast.get("priceRangeLow", rentcast["price"] * 0.95),
                    "source": "rentcast",
                }
            return await self._simulate_zillow_api(property_info)

        if tool_name == "get_redfin_estimate":
            # Re-use RentCast data if already fetched for zillow
            zillow_captured = captured.get("get_zillow_estimate", {})
            if zillow_captured.get("source") == "rentcast":
                price = zillow_captured["zestimate"]
                return {
                    "estimate": price,
                    "estimate_high": price * 1.04,
                    "estimate_low": price * 0.96,
                    "confidence_score": 0.90,
                    "source": "rentcast",
                }
            return await self._simulate_redfin_api(property_info)

        if tool_name == "get_tax_assessment":
            return await self._simulate_tax_records(property_info)

        if tool_name == "get_comparable_sales":
            rentcast_comps = await self._call_rentcast_comparables(property_info)
            if rentcast_comps:
                return {"comparables": rentcast_comps, "source": "rentcast"}
            comps = await self._simulate_comparable_sales(property_info)
            return {"comparables": comps, "source": "simulated"}

        return {"error": f"Unknown tool: {tool_name}"}

    async def analyze(self, application_data: Dict[str, Any]) -> PropertyValuationResult:
        """
        Property valuation analysis — the LLM drives all four tool calls and
        reasons over them to produce market trend, risk score, and summary.
        """
        start_time = time.time()
        app_id = application_data.get("application_id", "N/A")
        logger.info(f"Starting property valuation for application {app_id}")

        property_info = application_data.get("property", {})
        asking_price = property_info.get("asking_price", 400000)

        initial_prompt = f"""Analyze this property for mortgage underwriting.

Property: {property_info.get('address', 'N/A')}, {property_info.get('city', '')}, \
{property_info.get('state', '')} {property_info.get('zip_code', '')}
Type: {property_info.get('property_type', 'single_family')}
Built: {property_info.get('year_built', 'N/A')}
Size: {property_info.get('square_feet', 'N/A')} sq ft | \
{property_info.get('bedrooms', 'N/A')} bed / {property_info.get('bathrooms', 'N/A')} bath

Asking Price: ${asking_price:,.0f}
Loan Amount: ${property_info.get('loan_amount', 0):,.0f}
Down Payment: ${property_info.get('down_payment', 0):,.0f}

INSTRUCTIONS:
1. Call get_zillow_estimate for this property.
2. Call get_redfin_estimate for this property.
3. Call get_tax_assessment to check the county tax-assessed value.
4. Call get_comparable_sales to see recent nearby sales.
5. After ALL four tool results, reason about the valuation vs asking price and
   output your JSON risk assessment."""

        async def tool_executor(tool_name, args, captured):
            return await self._execute_tool(tool_name, args, captured, property_info)

        try:
            llm_text, captured, loop_ms = await self._run_agent_loop(
                initial_prompt, tool_executor
            )
            assessment = self._parse_llm_json(llm_text)
        except Exception as exc:
            logger.error(f"Agent loop failed for property valuation: {exc}")
            assessment = {}
            captured = {}
            loop_ms = int((time.time() - start_time) * 1000)

        # Extract captured tool data
        zillow_raw = captured.get("get_zillow_estimate", {})
        redfin_raw = captured.get("get_redfin_estimate", {})
        tax_raw = captured.get("get_tax_assessment", {})
        comps_raw = captured.get("get_comparable_sales", {})

        # Fallback fetch if LLM skipped tools
        if not zillow_raw:
            logger.warning("LLM skipped get_zillow_estimate — fetching directly")
            zillow_raw = await self._simulate_zillow_api(property_info)
        if not redfin_raw:
            redfin_raw = await self._simulate_redfin_api(property_info)
        if not tax_raw:
            tax_raw = await self._simulate_tax_records(property_info)
        if not comps_raw:
            comps_raw = {"comparables": await self._simulate_comparable_sales(property_info)}

        comps_data = comps_raw.get("comparables", [])

        zillow_estimate = zillow_raw.get("zestimate", asking_price)
        redfin_estimate = redfin_raw.get("estimate", asking_price)
        tax_assessed = tax_raw.get("assessed_value", asking_price * 0.80)

        estimated_value = (zillow_estimate + redfin_estimate) / 2
        valuation_gap_percent = ((asking_price - estimated_value) / estimated_value) * 100 \
            if estimated_value else 0.0

        # Use LLM's assessment; fall back to rule-based if missing
        risk_score = float(assessment.get("risk_score", 0))
        if risk_score == 0:
            valuation_data = {
                "zillow": {"zestimate": zillow_estimate},
                "redfin": {"estimate": redfin_estimate},
                "tax_records": {"assessed_value": tax_assessed},
                "comparable_sales": comps_data,
            }
            risk_score = self._calculate_property_risk_score(valuation_data, asking_price)

        risk_level_str = assessment.get(
            "risk_level", self._calculate_risk_level(risk_score)
        )
        try:
            risk_level = RiskLevel(risk_level_str)
        except ValueError:
            risk_level = RiskLevel(self._calculate_risk_level(risk_score))

        market_trend = assessment.get(
            "market_trend", self._determine_market_trend(comps_data)
        )
        summary = assessment.get(
            "analysis_summary",
            f"Property estimated at ${estimated_value:,.0f} vs asking ${asking_price:,.0f}.",
        )
        recommendations = assessment.get("recommendations", ["Order professional appraisal"])
        if not isinstance(recommendations, list):
            recommendations = [recommendations]

        processing_time = int((time.time() - start_time) * 1000)

        return PropertyValuationResult(
            estimated_value=round(estimated_value, 0),
            zillow_estimate=zillow_estimate,
            redfin_estimate=redfin_estimate,
            tax_assessed_value=tax_assessed,
            comparable_sales=comps_data[:5],
            valuation_gap_percent=round(valuation_gap_percent, 2),
            market_trend=market_trend,
            risk_score=round(risk_score, 2),
            risk_level=risk_level,
            analysis_summary=summary,
            recommendations=recommendations,
            processing_time_ms=processing_time,
        )
