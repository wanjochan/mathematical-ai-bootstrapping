"""实际向Cursor IDE发送清理backup/目录的指令"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import win32gui
import win32con
import win32api
import win32clipboard
import pyautogui
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 禁用pyautogui的安全检查
pyautogui.FAILSAFE = False


def find_cursor_window():
    """查找并激活Cursor IDE窗口"""
    print("🔍 查找Cursor IDE窗口...")
    
    def enum_windows_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and 'cursor' in title.lower():
                windows.append((hwnd, title))
        return True
    
    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)
    
    if not windows:
        print("❌ 未找到Cursor IDE窗口，请确保Cursor IDE已启动")
        return None
    
    hwnd, title = windows[0]
    print(f"✅ 找到Cursor窗口: {title}")
    
    # 激活窗口
    try:
        win32gui.SetForegroundWindow(hwnd)
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(1)
        print("✅ 窗口已激活")
        return hwnd
    except Exception as e:
        print(f"❌ 激活窗口失败: {e}")
        return None


def set_clipboard(text):
    """设置剪贴板内容"""
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
        return True
    except Exception as e:
        print(f"❌ 设置剪贴板失败: {e}")
        return False


def send_message_to_cursor(message):
    """向Cursor IDE发送消息"""
    print(f"📝 准备发送消息: {message}")
    
    # 方法1: 尝试使用Ctrl+L快捷键打开AI助手
    print("🎯 尝试打开AI助手面板 (Ctrl+L)...")
    pyautogui.hotkey('ctrl', 'l')
    time.sleep(2)
    
    # 方法2: 设置剪贴板并粘贴
    print("📋 使用剪贴板方式输入...")
    if set_clipboard(message):
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1)
        
        # 发送消息
        print("🚀 发送消息 (Enter)...")
        pyautogui.press('enter')
        time.sleep(0.5)
        
        print("✅ 消息已发送!")
        return True
    
    return False


def interactive_cursor_test():
    """交互式Cursor测试"""
    print("🎯 Cursor IDE 交互测试")
    print("=" * 50)
    
    # 查找并激活Cursor窗口
    hwnd = find_cursor_window()
    if not hwnd:
        return False
    
    print("\n📋 准备发送的消息:")
    cleanup_message = """请帮我清理一下backup/目录，具体要求：

1. 删除超过7天的备份文件
2. 保留最新的3个备份
3. 清理临时文件和日志文件
4. 显示清理前后的目录大小对比

请生成相应的脚本来完成这个任务。"""
    
    print(f"内容: {cleanup_message}")
    
    # 给用户时间切换到Cursor窗口
    print(f"\n⏰ 请确保:")
    print(f"  1. Cursor IDE窗口可见")
    print(f"  2. AI助手面板已打开")
    print(f"  3. 输入框处于焦点状态")
    
    input(f"\n按Enter键继续发送消息...")
    
    # 发送消息
    success = send_message_to_cursor(cleanup_message)
    
    if success:
        print(f"\n🎉 消息发送成功!")
        print(f"现在Cursor应该开始处理backup/目录清理任务。")
        print(f"请查看Cursor的响应...")
    else:
        print(f"\n❌ 消息发送失败")
    
    return success


def automated_cursor_test():
    """自动化Cursor测试（实验性）"""
    print("🤖 自动化Cursor IDE交互")
    print("=" * 50)
    
    hwnd = find_cursor_window()
    if not hwnd:
        return False
    
    cleanup_message = "请帮我清理backup/目录，删除7天前的备份，保留最新3个文件"
    
    print("🎯 尝试自动化交互序列...")
    
    # 序列1: 尝试常见的AI助手快捷键
    shortcuts_to_try = [
        ('ctrl', 'shift', 'p'),  # 命令面板
        ('ctrl', 'l'),           # AI助手（常见）
        ('ctrl', 'j'),           # 面板切换
        ('ctrl', '`'),           # 终端切换
    ]
    
    for keys in shortcuts_to_try:
        print(f"尝试快捷键: {' + '.join(keys)}")
        pyautogui.hotkey(*keys)
        time.sleep(1.5)
        
        # 尝试输入消息
        if set_clipboard(cleanup_message):
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(1)
            print(f"✅ 快捷键 {' + '.join(keys)} 尝试完成")
            break
    
    print("🔍 自动化序列完成，请检查Cursor IDE的响应")
    return True


def main():
    """主函数"""
    print("🚀 Cursor IDE 实战测试 - 清理backup/目录")
    print("=" * 60)
    
    print("选择测试模式:")
    print("1. 交互式测试 (推荐)")
    print("2. 自动化测试 (实验性)")
    
    choice = input("请选择 (1 或 2): ").strip()
    
    if choice == "1":
        success = interactive_cursor_test()
    elif choice == "2":
        success = automated_cursor_test()
    else:
        print("❌ 无效选择")
        return
    
    if success:
        print("\n" + "=" * 60)
        print("🎯 测试完成! 期望结果:")
        print("  • Cursor收到清理backup/目录的请求")
        print("  • Cursor生成相应的清理脚本")
        print("  • 可以执行脚本来清理目录")
        print("\n这展示了改进后的UI检测和交互能力!")
    else:
        print("\n❌ 测试未成功，请手动在Cursor中输入清理指令")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏸️ 测试中断")
    except Exception as e:
        print(f"\n💥 测试出错: {e}")
        import traceback
        traceback.print_exc()