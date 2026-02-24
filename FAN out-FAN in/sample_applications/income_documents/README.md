# Sample Income Documents

This folder contains sample income documentation files for testing the loan underwriter application's document upload and verification features.

## Available Documents

### John Wilson (Employed - W2 Employee)
| Document Type | Filename | Description |
|---------------|----------|-------------|
| W2 Form | `sample_w2_john_wilson_2025.txt` | W2 showing $127,500 annual income |
| Tax Return | `sample_tax_return_john_wilson_2025.txt` | Form 1040 with AGI of $133,390 |
| Pay Stub | `sample_pay_stub_john_wilson_jan2026.txt` | Semi-monthly pay stub, $10,625 gross |
| Bank Statement | `sample_bank_statement_john_wilson_jan2026.txt` | January 2026, avg balance $26,012 |

### Sarah Chen (Self-Employed - Freelancer)
| Document Type | Filename | Description |
|---------------|----------|-------------|
| Tax Return | `sample_tax_return_sarah_chen_2025.txt` | Schedule C with $98,500 net profit |
| Bank Statement | `sample_bank_statement_sarah_chen_jan2026.txt` | Business checking, $45,000 avg balance |

### Test Files for Identity Mismatch Detection
| Document Type | Filename | Description |
|---------------|----------|-------------|
| Bank Statement | `MISMATCHED_bank_statement_different_person.txt` | **TEST FILE** - Different person's name to trigger identity mismatch |

## How to Use

1. Navigate to the **New Application** page
2. Scroll to the **Income Documentation** section
3. Click on each upload field and select the appropriate sample file:
   - **W2 Forms**: Upload `sample_w2_*.txt`
   - **Tax Returns**: Upload `sample_tax_return_*.txt`
   - **Pay Stubs**: Upload `sample_pay_stub_*.txt`
   - **Bank Statements**: Upload `sample_bank_statement_*.txt`

4. The system will:
   - Accept the file upload
   - Analyze document content using AI
   - Extract key financial information
   - Calculate documentation completeness score
   - **Validate that all documents belong to the same person**

## Cross-Document Identity Validation (NEW)

The system validates that all uploaded documents belong to the same applicant:

- **Names** extracted from each document are compared
- **SSN last 4 digits** are cross-referenced where available
- **Mismatches trigger fraud flags** with specific details

### Testing Identity Mismatch
To test this feature:
1. Upload John Wilson's W2 (`sample_w2_john_wilson_2025.txt`)
2. Upload the mismatched bank statement (`MISMATCHED_bank_statement_different_person.txt`)
3. Submit the application
4. The fraud detection will show:
   - "Cross-Doc Identity: MISMATCH" badge
   - Specific flags like "NAME MISMATCH: Bank Statement shows 'Michael Thompson' but applicant is 'John Wilson'"

## Documentation Completeness Scoring

The fraud detection agent evaluates documentation based on employment type:

### For W2 Employees:
- W2 provided: 40% weight
- Tax returns: 30% weight
- Pay stubs: 20% weight
- Bank statements: 10% weight

### For Self-Employed:
- Tax returns: 40% weight
- Bank statements: 30% weight
- W2/1099: 20% weight
- Pay stubs: 10% weight

## Status Thresholds
- **Complete** (≥85%): Green badge, full verification
- **Adequate** (≥60%): Blue badge, standard approval
- **Incomplete** (≥40%): Yellow warning, additional docs requested
- **Insufficient** (<40%): Red alert, cannot proceed without more documents
