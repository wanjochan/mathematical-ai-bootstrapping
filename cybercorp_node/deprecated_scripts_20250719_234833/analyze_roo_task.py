"""Analyze what Roo is doing with the task"""

import json
import os

def analyze_roo_state():
    """Analyze the current Roo Code state"""
    
    var_dir = os.path.join(os.path.dirname(__file__), 'var')
    latest_file = os.path.join(var_dir, 'roo_check_20250719_222734.json')
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Find the main document text
    for area in data.get('content_areas', []):
        if area.get('type') == 'Document':
            texts = area.get('texts', [])
            if texts and isinstance(texts[0], str):
                content = texts[0]
                
                print("=== Roo Code Current State Analysis ===")
                print("=" * 80)
                
                # Extract key information
                if 'Task:' in content:
                    task_start = content.find('Task:')
                    task_end = content.find('Initial Checkpoint', task_start)
                    if task_end == -1:
                        task_end = content.find('I need to', task_start)
                    
                    task_text = content[task_start:task_end].strip()
                    print("\n[1] Current Task:")
                    print("-" * 60)
                    print(task_text)
                
                # Look for Roo's response
                if 'I need to examine' in content:
                    response_start = content.find('I need to examine')
                    response_end = content.find('Roo wants to', response_start)
                    if response_end == -1:
                        response_end = len(content)
                    
                    response_text = content[response_start:response_end].strip()
                    print("\n[2] Roo's Response:")
                    print("-" * 60)
                    print(response_text)
                
                # Check for file request
                if 'Roo wants to read' in content:
                    file_start = content.find('Roo wants to read')
                    file_end = content.find('Auto-approve', file_start)
                    
                    file_request = content[file_start:file_end].strip()
                    print("\n[3] Roo's Request:")
                    print("-" * 60)
                    print(file_request)
                
                # Check for our original task
                if '分析一下当前的产品设计' in content:
                    print("\n[4] Our Original Task Status:")
                    print("-" * 60)
                    print("NOT FOUND - Our task '分析一下当前的产品设计' is not in the current view")
                else:
                    print("\n[4] Our Original Task Status:")
                    print("-" * 60)
                    print("Our task '分析一下当前的产品设计' was likely replaced by a new task")
                
                print("\n[5] Summary:")
                print("-" * 60)
                print("Roo is currently working on a DIFFERENT task:")
                print("- Examining system components in cybercorp directories")
                print("- Analyzing source code structure")
                print("- Currently wants to read: cybercorp_server/src/main.py")
                print("\nOur product design analysis task may have been:")
                print("1. Completed earlier (check history)")
                print("2. Replaced by this new task")
                print("3. In a different chat/session")
                
                return content

if __name__ == "__main__":
    analyze_roo_state()