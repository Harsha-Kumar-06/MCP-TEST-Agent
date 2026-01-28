"""
Test script to demonstrate the new code/text fix generation feature
"""

# Example documents with issues that should generate fixes

# Test Case 1: Python code with security vulnerability
test_code_with_sql_injection = """
# User Authentication System

def login_user(username, password):
    '''Handle user login'''
    # Connect to database
    db = sqlite3.connect('users.db')
    cursor = db.cursor()
    
    # VULNERABLE: Direct string concatenation in SQL query
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    
    user = cursor.fetchone()
    
    if user:
        return {"status": "success", "user_id": user[0]}
    else:
        return {"status": "failed", "message": "Invalid credentials"}
"""

# Test Case 2: Text with grammar errors
test_text_with_grammar = """
# Project Report

This report discuss the findings of our researchs into artificial intelligence applications. 
The team have identified several key areas where AI can improves efficiency.

Between you and I, the results was better then expected. Their are many opportunities for 
optimization that has been overlooked in the passed. 

The data shows that less employees can do more work when they have access to AI tools. 
This phenomena is particularly evident in customer service departments.
"""

# Test Case 3: Code with performance issues
test_code_with_performance_issue = """
def find_duplicates(data_list):
    '''Find duplicate items in a list'''
    duplicates = []
    
    # INEFFICIENT: O(n²) time complexity
    for i in range(len(data_list)):
        for j in range(i + 1, len(data_list)):
            if data_list[i] == data_list[j]:
                if data_list[i] not in duplicates:
                    duplicates.append(data_list[i])
    
    return duplicates

# Example usage
large_dataset = list(range(10000)) * 2  # 20,000 items
result = find_duplicates(large_dataset)  # This will be VERY slow
"""

print("🧪 Test Cases for Code Fix Generation Feature\n")
print("=" * 80)
print("\n📝 Test Case 1: Security Vulnerability (SQL Injection)")
print("-" * 80)
print(test_code_with_sql_injection)
print("\n" + "=" * 80)
print("\n📝 Test Case 2: Grammar Errors")
print("-" * 80)
print(test_text_with_grammar)
print("\n" + "=" * 80)
print("\n📝 Test Case 3: Performance Issue")
print("-" * 80)
print(test_code_with_performance_issue)
print("\n" + "=" * 80)
print("\n✅ Run these through the API with appropriate questions:")
print("   • 'Find security vulnerabilities and provide fixes'")
print("   • 'Identify and correct all grammar errors'")
print("   • 'Find performance issues and suggest optimized code'")
print("\n💡 The system will now generate:")
print("   ✓ Location markers [P#:L#-#]")
print("   ✓ Current (incorrect) code/text")
print("   ✓ Fixed (corrected) code/text ready to copy-paste")
print("   ✓ Explanation of why the fix works")
print("=" * 80)
