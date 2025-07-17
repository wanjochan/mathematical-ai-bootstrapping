"""
Computer-Use API测试文件
测试基础Computer-Use操作接口的各项功能
"""

import time
import json
import requests
import subprocess
from typing import Dict, Any

# 测试配置
BASE_URL = "http://localhost:8000/api/v1/computer-use"

class ComputerUseAPITester:
    """Computer-Use API测试类"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_health_check(self):
        """测试健康检查"""
        print("=== 测试Computer-Use健康检查 ===")
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            data = response.json()
            
            print(f"✅ 健康检查通过")
            print(f"状态: {data['status']}")
            print(f"组件: {data['component']}")
            print(f"版本: {data['version']}")
            print(f"功能: {', '.join(data['features'])}")
            
            system_info = data['system_info']
            print(f"屏幕大小: {system_info['screen_size']}")
            print(f"鼠标位置: {system_info['mouse_position']}")
            return True
            
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            return False
    
    def test_system_info(self):
        """测试系统信息"""
        print("\n=== 测试系统信息 ===")
        try:
            response = self.session.get(f"{self.base_url}/info")
            response.raise_for_status()
            data = response.json()
            
            print(f"✅ 系统信息获取成功")
            print(f"屏幕大小: {data['screen_size']}")
            print(f"当前活动窗口: {data['active_window']}")
            print(f"鼠标位置: {data['mouse_position']}")
            print(f"安全模式: {data['fail_safe_enabled']}")
            return True
            
        except Exception as e:
            print(f"❌ 系统信息测试失败: {e}")
            return False
    
    def test_screenshot(self):
        """测试截图功能"""
        print("\n=== 测试截图功能 ===")
        try:
            # 全屏截图
            response = self.session.post(f"{self.base_url}/screenshot")
            response.raise_for_status()
            data = response.json()
            
            print(f"✅ 全屏截图成功")
            print(f"截图大小: {data['data']['size']}")
            print(f"截图数据长度: {len(data['data']['screenshot_base64'])} 字符")
            
            # 区域截图测试
            response = self.session.post(
                f"{self.base_url}/screenshot?x=100&y=100&width=300&height=200"
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"✅ 区域截图成功")
            print(f"区域: {data['data']['region']}")
            print(f"截图大小: {data['data']['size']}")
            return True
            
        except Exception as e:
            print(f"❌ 截图测试失败: {e}")
            return False
    
    def test_mouse_operations(self):
        """测试鼠标操作"""
        print("\n=== 测试鼠标操作 ===")
        try:
            # 点击操作（选择一个安全的位置）
            click_data = {
                "action": "click",
                "x": 500,
                "y": 500,
                "button": "left",
                "clicks": 1
            }
            
            response = self.session.post(f"{self.base_url}/click", json=click_data)
            response.raise_for_status()
            data = response.json()
            
            print(f"✅ 点击操作成功")
            print(f"点击位置: {data['data']['position']}")
            print(f"按钮: {data['data']['button']}")
            
            # 滚轮操作
            scroll_data = {
                "x": 500,
                "y": 500,
                "direction": "up",
                "clicks": 3
            }
            
            response = self.session.post(f"{self.base_url}/scroll", json=scroll_data)
            response.raise_for_status()
            data = response.json()
            
            print(f"✅ 滚轮操作成功")
            print(f"滚轮位置: {data['data']['position']}")
            print(f"方向: {data['data']['direction']}")
            return True
            
        except Exception as e:
            print(f"❌ 鼠标操作测试失败: {e}")
            return False
    
    def test_keyboard_operations(self):
        """测试键盘操作"""
        print("\n=== 测试键盘操作 ===")
        try:
            # 先启动记事本
            print("启动记事本进行键盘测试...")
            notepad = subprocess.Popen(['notepad.exe'])
            time.sleep(2)  # 等待记事本启动
            
            try:
                # 文本输入
                type_data = {
                    "action": "type",
                    "text": "Hello Computer-Use API!",
                    "interval": 0.05
                }
                
                response = self.session.post(f"{self.base_url}/type", json=type_data)
                response.raise_for_status()
                data = response.json()
                
                print(f"✅ 文本输入成功")
                print(f"输入文本: {data['data']['text']}")
                print(f"文本长度: {data['data']['length']}")
                
                # 按键操作
                key_data = {
                    "action": "key",
                    "key": "enter"
                }
                
                response = self.session.post(f"{self.base_url}/key", json=key_data)
                response.raise_for_status()
                data = response.json()
                
                print(f"✅ 按键操作成功")
                print(f"按键: {data['data']['key']}")
                
                # 组合键操作
                hotkey_data = {
                    "action": "hotkey",
                    "keys": ["ctrl", "a"]
                }
                
                response = self.session.post(f"{self.base_url}/key", json=hotkey_data)
                response.raise_for_status()
                data = response.json()
                
                print(f"✅ 组合键操作成功")
                print(f"组合键: {data['data']['keys']}")
                
                return True
                
            finally:
                # 关闭记事本
                notepad.terminate()
                
        except Exception as e:
            print(f"❌ 键盘操作测试失败: {e}")
            return False
    
    def test_context_management(self):
        """测试上下文管理"""
        print("\n=== 测试上下文管理 ===")
        try:
            response = self.session.get(f"{self.base_url}/context")
            response.raise_for_status()
            data = response.json()
            
            print(f"✅ 上下文获取成功")
            print(f"最后操作: {data.get('last_action', '无')}")
            print(f"活动窗口: {data.get('active_window', '无')}")
            print(f"屏幕大小: {data.get('screen_size', '无')}")
            print(f"有截图: {data.get('has_screenshot', False)}")
            return True
            
        except Exception as e:
            print(f"❌ 上下文管理测试失败: {e}")
            return False
    
    def test_operation_sequence(self):
        """测试操作序列"""
        print("\n=== 测试操作序列 ===")
        try:
            # 定义一个简单的操作序列
            sequence = [
                {
                    "type": "click",
                    "action": "click",
                    "x": 400,
                    "y": 400,
                    "critical": False
                },
                {
                    "type": "wait",
                    "duration": 0.5
                },
                {
                    "type": "key",
                    "action": "key", 
                    "key": "escape",
                    "critical": False
                }
            ]
            
            response = self.session.post(f"{self.base_url}/sequence", json=sequence)
            response.raise_for_status()
            data = response.json()
            
            print(f"✅ 操作序列执行成功")
            print(f"总步骤: {data['total_steps']}")
            print(f"完成步骤: {data['completed_steps']}")
            print(f"整体成功: {data['success']}")
            
            # 显示每个步骤的结果
            for result in data['results']:
                step_success = "✅" if result['result']['success'] else "❌"
                print(f"  步骤 {result['step']}: {step_success} {result['action']['type']}")
            
            return True
            
        except Exception as e:
            print(f"❌ 操作序列测试失败: {e}")
            return False

def run_computer_use_tests():
    """运行所有Computer-Use测试"""
    print("🚀 开始Computer-Use API测试")
    print("=" * 50)
    
    tester = ComputerUseAPITester()
    results = []
    
    # 测试列表
    test_functions = [
        ("健康检查", tester.test_health_check),
        ("系统信息", tester.test_system_info),
        ("截图功能", tester.test_screenshot),
        ("鼠标操作", tester.test_mouse_operations),
        ("键盘操作", tester.test_keyboard_operations),
        ("上下文管理", tester.test_context_management),
        ("操作序列", tester.test_operation_sequence),
    ]
    
    for test_name, test_func in test_functions:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试出现异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果摘要
    print("\n" + "=" * 50)
    print("📊 Computer-Use测试结果摘要:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过! Computer-Use组件工作正常")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关功能")
        return False

if __name__ == "__main__":
    # 运行测试
    success = run_computer_use_tests()
    
    if success:
        print("\n✅ Computer-Use API测试完成 - 所有功能正常")
    else:
        print("\n❌ Computer-Use API测试完成 - 发现问题") 