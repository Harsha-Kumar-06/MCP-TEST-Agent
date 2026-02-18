"""
Sales Tools - Functions for Sales operations.

These are mock implementations demonstrating the tool pattern.
In production, these would connect to your CRM system.
"""

from datetime import datetime, timedelta
from typing import Optional


def lookup_customer(
    customer_id: Optional[str] = None,
    company_name: Optional[str] = None,
    email: Optional[str] = None
) -> dict:
    """
    Look up customer information in the CRM.
    
    Args:
        customer_id: Customer ID to look up
        company_name: Company name to search
        email: Contact email to search
    
    Returns:
        dict: Customer information
    """
    # Mock customer data
    if customer_id or company_name or email:
        return {
            "found": True,
            "customer": {
                "id": customer_id or "CUST-001234",
                "company_name": company_name or "Acme Corporation",
                "industry": "Technology",
                "account_tier": "Enterprise",
                "primary_contact": {
                    "name": "John Smith",
                    "email": email or "john.smith@acme.com",
                    "phone": "+1-555-123-4567"
                },
                "account_manager": "Sarah Johnson",
                "contract_status": "Active",
                "contract_renewal": "2025-06-30",
                "total_revenue_ytd": "$125,000",
                "last_interaction": "2024-01-20"
            },
            "recent_opportunities": [
                {"name": "Q1 Expansion", "value": "$50,000", "stage": "Proposal"},
                {"name": "New Product Line", "value": "$30,000", "stage": "Discovery"}
            ]
        }
    
    return {
        "found": False,
        "message": "Please provide customer_id, company_name, or email to search"
    }


def generate_quote(
    customer_id: str,
    products_str: str,
    discount_percentage: float = 0,
    valid_days: int = 30
) -> dict:
    """
    Generate a sales quote for a customer.
    
    Args:
        customer_id: Customer ID for the quote
        products_str: Products with quantities in format "product_name:quantity,product_name:quantity" (e.g., "Product A:5,Product B:2")
        discount_percentage: Discount to apply (0-30%)
        valid_days: Number of days quote is valid
    
    Returns:
        dict: Generated quote information
    """
    quote_id = f"QT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Parse products string into list
    products = []
    if products_str:
        for item in products_str.split(","):
            parts = item.strip().split(":")
            if len(parts) >= 2:
                products.append({"name": parts[0].strip(), "quantity": int(parts[1].strip())})
            else:
                products.append({"name": parts[0].strip(), "quantity": 1})
    
    # Mock product pricing
    product_prices = {
        "product_a": 1000,
        "product_b": 2500,
        "product_c": 500,
        "enterprise_license": 10000,
        "support_package": 3000
    }
    
    line_items = []
    subtotal = 0
    
    for product in products:
        product_name = product.get("name", "Unknown")
        quantity = product.get("quantity", 1)
        unit_price = product_prices.get(product_name.lower().replace(" ", "_"), 1000)
        line_total = unit_price * quantity
        subtotal += line_total
        
        line_items.append({
            "product": product_name,
            "quantity": quantity,
            "unit_price": f"${unit_price:,.2f}",
            "line_total": f"${line_total:,.2f}"
        })
    
    discount_amount = subtotal * (discount_percentage / 100)
    total = subtotal - discount_amount
    
    return {
        "quote_id": quote_id,
        "customer_id": customer_id,
        "status": "draft",
        "line_items": line_items,
        "subtotal": f"${subtotal:,.2f}",
        "discount": f"{discount_percentage}% (${discount_amount:,.2f})",
        "total": f"${total:,.2f}",
        "valid_until": (datetime.now() + timedelta(days=valid_days)).strftime("%Y-%m-%d"),
        "terms": "Net 30",
        "message": f"Quote {quote_id} generated successfully. Ready for review.",
        "actions": ["Send to customer", "Request approval", "Edit quote"]
    }


def check_pricing(
    product_name: str,
    quantity: int = 1,
    customer_tier: str = "standard"
) -> dict:
    """
    Check current pricing and available discounts.
    
    Args:
        product_name: Name of the product
        quantity: Quantity for volume pricing
        customer_tier: Customer tier (standard, silver, gold, enterprise)
    
    Returns:
        dict: Pricing information and available discounts
    """
    # Mock pricing data
    base_prices = {
        "product_a": 1000,
        "product_b": 2500,
        "product_c": 500,
        "enterprise_license": 10000,
        "support_package": 3000
    }
    
    tier_discounts = {
        "standard": 0,
        "silver": 5,
        "gold": 10,
        "enterprise": 15
    }
    
    volume_discounts = {
        1: 0,
        5: 5,
        10: 10,
        25: 15,
        50: 20,
        100: 25
    }
    
    product_key = product_name.lower().replace(" ", "_")
    base_price = base_prices.get(product_key, 1000)
    tier_discount = tier_discounts.get(customer_tier.lower(), 0)
    
    # Find applicable volume discount
    vol_discount = 0
    for qty, disc in volume_discounts.items():
        if quantity >= qty:
            vol_discount = disc
    
    total_discount = min(tier_discount + vol_discount, 30)  # Cap at 30%
    final_price = base_price * (1 - total_discount / 100)
    
    return {
        "product": product_name,
        "base_price": f"${base_price:,.2f}",
        "customer_tier": customer_tier,
        "tier_discount": f"{tier_discount}%",
        "volume_discount": f"{vol_discount}% (for {quantity} units)",
        "total_discount": f"{total_discount}%",
        "final_unit_price": f"${final_price:,.2f}",
        "total_price": f"${final_price * quantity:,.2f}",
        "max_discount_allowed": "30% (requires VP approval for higher)"
    }


def get_sales_report(
    report_type: str = "summary",
    period: str = "current_month"
) -> dict:
    """
    Generate sales reports and metrics.
    
    Args:
        report_type: Type of report (summary, pipeline, forecast, team)
        period: Time period (current_month, last_month, quarter, year)
    
    Returns:
        dict: Sales report data
    """
    reports = {
        "summary": {
            "period": period,
            "total_revenue": "$1,250,000",
            "deals_closed": 45,
            "average_deal_size": "$27,778",
            "win_rate": "35%",
            "quota_attainment": "85%",
            "top_products": ["Enterprise License", "Support Package", "Product A"]
        },
        "pipeline": {
            "period": period,
            "total_pipeline": "$3,500,000",
            "stages": {
                "discovery": {"count": 25, "value": "$750,000"},
                "qualification": {"count": 18, "value": "$900,000"},
                "proposal": {"count": 12, "value": "$1,200,000"},
                "negotiation": {"count": 8, "value": "$650,000"}
            },
            "expected_close_this_month": "$450,000"
        },
        "forecast": {
            "period": "next_quarter",
            "projected_revenue": "$1,800,000",
            "confidence": "Medium",
            "committed": "$800,000",
            "best_case": "$1,200,000",
            "pipeline_coverage": "2.5x"
        },
        "team": {
            "period": period,
            "top_performers": [
                {"name": "Alice Brown", "revenue": "$350,000", "quota": "115%"},
                {"name": "Bob Wilson", "revenue": "$280,000", "quota": "93%"},
                {"name": "Carol Davis", "revenue": "$250,000", "quota": "83%"}
            ],
            "team_quota_attainment": "85%"
        }
    }
    
    return {
        "report_type": report_type,
        "data": reports.get(report_type, reports["summary"]),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "note": "For detailed reports, access the Sales Dashboard at sales.company.com"
    }


def update_crm(
    customer_id: str,
    update_type: str,
    data: dict
) -> dict:
    """
    Update customer records in the CRM.
    
    Args:
        customer_id: Customer ID to update
        update_type: Type of update (contact, opportunity, note, activity)
        data: Data to update
    
    Returns:
        dict: Update confirmation
    """
    update_id = f"UPD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "status": "success",
        "update_id": update_id,
        "customer_id": customer_id,
        "update_type": update_type,
        "data_updated": data,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": f"CRM record for customer {customer_id} updated successfully.",
        "audit_trail": "Change logged for compliance"
    }
