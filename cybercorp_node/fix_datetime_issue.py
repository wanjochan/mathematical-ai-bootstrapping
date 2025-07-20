"""
Fix datetime issue in client.py
"""

import re

# Read the client.py file
with open('client.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check for potential issues
print("Checking for datetime issues...")

# Find all datetime usages
datetime_pattern = r'\bdatetime\b'
matches = list(re.finditer(datetime_pattern, content))

print(f"Found {len(matches)} occurrences of 'datetime'")

# Check each line
lines = content.split('\n')
for match in matches:
    line_start = content.rfind('\n', 0, match.start()) + 1
    line_end = content.find('\n', match.end())
    if line_end == -1:
        line_end = len(content)
    
    line_num = content[:match.start()].count('\n') + 1
    line_content = content[line_start:line_end].strip()
    
    print(f"Line {line_num}: {line_content}")

# The issue might be that datetime is imported at module level but re-imported locally
# Let's check if there's a function that might shadow the global datetime

print("\n\nChecking for potential shadowing...")

# Look for functions that might have local datetime imports
local_import_pattern = r'def\s+\w+\([^)]*\):[^}]*?from\s+datetime\s+import\s+datetime'
local_imports = list(re.finditer(local_import_pattern, content, re.DOTALL))

if local_imports:
    print(f"Found {len(local_imports)} functions with local datetime imports")
    for match in local_imports:
        func_start = content.rfind('def ', 0, match.start())
        func_name_end = content.find('(', func_start)
        func_name = content[func_start+4:func_name_end]
        print(f"  - Function: {func_name}")

# The real issue might be in response_formatter usage
print("\n\nChecking response_formatter imports...")

# Check if format_success, format_error are imported
formatter_import = re.search(r'from\s+utils\.response_formatter\s+import\s+([^\\n]+)', content)
if formatter_import:
    imports = formatter_import.group(1)
    print(f"Imported from response_formatter: {imports}")
    
    # Check if these are used before being imported
    for func in ['format_success', 'format_error']:
        first_use = content.find(f'{func}(')
        import_line = content.find(f'from utils.response_formatter import')
        if first_use != -1 and import_line != -1 and first_use < import_line:
            print(f"WARNING: {func} used before import!")

print("\nAnalysis complete.")