import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract JavaScript content
script_start = content.find('<script>')
script_end = content.find('</script>')

if script_start == -1 or script_end == -1:
    print("ERROR: Script tags not found")
    exit(1)

js_content = content[script_start + 8:script_end]

# Count braces
open_braces = js_content.count('{')
close_braces = js_content.count('}')
open_parens = js_content.count('(')
close_parens = js_content.count(')')
open_brackets = js_content.count('[')
close_brackets = js_content.count(']')

print(f"JavaScript Analysis:")
print(f"  Open braces: {open_braces}")
print(f"  Close braces: {close_braces}")
print(f"  Difference: {open_braces - close_braces}")
print(f"  Open parens: {open_parens}")
print(f"  Close parens: {close_parens}")
print(f"  Difference: {open_parens - close_parens}")
print(f"  Open brackets: {open_brackets}")
print(f"  Close brackets: {close_brackets}")
print(f"  Difference: {open_brackets - close_brackets}")

# Check for common issues
lines = js_content.split('\n')
for i, line in enumerate(lines, 1):
    # Check for syntax issues
    if '}' in line and '{' not in line:
        if i < len(lines):
            next_line = lines[i].strip() if i < len(lines) else ""
            if next_line and not next_line.startswith('//') and not next_line.startswith('}'):
                stripped = line.strip()
                if stripped.startswith('}') and not stripped.endswith(';') and not stripped.endswith('}'):
                    if 'else' not in next_line and 'catch' not in next_line:
                        print(f"Line {i}: Potential issue after closing brace: '{line.strip()}'")

print("\nScript location in file:")
print(f"  Start: line {content[:script_start].count(chr(10)) + 1}")
print(f"  End: line {content[:script_end].count(chr(10)) + 1}")
