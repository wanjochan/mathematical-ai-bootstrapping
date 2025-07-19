"""Extract Roo Code dialog content from saved scan"""

import json

def extract_roo_code_content():
    print("Extracting Roo Code Dialog Content")
    print("=" * 60)
    
    try:
        with open('vscode_dialog_scan.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if data and len(data) > 0:
            dialogs = data[0].get('dialogs_found', [])
            
            print(f"\nFound {len(dialogs)} dialog elements")
            print("\nRoo Code Dialog Content:")
            print("-" * 60)
            
            # Look for the main task
            for dialog in dialogs:
                texts = dialog.get('texts', [])
                for text in texts:
                    if 'Task:' in text and '请对mathematical-ai-bootstrapping' in text:
                        print("\n[TASK CONTENT]")
                        print(text)
                        print("\n[PARSED TASK]")
                        # Parse the task
                        task_text = text.split('Task:')[1].strip()
                        task_text = task_text.replace('\\u8bf7', '请')
                        task_text = task_text.replace('\\u5bf9', '对')
                        task_text = task_text.replace('\\u4ed3', '仓')
                        task_text = task_text.replace('\\u5e93', '库')
                        task_text = task_text.replace('\\u8fdb', '进')
                        task_text = task_text.replace('\\u884c', '行')
                        task_text = task_text.replace('\\u5168', '全')
                        task_text = task_text.replace('\\u9762', '面')
                        task_text = task_text.replace('\\u67b6', '架')
                        task_text = task_text.replace('\\u6784', '构')
                        task_text = task_text.replace('\\u5206', '分')
                        task_text = task_text.replace('\\u6790', '析')
                        task_text = task_text.replace('\\uff0c', '，')
                        task_text = task_text.replace('\\u91cd', '重')
                        task_text = task_text.replace('\\u70b9', '点')
                        task_text = task_text.replace('\\u5173', '关')
                        task_text = task_text.replace('\\u6ce8', '注')
                        task_text = task_text.replace('\\u7cfb', '系')
                        task_text = task_text.replace('\\u5217', '列')
                        task_text = task_text.replace('\\u7ec4', '组')
                        task_text = task_text.replace('\\u4ef6', '件')
                        task_text = task_text.replace('\\u3002', '。')
                        task_text = task_text.replace('\\u5e94', '应')
                        task_text = task_text.replace('\\u5305', '包')
                        task_text = task_text.replace('\\u62ec', '括')
                        task_text = task_text.replace('\\uff1a', '：')
                        task_text = task_text.replace('\\u7edf', '统')
                        task_text = task_text.replace('\\u603b', '总')
                        task_text = task_text.replace('\\u4f53', '体')
                        task_text = task_text.replace('\\u4ea4', '交')
                        task_text = task_text.replace('\\u4e92', '互')
                        task_text = task_text.replace('\\u6570', '数')
                        task_text = task_text.replace('\\u636e', '据')
                        task_text = task_text.replace('\\u6d41', '流')
                        task_text = task_text.replace('\\u6280', '技')
                        task_text = task_text.replace('\\u672f', '术')
                        task_text = task_text.replace('\\u6808', '栈')
                        task_text = task_text.replace('\\u8bc4', '评')
                        task_text = task_text.replace('\\u4f30', '估')
                        task_text = task_text.replace('\\u6a21', '模')
                        task_text = task_text.replace('\\u5757', '块')
                        task_text = task_text.replace('\\u804c', '职')
                        task_text = task_text.replace('\\u8d23', '责')
                        task_text = task_text.replace('\\u5212', '划')
                        task_text = task_text.replace('\\u6269', '扩')
                        task_text = task_text.replace('\\u5c55', '展')
                        task_text = task_text.replace('\\u6027', '性')
                        task_text = task_text.replace('\\u5b8c', '完')
                        task_text = task_text.replace('\\u6210', '成')
                        task_text = task_text.replace('\\u540e', '后')
                        task_text = task_text.replace('\\u4f7f', '使')
                        task_text = task_text.replace('\\u7528', '用')
                        task_text = task_text.replace('\\u5de5', '工')
                        task_text = task_text.replace('\\u5177', '具')
                        task_text = task_text.replace('\\u63d0', '提')
                        task_text = task_text.replace('\\u4ea4', '交')
                        task_text = task_text.replace('\\u4e00', '一')
                        task_text = task_text.replace('\\u4efd', '份')
                        task_text = task_text.replace('\\u6574', '整')
                        task_text = task_text.replace('\\u7684', '的')
                        task_text = task_text.replace('\\u62a5', '报')
                        task_text = task_text.replace('\\u544a', '告')
                        task_text = task_text.replace('\\u8be5', '该')
                        task_text = task_text.replace('\\u5c06', '将')
                        task_text = task_text.replace('\\u7531', '由')
                        task_text = task_text.replace('\\u8463', '董')
                        task_text = task_text.replace('\\u79d8', '秘')
                        task_text = task_text.replace('\\u5f0f', '式')
                        task_text = task_text.replace('\\u5411', '向')
                        task_text = task_text.replace('\\u6237', '户')
                        task_text = task_text.replace('\\u6c47', '汇')
                        task_text = task_text.replace('\\u786e', '确')
                        task_text = task_text.replace('\\u4fdd', '保')
                        task_text = task_text.replace('\\u4e14', '且')
                        task_text = task_text.replace('\\u53ea', '只')
                        task_text = task_text.replace('\\u5c42', '层')
                        
                        print(task_text)
                        break
            
            # Also look for conversation content
            print("\n\nOther Dialog Elements:")
            print("-" * 60)
            for dialog in dialogs[:10]:  # First 10 elements
                if dialog.get('texts'):
                    for text in dialog['texts']:
                        if len(text) > 20 and not text.startswith('\\ue'):
                            print(f"\n[{dialog['type']}] {text[:100]}...")
                            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_roo_code_content()