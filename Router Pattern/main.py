"""
Main entry point for running CorpAssist interactively.

Usage:
    python main.py

Or use ADK CLI:
    adk run helpdesk_bot
    adk web  # For web UI
"""

import asyncio
import os
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from helpdesk_bot import root_agent


# Load environment variables
load_dotenv()


async def main():
    """Run CorpAssist in interactive mode."""
    
    # Verify API key is set
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable not set.")
        print("Please set your Google API key in .env file or environment.")
        return
    
    # Create session service for conversation memory
    session_service = InMemorySessionService()
    
    # Create runner
    runner = Runner(
        agent=root_agent,
        app_name="helpdesk_bot",
        session_service=session_service,
    )
    
    # Create a session
    session = await session_service.create_session(
        app_name="helpdesk_bot",
        user_id="user_001",
    )
    
    print("=" * 60)
    print("  CorpAssist - Your Workplace Assistant")
    print("=" * 60)
    print("\nWelcome! I can help you with:")
    print("  - HR: Leave, benefits, payroll, policies")
    print("  - IT: Hardware, software, access, technical issues")
    print("  - Sales: Customer info, quotes, CRM")
    print("  - Legal: Contracts, compliance, NDAs")
    print("\nType 'quit' or 'exit' to end the conversation.\n")
    print("-" * 60)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "bye", "q"]:
                print("\nThank you for using HelpDesk Bot. Goodbye!")
                break
            
            # Create the user message
            content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_input)]
            )
            
            # Run the agent
            print("\nHelpDesk Bot: ", end="", flush=True)
            
            async for event in runner.run_async(
                session_id=session.id,
                user_id="user_001",
                new_message=content,
            ):
                # Handle different event types
                if hasattr(event, "content") and event.content:
                    if hasattr(event.content, "parts"):
                        for part in event.content.parts:
                            if hasattr(part, "text") and part.text:
                                print(part.text, end="", flush=True)
            
            print()  # New line after response
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            continue


if __name__ == "__main__":
    asyncio.run(main())
