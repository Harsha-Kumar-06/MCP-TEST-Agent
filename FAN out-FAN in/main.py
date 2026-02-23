"""
Main entry point for the Loan Underwriter application.
Run with: python main.py
"""

import uvicorn
from loan_underwriter.config import config


def main():
    """Run the FastAPI application."""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🏦  M O R T G A G E C L E A R                         ║
    ║   Multi-Agent Mortgage Underwriting System               ║
    ║                                                           ║
    ║   Fan-Out/Fan-In Architecture for Rapid Processing       ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    print(f"Starting server at http://{config.host}:{config.port}")
    print(f"API Documentation: http://{config.host}:{config.port}/docs")
    print(f"Debug Mode: {config.debug}")
    print("\nPress Ctrl+C to stop the server.\n")
    
    uvicorn.run(
        "loan_underwriter.app:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="debug" if config.debug else "info"
    )


if __name__ == "__main__":
    main()
