import re

text = '''My tech portfolio:
15000 AAPL @ $185 (bought for $140)
8000 MSFT shares at $410, paid $305
3000 Tesla at $245'''

patterns = [
    # Pattern 16
    r'([\d,]+[kKmM]?)\s+([A-Z]{2,5})\s+@[^\d]*(\d+\.?\d*)\s*\([^\d$]*\$?(\d+\.?\d*)\)',
    # Pattern 17
    r'([\d,]+[kKmM]?)\s+([A-Z]{2,5})\s+shares\s+at[^\d]+(\d+\.?\d*)[^\d,]*,\s*paid[^\d]+(\d+\.?\d*)',
    # Pattern 18
    r'([\d,]+[kKmM]?)\s+([A-Z][A-Za-z]{1,4})\s+at[^\d]+(\d+\.?\d*)(?![^\n]*paid)',
]

for i, pattern in enumerate(patterns, 16):
    print(f"\nPattern {i}:")
    matches = list(re.finditer(pattern, text, re.IGNORECASE))
    if matches:
        for m in matches:
            print(f"  {m.groups()} - '{m.group(0)}'")
    else:
        print("  No matches")
