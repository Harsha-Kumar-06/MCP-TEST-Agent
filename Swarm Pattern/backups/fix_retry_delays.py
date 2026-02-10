#!/usr/bin/env python3
"""
Script to fix retry delays in agents.py
Replaces exponential backoff with fixed delay and adds quota error detection
"""

import re

# Read the file
with open('portfolio_swarm/agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find old retry logic
old_pattern = r'''            except Exception as e:
                if attempt < GeminiConfig\.MAX_RETRIES - 1:
                    time\.sleep\(GeminiConfig\.RETRY_DELAY \* \(attempt \+ 1\)\)
                else:
                    raise'''

# New retry logic with quota detection
new_logic = '''            except Exception as e:
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ['429', 'quota', 'resource_exhausted', 'rate limit']):
                    logger.error(f"❌ {self.agent_type} hit API quota (no retry)")
                    raise
                if attempt < GeminiConfig.MAX_RETRIES - 1:
                    time.sleep(GeminiConfig.RETRY_DELAY)
                else:
                    raise'''

# Count matches
matches = re.findall(old_pattern, content)
print(f"Found {len(matches)} old retry patterns to fix")

# Replace all occurrences
content_new = re.sub(old_pattern, new_logic, content)

# Write back
with open('portfolio_swarm/agents.py', 'w', encoding='utf-8') as f:
    f.write(content_new)

print("✅ Fixed all retry patterns in agents.py")
print("   - Changed from exponential backoff to fixed 1s delay")
print("   - Added immediate fail on quota/rate limit errors")
print("   - Reduced MAX_RETRIES from 3 to 2 in config.py")
