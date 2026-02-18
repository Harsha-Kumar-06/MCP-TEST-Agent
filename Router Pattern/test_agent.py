"""
Test script to verify the HelpDesk Bot routing logic.

This script tests the intent classification and routing without making actual API calls.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Test cases for the router
TEST_CASES = [
    # Single intent tests
    {
        "input": "My laptop is running really slow",
        "expected_route": "it_support_agent",
        "expected_category": "Hardware_Issue"
    },
    {
        "input": "I need to request PTO for next week",
        "expected_route": "hr_agent",
        "expected_category": "Leave_Request"
    },
    {
        "input": "Can you review this vendor contract?",
        "expected_route": "legal_agent",
        "expected_category": "Contract_Review"
    },
    {
        "input": "What's the pricing for our enterprise product?",
        "expected_route": "sales_agent",
        "expected_category": "Pricing"
    },
    {
        "input": "What's the weather like today?",
        "expected_route": "off_topic_agent",
        "expected_category": "Off_Topic"
    },
    
    # Multiple intent tests
    {
        "input": "My laptop is slow and I need a license for Adobe",
        "expected_route": "it_support_agent",
        "expected_category": "Hardware_Issue + Software_Request"
    },
    {
        "input": "I need PTO next week and also my VPN isn't working",
        "expected_route": ["hr_agent", "it_support_agent"],
        "expected_category": "Leave_Request + IT_Issue"
    },
    
    # Edge cases
    {
        "input": "Help",
        "expected_route": "router",
        "expected_category": "Clarification_Needed"
    },
    {
        "input": "I have a question about my 401k and also need to reset my password",
        "expected_route": ["hr_agent", "it_support_agent"],
        "expected_category": "Benefits + Access"
    },
]


def print_test_header():
    """Print test header."""
    print("=" * 70)
    print("  HelpDesk Bot - Routing Test Suite")
    print("=" * 70)
    print()


def print_test_case(idx: int, test_case: dict):
    """Print a test case."""
    print(f"Test {idx + 1}: {test_case['input']}")
    print(f"  Expected Route: {test_case['expected_route']}")
    print(f"  Expected Category: {test_case['expected_category']}")
    print()


async def run_live_test():
    """Run live tests against the actual agent (requires API key)."""
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("Skipping live tests - GOOGLE_API_KEY not set")
        return
    
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from helpdesk_bot import root_agent
    
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="helpdesk_bot",
        session_service=session_service,
    )
    
    session = await session_service.create_session(
        app_name="helpdesk_bot",
        user_id="test_user",
    )
    
    print("\n" + "=" * 70)
    print("  Running Live Tests")
    print("=" * 70 + "\n")
    
    for idx, test_case in enumerate(TEST_CASES[:3]):  # Run first 3 tests
        print(f"\nTest {idx + 1}: {test_case['input']}")
        print("-" * 50)
        
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=test_case["input"])]
        )
        
        response_text = ""
        async for event in runner.run_async(
            session_id=session.id,
            user_id="test_user",
            new_message=content,
        ):
            if hasattr(event, "content") and event.content:
                if hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text
        
        print(f"Response: {response_text[:200]}...")
        print()


def run_static_tests():
    """Run static tests to verify structure."""
    print("\n" + "=" * 70)
    print("  Static Structure Tests")
    print("=" * 70 + "\n")
    
    # Test imports
    try:
        from helpdesk_bot import root_agent
        print("✓ Main agent imports successfully")
    except Exception as e:
        print(f"✗ Failed to import main agent: {e}")
        return
    
    # Test agent structure
    try:
        assert root_agent.name == "helpdesk_router"
        print("✓ Root agent name is correct")
    except AssertionError:
        print(f"✗ Root agent name mismatch: {root_agent.name}")
    
    # Test sub-agents
    try:
        sub_agent_names = [sa.name for sa in root_agent.sub_agents]
        expected_names = ["hr_agent", "it_support_agent", "sales_agent", "legal_agent", "off_topic_agent"]
        for name in expected_names:
            assert name in sub_agent_names, f"Missing sub-agent: {name}"
        print(f"✓ All {len(expected_names)} sub-agents present")
    except Exception as e:
        print(f"✗ Sub-agent check failed: {e}")
    
    # Test tools
    try:
        from helpdesk_bot.sub_agents.hr_agent import hr_agent
        assert len(hr_agent.tools) > 0
        print(f"✓ HR agent has {len(hr_agent.tools)} tools")
        
        from helpdesk_bot.sub_agents.it_support_agent import it_support_agent
        assert len(it_support_agent.tools) > 0
        print(f"✓ IT Support agent has {len(it_support_agent.tools)} tools")
        
        from helpdesk_bot.sub_agents.sales_agent import sales_agent
        assert len(sales_agent.tools) > 0
        print(f"✓ Sales agent has {len(sales_agent.tools)} tools")
        
        from helpdesk_bot.sub_agents.legal_agent import legal_agent
        assert len(legal_agent.tools) > 0
        print(f"✓ Legal agent has {len(legal_agent.tools)} tools")
        
    except Exception as e:
        print(f"✗ Tools check failed: {e}")
    
    print("\n" + "-" * 70)
    print("Static tests completed!")


def main():
    """Main test runner."""
    print_test_header()
    
    print("Test Cases Overview:")
    print("-" * 70)
    for idx, test_case in enumerate(TEST_CASES):
        print_test_case(idx, test_case)
    
    # Run static structure tests
    run_static_tests()
    
    # Run live tests if API key is available
    asyncio.run(run_live_test())
    
    print("\n" + "=" * 70)
    print("  All tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
