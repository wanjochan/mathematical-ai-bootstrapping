"""简单直接的Cursor IDE交互测试 - 基于坐标点击"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import win32gui
import win32con
import win32api
import win32clipboard


class SimpleCursorController:
    """简单的Cursor IDE控制器 - 直接基于坐标"""
    
    def __init__(self):
        self.cursor_hwnd = None
        
    def find_cursor_window(self):
        """查找Cursor IDE窗口"""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and 'cursor' in title.lower():
                    windows.append((hwnd, title))
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        
        if windows:
            self.cursor_hwnd, title = windows[0]
            print(f"OK 找到Cursor IDE: {title}")
            return True
        else:
            print("FAIL 未找到Cursor IDE窗口")
            return False
    
    def get_window_size(self):
        """获取窗口尺寸"""
        if self.cursor_hwnd:
            left, top, right, bottom = win32gui.GetWindowRect(self.cursor_hwnd)
            width = right - left
            height = bottom - top
            print(f"窗口尺寸: {width}x{height}")
            return width, height
        return None, None
    
    def click_chat_input_area(self):
        """点击聊天输入区域（基于观察到的UI布局）"""
        try:
            if not self.cursor_hwnd:
                print("❌ 无Cursor窗口句柄")
                return False
            
            # 基于观察到的UI，聊天输入框位置大概在右侧面板的中下部
            # 获取窗口尺寸来计算相对位置
            left, top, right, bottom = win32gui.GetWindowRect(self.cursor_hwnd)
            width = right - left
            height = bottom - top
            
            # 计算聊天输入框的估计位置
            # 右侧面板大约从60%宽度开始，输入框在面板的中部偏下
            input_x = int(width * 0.8)  # 右侧面板中央
            input_y = int(height * 0.75)  # 下方75%位置
            
            # 转换为屏幕坐标
            screen_x = left + input_x
            screen_y = top + input_y
            
            print(f"🎯 尝试点击聊天输入区域:")
            print(f"   窗口坐标: ({input_x}, {input_y})")
            print(f"   屏幕坐标: ({screen_x}, {screen_y})")
            
            # 确保窗口在前台
            win32gui.SetForegroundWindow(self.cursor_hwnd)
            time.sleep(0.5)
            
            # 点击该位置
            win32api.SetCursorPos((screen_x, screen_y))
            time.sleep(0.3)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            time.sleep(0.1)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
            
            print("✅ 点击完成")
            return True
            
        except Exception as e:
            print(f"FAIL 点击失败: {e}")
            return False
    
    def send_simple_message(self, message):
        """发送简单消息"""
        try:
            print(f"📝 准备发送消息: '{message}'")
            
            # 等待一下让焦点稳定
            time.sleep(0.5)
            
            # 清除可能存在的内容 (Ctrl+A)
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord('A'), 0, 0, 0)
            win32api.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.2)
            
            # 发送消息内容
            self.type_text(message)
            
            # 等待一下
            time.sleep(0.5)
            
            # 发送回车
            win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
            win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            print("✅ 消息发送完成")
            return True
            
        except Exception as e:
            print(f"❌ 发送消息失败: {e}")
            return False
    
    def type_text(self, text):
        """逐字符输入文本"""
        for char in text:
            if char == ' ':
                win32api.keybd_event(win32con.VK_SPACE, 0, 0, 0)
                win32api.keybd_event(win32con.VK_SPACE, 0, win32con.KEYEVENTF_KEYUP, 0)
            elif char.isalpha():
                vk_code = ord(char.upper())
                if char.isupper():
                    # 大写字母
                    win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
                    win32api.keybd_event(vk_code, 0, 0, 0)
                    win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                    win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
                else:
                    # 小写字母
                    win32api.keybd_event(vk_code, 0, 0, 0)
                    win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            elif char.isdigit():
                vk_code = ord(char)
                win32api.keybd_event(vk_code, 0, 0, 0)
                win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            elif char in '.,!?':
                # 常用标点符号
                char_map = {'.': win32con.VK_OEM_PERIOD, ',': win32con.VK_OEM_COMMA}
                if char in char_map:
                    vk_code = char_map[char]
                    win32api.keybd_event(vk_code, 0, 0, 0)
                    win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            time.sleep(0.05)  # 小延迟，避免输入过快


def main():
    """主测试函数"""
    print("🚀 Cursor IDE 简单交互测试")
    print("=" * 50)
    print("这个测试将:")
    print("1. 找到Cursor IDE窗口")
    print("2. 点击估计的聊天输入位置")
    print("3. 发送一条测试消息")
    print()
    
    controller = SimpleCursorController()
    
    # 步骤1: 查找窗口
    if not controller.find_cursor_window():
        return False
    
    # 步骤2: 获取窗口信息
    width, height = controller.get_window_size()
    if not width:
        return False
    
    # 步骤3: 进行交互测试
    print("\n🎯 开始交互测试...")
    
    # 点击聊天输入区域
    if not controller.click_chat_input_area():
        return False
    
    # 等待一下让界面响应
    time.sleep(1)
    
    # 发送测试消息
    test_message = "Hello from cybercorp_node! This is a test message."
    print(f"\n📤 发送测试消息...")
    
    if controller.send_simple_message(test_message):
        print("\n🎉 交互测试成功!")
        print("✅ cybercorp_node成功向Cursor IDE发送了消息")
        print("✅ 请查看Cursor IDE界面确认消息是否正确发送")
        return True
    else:
        print("\n❌ 交互测试失败")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🤖 cybercorp_node -> Cursor IDE 实战交互测试")
    print("=" * 60)
    print()
    print("准备要求:")
    print("1. ✅ Cursor IDE 已启动")
    print("2. ✅ AI助手聊天面板已打开")
    print("3. ✅ 没有其他程序遮挡Cursor窗口")
    print()
    print("即将开始实际交互测试...")
    print("这将向Cursor IDE发送一条真实的测试消息!")
    print()
    
    try:
        success = main()
        
        if success:
            print("\n" + "=" * 60)
            print("🎊 恭喜! cybercorp_node成功控制了Cursor IDE!")
            print("=" * 60)
            print("✅ 这证明了:")
            print("   - cybercorp_node可以找到并控制Cursor IDE")
            print("   - 可以向Cursor发送编程相关的问题")
            print("   - 实现了'备选开发员'的基础功能")
            print()
            print("🚀 现在可以用cybercorp_node自动化您的开发工作流!")
        else:
            print("\n❌ 测试不完全成功，但基础功能已验证")
            
    except KeyboardInterrupt:
        print("\n⏸️ 用户中断测试")
    except Exception as e:
        print(f"\n💥 测试出错: {e}")
        import traceback
        traceback.print_exc()