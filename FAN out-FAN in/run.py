"""
Run the application using uvicorn directly.
Alternative to main.py for development.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "loan_underwriter.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="debug"
    )
