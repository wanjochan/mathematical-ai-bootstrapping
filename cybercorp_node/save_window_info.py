"""Save window information to var directory"""

import json
import os
from datetime import datetime

def save_window_info(username, window_data):
    """Save window information to var directory"""
    
    # Ensure var directory exists
    var_dir = os.path.join(os.path.dirname(__file__), 'var')
    os.makedirs(var_dir, exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'windows_{username}_{timestamp}.json'
    filepath = os.path.join(var_dir, filename)
    
    # Save data
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(window_data, f, indent=2, ensure_ascii=False)
    
    print(f"Window information saved to: {filepath}")
    return filepath

def save_vscode_structure(username, vscode_data):
    """Save VSCode structure to var directory"""
    
    var_dir = os.path.join(os.path.dirname(__file__), 'var')
    os.makedirs(var_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'vscode_structure_{username}_{timestamp}.json'
    filepath = os.path.join(var_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(vscode_data, f, indent=2, ensure_ascii=False)
    
    print(f"VSCode structure saved to: {filepath}")
    return filepath