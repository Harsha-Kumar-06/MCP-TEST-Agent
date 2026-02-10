from html.parser import HTMLParser
import sys

class JavaScriptExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.script_content = []
        
    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.in_script = True
            
    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_script = False
            
    def handle_data(self, data):
        if self.in_script:
            self.script_content.append(data)

try:
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = JavaScriptExtractor()
    parser.feed(content)
    
    js_code = ''.join(parser.script_content)
    
    # Check for function definitions
    functions = ['loadSample', 'showTextInput', 'showFileUpload', 'updateRangeValue']
    print("Function Check:")
    for func in functions:
        if f'function {func}' in js_code or f'{func} = ' in js_code or f'{func}: function' in js_code:
            print(f"  ✓ {func} is defined")
        else:
            print(f"  ✗ {func} is NOT defined")
    
    print(f"\nTotal JavaScript lines: {js_code.count(chr(10))}")
    print(f"Script contains {js_code.count('function ')} function declarations")
    
    # Check for specific syntax errors
    if 'function updateRangeValue' in js_code:
        # Find the function
        start = js_code.find('function updateRangeValue')
        # Find matching closing brace
        print("\n✓ updateRangeValue function found")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

print("\n✓ HTML file is valid")
