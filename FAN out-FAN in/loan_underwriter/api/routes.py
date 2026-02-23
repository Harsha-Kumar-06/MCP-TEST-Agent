"""
API Routes for MortgageClear.
"""

import logging
import base64
import json
import re
import os
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import JSONResponse

from .schemas import (
    ApplicationRequest,
    ApplicationResponse,
    ErrorResponse,
    ApplicationStatusResponse
)
from ..agents import AggregatorAgent
from ..models import (
    MortgageApplication,
    ApplicantInfo,
    PropertyInfo,
    IncomeDocuments,
    ApplicationStatus
)
from ..config import config

logger = logging.getLogger(__name__)

router = APIRouter()

# File-based storage for persistence across server restarts
STORAGE_DIR = Path(__file__).parent.parent.parent / "data"
APPLICATIONS_FILE = STORAGE_DIR / "applications.json"
RESULTS_FILE = STORAGE_DIR / "results.json"

def _load_store(filepath: Path) -> Dict[str, Dict[str, Any]]:
    """Load data from JSON file."""
    try:
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load {filepath}: {e}")
    return {}

def _save_store(filepath: Path, data: Dict[str, Dict[str, Any]]) -> None:
    """Save data to JSON file."""
    try:
        STORAGE_DIR.mkdir(exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.warning(f"Could not save {filepath}: {e}")

# Load existing data on startup
applications_store: Dict[str, Dict[str, Any]] = _load_store(APPLICATIONS_FILE)
results_store: Dict[str, Dict[str, Any]] = _load_store(RESULTS_FILE)


def convert_request_to_application(request: ApplicationRequest) -> Dict[str, Any]:
    """Convert API request to internal application format."""
    import uuid
    
    applicant = ApplicantInfo(
        first_name=request.applicant.first_name,
        last_name=request.applicant.last_name,
        ssn=request.applicant.ssn,
        date_of_birth=request.applicant.date_of_birth,
        email=request.applicant.email,
        phone=request.applicant.phone,
        current_address=request.applicant.current_address,
        employment_status=request.applicant.employment_status,
        employer_name=request.applicant.employer_name,
        years_employed=request.applicant.years_employed,
        annual_income=request.applicant.annual_income
    )
    
    property_info = PropertyInfo(
        address=request.property.address,
        city=request.property.city,
        state=request.property.state,
        zip_code=request.property.zip_code,
        property_type=request.property.property_type,
        year_built=request.property.year_built,
        square_feet=request.property.square_feet,
        bedrooms=request.property.bedrooms,
        bathrooms=request.property.bathrooms,
        asking_price=request.property.asking_price,
        down_payment=request.property.down_payment,
        loan_amount=request.property.loan_amount
    )
    
    income_docs = IncomeDocuments(
        w2_provided=request.income_docs.w2_provided,
        tax_returns_years=request.income_docs.tax_returns_years,
        pay_stubs_months=request.income_docs.pay_stubs_months,
        bank_statements_months=request.income_docs.bank_statements_months,
        additional_income_sources=request.income_docs.additional_income_sources
    )
    
    # Generate application ID if not provided
    app_id = request.application_id if request.application_id else f"APP-{uuid.uuid4().hex[:8].upper()}"
    
    application = MortgageApplication(
        application_id=app_id,
        applicant=applicant,
        property=property_info,
        income_docs=income_docs
    )
    
    return application.to_dict()


@router.post(
    "/applications/process",
    response_model=ApplicationResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Process Mortgage Application",
    description="""
    Submit a mortgage application for immediate processing using the multi-agent system.
    
    The system uses a fan-out/fan-in architecture to process the application in parallel:
    1. Credit Analysis Agent - Analyzes credit history and DTI
    2. Property Valuation Agent - Evaluates property value
    3. Fraud Detection Agent - Screens for fraud indicators
    4. Aggregator Agent - Combines results into final decision
    
    Processing typically takes 30-60 seconds compared to 30-60 days for traditional manual underwriting.
    """
)
async def process_application(request: ApplicationRequest):
    """Process a mortgage application through the multi-agent system."""
    
    try:
        logger.info(f"Received application request")
        
        # Convert request to internal format
        application_data = convert_request_to_application(request)
        application_id = application_data["application_id"]
        
        logger.info(f"Processing application {application_id}")
        
        # Store application
        applications_store[application_id] = {
            **application_data,
            "status": ApplicationStatus.PROCESSING.value,
            "submitted_at": datetime.now().isoformat()
        }
        
        # Process through aggregator agent
        aggregator = AggregatorAgent()
        result = await aggregator.process_application(application_data)
        
        # Store result
        results_store[application_id] = result
        
        # Update application status
        applications_store[application_id]["status"] = result["decision"]
        
        # Persist to file
        _save_store(APPLICATIONS_FILE, applications_store)
        _save_store(RESULTS_FILE, results_store)
        
        logger.info(f"Application {application_id} processed: {result['decision']}")
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error processing application: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process application: {str(e)}"
        )


@router.get(
    "/applications/{application_id}",
    response_model=ApplicationResponse,
    responses={
        404: {"model": ErrorResponse}
    },
    summary="Get Application Result",
    description="Retrieve the processing result for a specific application."
)
async def get_application_result(application_id: str):
    """Get the result of a processed application."""
    
    if application_id not in results_store:
        raise HTTPException(
            status_code=404,
            detail=f"Application {application_id} not found"
        )
    
    return JSONResponse(content=results_store[application_id])


@router.get(
    "/applications/{application_id}/status",
    response_model=ApplicationStatusResponse,
    responses={
        404: {"model": ErrorResponse}
    },
    summary="Get Application Status",
    description="Check the current status of an application."
)
async def get_application_status(application_id: str):
    """Get the status of an application."""
    
    if application_id not in applications_store:
        raise HTTPException(
            status_code=404,
            detail=f"Application {application_id} not found"
        )
    
    app_data = applications_store[application_id]
    
    return {
        "application_id": application_id,
        "status": app_data.get("status", "unknown"),
        "message": f"Application is {app_data.get('status', 'unknown')}"
    }


@router.get(
    "/applications",
    summary="List All Applications",
    description="Get a list of all processed applications."
)
async def list_applications():
    """List all applications."""
    
    applications = []
    for app_id, app_data in applications_store.items():
        applications.append({
            "application_id": app_id,
            "status": app_data.get("status"),
            "submitted_at": app_data.get("submitted_at"),
            "applicant_name": f"{app_data.get('applicant', {}).get('first_name', '')} {app_data.get('applicant', {}).get('last_name', '')}".strip()
        })
    
    return {"applications": applications, "total": len(applications)}


@router.delete(
    "/applications/{application_id}",
    summary="Delete Application",
    description="Delete a specific application and its results."
)
async def delete_application(application_id: str):
    """Delete a specific application."""
    
    if application_id not in applications_store:
        raise HTTPException(
            status_code=404,
            detail=f"Application {application_id} not found"
        )
    
    # Remove from both stores
    del applications_store[application_id]
    if application_id in results_store:
        del results_store[application_id]
    
    # Persist changes
    _save_store(APPLICATIONS_FILE, applications_store)
    _save_store(RESULTS_FILE, results_store)
    
    return {"message": f"Application {application_id} deleted successfully"}


@router.delete(
    "/applications",
    summary="Clear All Applications",
    description="Delete all applications and their results."
)
async def clear_all_applications():
    """Clear all applications."""
    
    count = len(applications_store)
    
    # Clear both stores
    applications_store.clear()
    results_store.clear()
    
    # Persist changes
    _save_store(APPLICATIONS_FILE, applications_store)
    _save_store(RESULTS_FILE, results_store)
    
    return {"message": f"Cleared {count} application(s) successfully"}


@router.post(
    "/applications/demo",
    response_model=ApplicationResponse,
    summary="Process Demo Application",
    description="Process a pre-filled demo application to test the system."
)
async def process_demo_application():
    """Process a demo application with sample data."""
    
    demo_request = ApplicationRequest(
        applicant={
            "first_name": "Jane",
            "last_name": "Doe",
            "ssn": "5678",
            "date_of_birth": "1988-03-22",
            "email": "jane.doe@example.com",
            "phone": "555-987-6543",
            "current_address": "789 Example Blvd, Sample City, CA 90001",
            "employment_status": "employed",
            "employer_name": "Innovation Labs",
            "years_employed": 7,
            "annual_income": 145000.00
        },
        property={
            "address": "321 Oak Street",
            "city": "Sunnyvale",
            "state": "CA",
            "zip_code": "94086",
            "property_type": "single_family",
            "year_built": 2018,
            "square_feet": 2200,
            "bedrooms": 4,
            "bathrooms": 3.0,
            "asking_price": 850000.00,
            "down_payment": 170000.00,
            "loan_amount": 680000.00
        },
        income_docs={
            "w2_provided": True,
            "tax_returns_years": 2,
            "pay_stubs_months": 3,
            "bank_statements_months": 6,
            "additional_income_sources": ["stock_options"]
        }
    )
    
    return await process_application(demo_request)


@router.post(
    "/applications/demo-approval",
    response_model=ApplicationResponse,
    summary="Process Approval Demo Application",
    description="Process a demo application with strong financials designed to get approved."
)
async def process_approval_demo_application():
    """Process a demo application designed for approval - strong financials, large down payment, stable employment."""
    
    approval_demo_request = ApplicationRequest(
        applicant={
            "first_name": "Michael",
            "last_name": "Thompson",
            "ssn": "4521",
            "date_of_birth": "1982-06-15",
            "email": "michael.thompson@bigcorp.com",
            "phone": "415-555-1234",
            "current_address": "456 Executive Way, San Francisco, CA 94102",
            "employment_status": "employed",
            "employer_name": "Fortune 500 Tech Inc",
            "years_employed": 12,
            "annual_income": 285000.00
        },
        property={
            "address": "789 Premium Lane",
            "city": "San Mateo",
            "state": "CA",
            "zip_code": "94401",
            "property_type": "single_family",
            "year_built": 2020,
            "square_feet": 2800,
            "bedrooms": 4,
            "bathrooms": 3.0,
            "asking_price": 950000.00,
            "down_payment": 285000.00,
            "loan_amount": 665000.00
        },
        income_docs={
            "w2_provided": True,
            "tax_returns_years": 3,
            "pay_stubs_months": 6,
            "bank_statements_months": 12,
            "additional_income_sources": ["investment_income", "bonus"]
        }
    )
    
    return await process_application(approval_demo_request)


@router.post(
    "/applications/extract-document",
    summary="Extract Application Data from Document",
    description="Upload a document and use AI to extract mortgage application information."
)
async def extract_document_data(file: UploadFile = File(...)):
    """Extract application data from an uploaded document using Gemini AI."""
    
    try:
        logger.info(f"Received document for extraction: {file.filename}")
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")
        
        # Determine file type
        filename = file.filename.lower()
        is_image = filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
        is_pdf = filename.endswith('.pdf')
        
        # Initialize Gemini
        try:
            from google import genai
            client = genai.Client(api_key=config.google_api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise HTTPException(status_code=500, detail="AI service not available")
        
        # Prepare the extraction prompt
        extraction_prompt = """
        Analyze this document and extract mortgage application information. 
        Return a JSON object with the following structure (use null for fields not found):
        
        {
            "applicant": {
                "first_name": "string",
                "last_name": "string", 
                "ssn": "last 4 digits only as string",
                "date_of_birth": "YYYY-MM-DD format",
                "email": "string",
                "phone": "string",
                "current_address": "full address string",
                "employment_status": "employed|self-employed|retired|other",
                "employer_name": "string",
                "years_employed": number,
                "annual_income": number
            },
            "property": {
                "address": "street address",
                "city": "string",
                "state": "2-letter code",
                "zip_code": "string",
                "property_type": "single_family|condo|townhouse|multi_family",
                "year_built": number,
                "square_feet": number,
                "bedrooms": number,
                "bathrooms": number,
                "asking_price": number,
                "down_payment": number
            },
            "income_docs": {
                "w2_provided": boolean,
                "tax_returns_years": number,
                "pay_stubs_months": number,
                "bank_statements_months": number
            }
        }
        
        IMPORTANT: Return ONLY the JSON object, no markdown formatting, no code blocks, no extra text.
        Extract as much information as possible from the document. For any field not found, use null.
        """
        
        # Process based on file type
        if is_image:
            # For images, use vision capabilities
            import PIL.Image
            import io
            image = PIL.Image.open(io.BytesIO(content))
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[extraction_prompt, image]
            )
        elif is_pdf:
            # For PDFs, encode as base64 and send
            encoded = base64.standard_b64encode(content).decode('utf-8')
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    extraction_prompt,
                    {"mime_type": "application/pdf", "data": encoded}
                ]
            )
        else:
            # For text files, decode and send as text
            try:
                text_content = content.decode('utf-8')
            except:
                text_content = content.decode('latin-1')
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[f"{extraction_prompt}\n\nDocument content:\n{text_content[:50000]}"]
            )
        
        # Parse the response
        response_text = response.text.strip()
        
        # Clean up the response - remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)
        
        try:
            extracted_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {response_text[:500]}")
            raise HTTPException(
                status_code=422, 
                detail="Could not extract structured data from document. Please try a clearer document."
            )
        
        logger.info(f"Successfully extracted data from {file.filename}")
        
        return JSONResponse(content={
            "success": True,
            "message": "Document processed successfully",
            "extracted_data": extracted_data,
            "fields_found": count_fields(extracted_data)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting document data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )


def count_fields(data: dict, prefix: str = "") -> int:
    """Count non-null fields in extracted data."""
    count = 0
    for key, value in data.items():
        if isinstance(value, dict):
            count += count_fields(value, f"{prefix}{key}.")
        elif value is not None:
            count += 1
    return count


@router.post(
    "/applications/upload-income-doc",
    summary="Upload Income Documentation",
    description="Upload W2, tax returns, pay stubs, or bank statements for verification."
)
async def upload_income_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...)
):
    """Upload and analyze income documentation using Gemini AI."""
    
    try:
        valid_types = ['w2', 'tax_return', 'pay_stub', 'bank_statement']
        if doc_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid doc_type. Must be one of: {valid_types}")
        
        logger.info(f"Received {doc_type} document: {file.filename}")
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")
        
        # Determine file type
        filename = file.filename.lower()
        is_image = filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
        is_pdf = filename.endswith('.pdf')
        
        # Initialize Gemini
        try:
            from google import genai
            client = genai.Client(api_key=config.google_api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            # Return basic response without AI analysis
            return JSONResponse(content={
                "success": True,
                "doc_type": doc_type,
                "filename": file.filename,
                "file_size": file_size,
                "verified": True,
                "analysis": {"status": "uploaded", "details": "Document received but AI analysis unavailable"}
            })
        
        # Prepare analysis prompt based on document type
        prompts = {
            'w2': """Analyze this W2 tax form and extract the following information in JSON format:
            {
                "employer_name": "string",
                "employer_ein": "string",
                "tax_year": number,
                "wages_tips_compensation": number,
                "federal_tax_withheld": number,
                "social_security_wages": number,
                "medicare_wages": number,
                "employee_name": "string",
                "employee_ssn_last4": "string",
                "is_valid_w2": boolean,
                "confidence_score": number between 0-100
            }
            Return ONLY the JSON object, no extra text.""",
            
            'tax_return': """Analyze this tax return document and extract the following in JSON format:
            {
                "tax_year": number,
                "filing_status": "string",
                "total_income": number,
                "adjusted_gross_income": number,
                "taxable_income": number,
                "total_tax": number,
                "refund_or_owed": number,
                "form_type": "1040|1040-SR|1040-NR|Schedule C|other",
                "is_valid_return": boolean,
                "confidence_score": number between 0-100
            }
            Return ONLY the JSON object, no extra text.""",
            
            'pay_stub': """Analyze this pay stub and extract the following in JSON format:
            {
                "employer_name": "string",
                "employee_name": "string",
                "pay_period_start": "YYYY-MM-DD",
                "pay_period_end": "YYYY-MM-DD",
                "gross_pay": number,
                "net_pay": number,
                "federal_tax": number,
                "state_tax": number,
                "ytd_gross": number,
                "pay_frequency": "weekly|biweekly|semimonthly|monthly",
                "is_valid_paystub": boolean,
                "confidence_score": number between 0-100
            }
            Return ONLY the JSON object, no extra text.""",
            
            'bank_statement': """Analyze this bank statement and extract the following in JSON format:
            {
                "bank_name": "string",
                "account_holder": "string",
                "account_type": "checking|savings|money_market",
                "statement_period_start": "YYYY-MM-DD",
                "statement_period_end": "YYYY-MM-DD",
                "beginning_balance": number,
                "ending_balance": number,
                "total_deposits": number,
                "total_withdrawals": number,
                "average_daily_balance": number,
                "is_valid_statement": boolean,
                "confidence_score": number between 0-100
            }
            Return ONLY the JSON object, no extra text."""
        }
        
        analysis_prompt = prompts.get(doc_type, prompts['w2'])
        
        # Process based on file type
        try:
            if is_image:
                import PIL.Image
                import io
                image = PIL.Image.open(io.BytesIO(content))
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[analysis_prompt, image]
                )
            elif is_pdf:
                encoded = base64.standard_b64encode(content).decode('utf-8')
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[
                        analysis_prompt,
                        {"mime_type": "application/pdf", "data": encoded}
                    ]
                )
            else:
                try:
                    text_content = content.decode('utf-8')
                except:
                    text_content = content.decode('latin-1')
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[f"{analysis_prompt}\n\nDocument content:\n{text_content[:50000]}"]
                )
            
            # Parse response
            response_text = response.text.strip()
            if response_text.startswith('```'):
                response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
                response_text = re.sub(r'\n?```$', '', response_text)
            
            analysis = json.loads(response_text)
            
        except Exception as e:
            logger.warning(f"AI analysis failed: {e}")
            analysis = {"status": "uploaded", "details": "AI analysis failed, document marked as uploaded"}
        
        logger.info(f"Successfully processed {doc_type}: {file.filename}")
        
        return JSONResponse(content={
            "success": True,
            "doc_type": doc_type,
            "filename": file.filename,
            "file_size": file_size,
            "verified": analysis.get('confidence_score', 50) >= 60 if isinstance(analysis, dict) else True,
            "analysis": analysis
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading income document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )
