"""
Legal Tools - Functions for Legal and Compliance operations.

These are mock implementations demonstrating the tool pattern.
In production, these would connect to your legal management system.
"""

from datetime import datetime, timedelta
from typing import Optional


def request_contract_review(
    requester_id: str,
    contract_type: str,
    counterparty: str,
    contract_value: str,
    urgency: str = "normal",
    notes: Optional[str] = None
) -> dict:
    """
    Submit a contract for legal review.
    
    Args:
        requester_id: Employee ID of the requester
        contract_type: Type of contract (vendor, customer, partnership, nda, employment)
        counterparty: Name of the other party
        contract_value: Estimated contract value
        urgency: Review urgency (low, normal, high, critical)
        notes: Additional notes or concerns
    
    Returns:
        dict: Review request status and timeline
    """
    request_id = f"LGL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # SLA based on urgency and contract value
    sla_map = {
        "critical": "1 business day",
        "high": "3 business days",
        "normal": "5 business days",
        "low": "10 business days"
    }
    
    return {
        "status": "submitted",
        "request_id": request_id,
        "requester_id": requester_id,
        "contract_type": contract_type,
        "counterparty": counterparty,
        "contract_value": contract_value,
        "urgency": urgency,
        "estimated_completion": sla_map.get(urgency, "5 business days"),
        "assigned_to": "Legal Team Queue",
        "next_steps": [
            "Upload contract document to legal portal",
            "Legal team will review and provide redlines",
            "You'll receive notification when review is complete"
        ],
        "portal_url": "legal.company.com/contracts",
        "message": f"Contract review request {request_id} submitted successfully."
    }


def check_compliance(
    compliance_area: str,
    question: Optional[str] = None
) -> dict:
    """
    Check compliance requirements and guidelines.
    
    Args:
        compliance_area: Area of compliance (data_privacy, export_control, financial, hr, safety)
        question: Specific compliance question
    
    Returns:
        dict: Compliance information and guidelines
    """
    compliance_data = {
        "data_privacy": {
            "regulations": ["GDPR", "CCPA", "HIPAA (if applicable)"],
            "key_requirements": [
                "Obtain consent before collecting personal data",
                "Provide data subject access upon request",
                "Report breaches within 72 hours",
                "Maintain data processing records"
            ],
            "training_required": "Annual data privacy training",
            "contact": "privacy@company.com",
            "resources": "compliance.company.com/privacy"
        },
        "export_control": {
            "regulations": ["EAR", "ITAR", "OFAC"],
            "key_requirements": [
                "Screen all international transactions",
                "Verify end-user and end-use",
                "Obtain licenses when required",
                "Maintain export records for 5 years"
            ],
            "training_required": "Export compliance certification",
            "contact": "export@company.com",
            "resources": "compliance.company.com/export"
        },
        "financial": {
            "regulations": ["SOX", "FCPA", "Anti-Money Laundering"],
            "key_requirements": [
                "Maintain accurate financial records",
                "No bribes or corrupt payments",
                "Report suspicious transactions",
                "Follow expense policies"
            ],
            "training_required": "Annual ethics and compliance training",
            "contact": "compliance@company.com",
            "resources": "compliance.company.com/financial"
        },
        "hr": {
            "regulations": ["EEO", "ADA", "FMLA", "FLSA"],
            "key_requirements": [
                "Non-discrimination in hiring and employment",
                "Reasonable accommodations",
                "Proper wage and hour compliance",
                "Safe workplace requirements"
            ],
            "training_required": "Harassment prevention training",
            "contact": "hr@company.com",
            "resources": "compliance.company.com/hr"
        },
        "safety": {
            "regulations": ["OSHA", "Local safety codes"],
            "key_requirements": [
                "Report all workplace injuries",
                "Follow safety procedures",
                "Use required PPE",
                "Participate in safety training"
            ],
            "training_required": "Annual safety training",
            "contact": "safety@company.com",
            "resources": "compliance.company.com/safety"
        }
    }
    
    area_data = compliance_data.get(compliance_area.lower())
    
    if area_data:
        return {
            "compliance_area": compliance_area,
            "information": area_data,
            "disclaimer": "This is general guidance only. For specific situations, consult the Legal team.",
            "question_asked": question,
            "recommendation": "For specific questions, please contact the compliance team directly."
        }
    
    return {
        "error": f"Compliance area '{compliance_area}' not found",
        "available_areas": list(compliance_data.keys()),
        "general_contact": "compliance@company.com"
    }


def get_legal_template(
    template_type: str
) -> dict:
    """
    Get standard legal document templates.
    
    Args:
        template_type: Type of template (nda, msa, sow, amendment, termination)
    
    Returns:
        dict: Template information and access details
    """
    templates = {
        "nda": {
            "name": "Non-Disclosure Agreement",
            "versions": ["Mutual NDA", "One-Way NDA (Receiving)", "One-Way NDA (Disclosing)"],
            "last_updated": "2024-01-01",
            "approval_required": False,
            "signing_authority": "Director+"
        },
        "msa": {
            "name": "Master Service Agreement",
            "versions": ["Standard MSA", "Enterprise MSA", "Government MSA"],
            "last_updated": "2023-12-15",
            "approval_required": True,
            "signing_authority": "VP+"
        },
        "sow": {
            "name": "Statement of Work",
            "versions": ["Standard SOW", "Fixed Price SOW", "T&M SOW"],
            "last_updated": "2024-01-10",
            "approval_required": "If value > $50,000",
            "signing_authority": "Director+"
        },
        "amendment": {
            "name": "Contract Amendment",
            "versions": ["Standard Amendment", "Pricing Amendment", "Term Extension"],
            "last_updated": "2023-11-20",
            "approval_required": True,
            "signing_authority": "Same as original contract"
        },
        "termination": {
            "name": "Contract Termination Notice",
            "versions": ["For Convenience", "For Cause", "Mutual"],
            "last_updated": "2023-10-15",
            "approval_required": True,
            "signing_authority": "VP+ and Legal approval"
        }
    }
    
    template = templates.get(template_type.lower())
    
    if template:
        return {
            "template_type": template_type,
            "template_info": template,
            "access": f"legal.company.com/templates/{template_type.lower()}",
            "instructions": [
                "Download the appropriate version",
                "Fill in required fields (highlighted in yellow)",
                "Do not modify standard terms without Legal approval",
                "Submit for review before signing if required"
            ]
        }
    
    return {
        "error": f"Template '{template_type}' not found",
        "available_templates": list(templates.keys()),
        "template_portal": "legal.company.com/templates"
    }


def request_nda(
    requester_id: str,
    counterparty_name: str,
    counterparty_email: str,
    nda_type: str = "mutual",
    purpose: str = "",
    expiration_years: int = 3
) -> dict:
    """
    Request an NDA to be prepared and sent.
    
    Args:
        requester_id: Employee ID of the requester
        counterparty_name: Name of the other party
        counterparty_email: Email of the counterparty for sending
        nda_type: Type of NDA (mutual, receiving, disclosing)
        purpose: Purpose of the NDA/discussions
        expiration_years: NDA term in years (1-5)
    
    Returns:
        dict: NDA request status
    """
    request_id = f"NDA-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "status": "processing",
        "request_id": request_id,
        "requester_id": requester_id,
        "counterparty": {
            "name": counterparty_name,
            "email": counterparty_email
        },
        "nda_type": nda_type,
        "purpose": purpose,
        "term": f"{expiration_years} years",
        "next_steps": [
            "NDA will be generated from standard template",
            "Sent to counterparty via DocuSign within 1 business day",
            "You'll be CC'd on the signature request",
            "Fully executed copy will be stored in legal repository"
        ],
        "estimated_completion": "1-2 business days for counterparty signature",
        "message": f"NDA request {request_id} is being processed."
    }


def lookup_legal_policy(
    policy_topic: str
) -> dict:
    """
    Look up legal policies and guidelines.
    
    Args:
        policy_topic: Topic to look up (signing_authority, approval_matrix, 
                     contract_retention, dispute_resolution, ip_protection)
    
    Returns:
        dict: Policy information
    """
    policies = {
        "signing_authority": {
            "title": "Contract Signing Authority",
            "matrix": {
                "up_to_50k": "Director",
                "50k_to_250k": "VP",
                "250k_to_1m": "SVP",
                "over_1m": "C-Suite",
                "unlimited_liability": "CEO + General Counsel"
            },
            "exceptions": "Legal can grant one-time exceptions with documentation"
        },
        "approval_matrix": {
            "title": "Contract Approval Requirements",
            "requirements": {
                "standard_terms": "No additional approval needed",
                "modified_terms": "Legal review required",
                "indemnification_changes": "Legal + Risk review",
                "limitation_of_liability": "Legal + Finance review",
                "governing_law_changes": "General Counsel approval"
            }
        },
        "contract_retention": {
            "title": "Contract Retention Policy",
            "retention_periods": {
                "active_contracts": "Duration + 7 years",
                "expired_contracts": "7 years from expiration",
                "employment_contracts": "Duration + 10 years",
                "real_estate": "Permanent"
            },
            "storage": "All contracts must be stored in legal repository"
        },
        "dispute_resolution": {
            "title": "Dispute Resolution Policy",
            "process": [
                "Attempt good faith negotiation",
                "Escalate to Legal if unresolved in 30 days",
                "Mediation preferred over litigation",
                "Arbitration per contract terms"
            ],
            "jurisdiction": "Default: State of Delaware",
            "contact": "disputes@company.com"
        },
        "ip_protection": {
            "title": "Intellectual Property Protection",
            "guidelines": [
                "All employee inventions are company property (per employment agreement)",
                "Patent disclosures should be submitted promptly",
                "Trademarks must be approved by Legal/Marketing",
                "Do not share source code without proper agreements"
            ],
            "contact": "ip@company.com"
        }
    }
    
    policy = policies.get(policy_topic.lower())
    
    if policy:
        return {
            "policy_topic": policy_topic,
            "policy": policy,
            "full_policy_document": f"legal.company.com/policies/{policy_topic.lower()}",
            "disclaimer": "This is a summary. Refer to full policy for complete details."
        }
    
    return {
        "error": f"Policy '{policy_topic}' not found",
        "available_policies": list(policies.keys()),
        "policy_portal": "legal.company.com/policies",
        "contact": "legal@company.com for specific questions"
    }
