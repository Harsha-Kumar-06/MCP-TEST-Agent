import re

# Pattern 16 from the file
pattern = r'([\d,]+[kKmM]?)\s+([A-Z]{2,5})\s+@[^\d]*(\d+\.?\d*)\s*\([^$]*\$?(\d+\.?\d*)\)'

text = '15000 AAPL @ $185 (bought for $140)'

print("Testing pattern 16:")
print(f"Pattern: {repr(pattern)}")
print(f"Text: {repr(text)}")
print()

# Test with different flag combinations
print("Without flags:")
m = re.search(pattern, text)
if m:
    print(f"  Groups: {m.groups()}")
    print(f"  Full match: {repr(m.group(0))}")
else:
    print("  No match")

print("\nWith IGNORECASE:")
m = re.search(pattern, text, re.IGNORECASE)
if m:
    print(f"  Groups: {m.groups()}")
    print(f"  Full match: {repr(m.group(0))}")
else:
    print("  No match")

print("\nWith IGNORECASE | DOTALL:")
m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
if m:
    print(f"  Groups: {m.groups()}")
    print(f"  Full match: {repr(m.group(0))}")
else:
    print("  No match")

print("\n\nUsing finditer (like in parser):")
for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
    print(f"  Groups: {match.groups()}")
    print(f"  Full match: {repr(match.group(0))}")
    
    # Show each group explicitly
    for i in range(len(match.groups())):
        print(f"  Group {i+1}: {repr(match.group(i+1))}")
