import re

text = '''My tech portfolio:
15000 AAPL @ $185 (bought for $140)
8000 MSFT shares at $410, paid $305
3000 Tesla at $245'''

# All 18 patterns from text_parser.py
position_patterns = [
    # Pattern 1-10 (narrative formats)
    r'\(([A-Z]{2,5})\).*?purchased\s+([\d,]+)\s+shares.*?(\d+\.?\d*)\s+per\s+share.*?[Cc]urrent\s+price.*?(\d+\.?\d*)',
    r'\(([A-Z]{2,5})\)[^\d]*(\d{1,3}(?:,\d{3})*)\s+shares[^\d]*(\d+\.?\d*)[^\d]*currently\s+trading[^\d]*(\d+\.?\d*)',
    r'\(([A-Z]{2,5})\).*?(\d{1,3}(?:,\d{3})*)\s+shares.*?\$(\d+\.?\d*).*?current.*?\$(\d+\.?\d*)',
    r'([A-Z]{2,5}):?\s+(\d{1,3}(?:,\d{3})*)\s+shares.*?bought.*?\$(\d+\.?\d*).*?now.*?\$(\d+\.?\d*)',
    r'([A-Z]{2,5}).*?Position:\s*(\d{1,3}(?:,\d{3})*)\s+shares[^\d]*cost[^\d]*(\d+\.?\d*)[^\d]*current[^\d]*(\d+\.?\d*)',
    r'\(([A-Z]{2,5})\).*?[Bb]ought\s+([\d,]+)\s+shares.*?per\s+share.*?(\d+\.?\d*).*?trading.*?(\d+\.?\d*)',
    r'\(([A-Z]{2,5})\)[^\d]*[Bb]ought\s+([\d,]+)\s+([A-Z]{2,5})\s+shares[^\d]*(\d+\.?\d*)[^\d]*current.*?(\d+\.?\d*)',
    r'([A-Z]{2,5})\s+holding:\s*(\d{1,3}(?:,\d{3})*)[^\d]*purchase[^\d]*(\d+\.?\d*)[^\d]*market[^\d]*(\d+\.?\d*)',
    r'\(([A-Z]{2,5})\).*?holding\s+of\s+(\d{1,3}(?:,\d{3})*)[^\d]*acquired[^\d]*(\d+\.?\d*)[^\d]*valued[^\d]*(\d+\.?\d*)',
    r'\(([A-Z]{2,5})\)[^\d]*[Bb]ought\s+([\d,]+)\s+shares[^\d]*(\d+\.?\d*)[^\d]*currently\s+trading[^\d]*(\d+\.?\d*)',
    
    # Pattern 11-18 (simple formats)
    r'[Oo]wn\s+([\d,]+)\s+shares\s+of\s+\w+\s+\(([A-Z]{2,5})\)\s+bought[^\d]*(\d+\.?\d*)[^\d]+now[^\d]*(\d+\.?\d*)',
    r'([\d,]+)\s+\w+\s+\(([A-Z]{2,5})\)\s+shares[^\d]*cost\s+basis[^\d]*(\d+\.?\d*)[^\d]*current\s+price[^\d]*(\d+\.?\d*)',
    r'([A-Z]{2,5}):\s*([\d,]+[kKmM]?)\s+shares[^\d]*purchased[^\d]+(\d+\.?\d*)[^\d]+currently[^\d]*(\d+\.?\d*)',
    r'([A-Z]{2,5}):\s*([\d,]+[kKmM]?)\s+shares[^\d]*cost[^\d]+(\d+\.?\d*)[^\d]+now[^\d]*(\d+\.?\d*)',
    r'([A-Z]{2,5}):\s*([\d,]+[kKmM]?)\s+shares[^\d]*basis[^\d]+(\d+\.?\d*)[^\d]+price[^\d]*(\d+\.?\d*)',
    r'([\d,]+[kKmM]?)\s+([A-Z]{2,5})\s+@[^\d]*(\d+\.?\d*)\s*\([^\d$]*\$?(\d+\.?\d*)\)',
    r'([\d,]+[kKmM]?)\s+([A-Z]{2,5})\s+shares\s+at[^\d]+(\d+\.?\d*)[^\d,]*,\s*paid[^\d]+(\d+\.?\d*)',
    r'([\d,]+[kKmM]?)\s+([A-Z][A-Za-z]{1,4})\s+at[^\d]+(\d+\.?\d*)(?![^\n]*paid)',
]

print("Searching for MSFT matches...")
for i, pattern in enumerate(position_patterns, 1):
    matches = list(re.finditer(pattern, text, re.IGNORECASE | re.DOTALL))
    msft_matches = [m for m in matches if 'msft' in m.group(0).lower()]
    if msft_matches:
        print(f"\nPattern {i} matched MSFT:")
        for m in msft_matches:
            print(f"  Groups: {m.groups()}")
            print(f"  Text: '{m.group(0)}'")
