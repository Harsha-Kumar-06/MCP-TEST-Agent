# Test File with Multiple Security and Code Issues
# Upload this to test the copy-paste fix feature

import os
import sqlite3

def authenticate_user(username, password):
    """Login function with SQL injection vulnerability"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # VULNERABILITY: SQL Injection
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    
    user = cursor.fetchone()
    if user:
        print("Login successful!")
        return True
    else:
        print("Login failed!")
        return False

def load_user_file(filename):
    """File handling with path traversal vulnerability"""
    # VULNERABILITY: Path Traversal
    file_path = "/uploads/" + filename
    
    # Missing error handling
    f = open(file_path, 'r')
    content = f.read()
    # BUG: File not closed (resource leak)
    
    return content

def calculate_average(numbers):
    """Inefficient calculation"""
    # PERFORMANCE ISSUE: O(n²) when O(n) is possible
    total = 0
    count = 0
    for i in range(len(numbers)):
        for j in range(len(numbers)):
            if i == j:
                total += numbers[i]
                count += 1
    
    return total / count

def process_data(user_input):
    """Dangerous eval usage"""
    # CRITICAL: Code injection via eval
    result = eval(user_input)
    return result

def find_duplicates(data_list):
    """Finding duplicates inefficiently"""
    duplicates = []
    # PERFORMANCE: Nested loop - O(n²)
    for i in range(len(data_list)):
        for j in range(i + 1, len(data_list)):
            if data_list[i] == data_list[j]:
                if data_list[i] not in duplicates:
                    duplicates.append(data_list[i])
    return duplicates

# Usage examples
username = input("Username: ")
password = input("Password: ")
authenticate_user(username, password)

# XSS vulnerability in web context
user_comment = "<script>alert('XSS')</script>"
print(f"Comment: {user_comment}")  # Should be escaped

# Hardcoded credentials
API_KEY = "sk_live_1234567890abcdef"
DB_PASSWORD = "admin123"
