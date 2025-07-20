"""Fix Win32Backend imports in client.py"""

import re

# Read client.py
with open('client.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find Win32Backend() instantiations
pattern = r'(\s+)win32_backend = Win32Backend\(\)'

# Replacement that adds import check
replacement = r'''\1# Import on demand
\1global Win32Backend
\1if Win32Backend is None:
\1    from utils.win32_backend import Win32Backend
\1win32_backend = Win32Backend()'''

# Replace all occurrences
content = re.sub(pattern, replacement, content)

# Write back
with open('client.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed Win32Backend imports in client.py")