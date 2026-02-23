SAMPLE LOAN APPLICATIONS FOR TESTING
=====================================

This folder contains sample mortgage application documents that you can 
use to test the AI-powered document upload and auto-fill feature.

FILES INCLUDED:
---------------
1. sample_application_1.txt
   - Applicant: Michael Johnson
   - Property: San Francisco condo ($925,000)
   - Income: $165,000 (employed)

2. sample_application_2.txt  
   - Applicant: Sarah Williams
   - Property: Austin single family ($495,000)
   - Income: $128,000 (self-employed)

3. sample_application_3_highvalue.txt
   - Applicant: Robert Chen
   - Property: Palo Alto luxury home ($3,250,000)
   - Income: $575,000 (executive)
   - Jumbo loan application

4. sample_application_4_firsttime.txt
   - Applicant: Emily Rodriguez
   - Property: Boulder townhouse ($385,000)
   - Income: $78,000 (nurse)
   - First-time homebuyer

HOW TO USE:
-----------
1. Start the application: python main.py
2. Go to: http://127.0.0.1:8000/application
3. Click "Choose Document" in the upload section
4. Select any of these sample .txt files
5. Watch as AI extracts the data and auto-fills the form!

NOTES:
------
- The AI extraction works with various document formats
- It can handle different layouts and writing styles
- Some fields may not be extracted if the format is unclear
- You can manually adjust any auto-filled values
