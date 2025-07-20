"""Fix global declarations in client.py"""

# Read the file
with open('client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track if we're in a function and need to add global declaration
in_execute_command = False
global_added = False

new_lines = []

for i, line in enumerate(lines):
    # Check if we're entering _execute_command function
    if 'async def _execute_command' in line:
        in_execute_command = True
        new_lines.append(line)
        # Add global declaration at the beginning of the function
        indent = '        '  # 8 spaces for method indentation
        new_lines.append(f'{indent}global Win32Backend\n')
        global_added = True
        continue
    
    # Skip existing global Win32Backend lines if we already added it
    if in_execute_command and 'global Win32Backend' in line and global_added:
        continue
    
    # Check if we're exiting the function
    if in_execute_command and line.strip() and not line.startswith(' '):
        in_execute_command = False
        global_added = False
    
    new_lines.append(line)

# Write back
with open('client.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fixed global declarations in client.py")