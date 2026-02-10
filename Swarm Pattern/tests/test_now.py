import re

text = "bought at $150, now at $185"

# Pattern 11
p11 = r'[Oo]wn\s+([\d,]+)\s+shares\s+of\s+\w+\s+\(([A-Z]{2,5})\)\s+bought[^\d]*(\d+\.?\d*)[^\d]+now[^\d]*(\d+\.?\d*)'

# Pattern 18
p18 = r'([\d,]+[kKmM]?)\s+([A-Z][A-Za-z]{1,4})\s+at[^\d]+(\d+\.?\d*)(?![^\n]*paid)'

print("Text:", text)
print()
print("Pattern 11:")
for m in re.finditer(p11, text, re.I):
    print(f"  Groups: {m.groups()}, ticker={m.group(2)}")

print("\nPattern 18:")
for m in re.finditer(p18, text, re.I):
    print(f"  Groups: {m.groups()}, ticker={m.group(2)}")
