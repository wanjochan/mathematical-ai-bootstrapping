"""
UI-TARS API测试文件
测试UI-TARS窗口信息流组件的各项功能
"""

import asyncio
import json
import time
import threading
from typing import Dict, Any
import requests
import websockets
import subprocess

# 测试配置
BASE_URL = "http://localhost:8000/api/v1/ui-tars"
WS_URL = "ws://localhost:8000/api/v1/ui-tars"

class UITarsAPITester:
    """UI-TARS API测试类"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_health_check(self):
        """测试健康检查"""
        print("=== 测试健康检查 ===")
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            data = response.json()
            
            print(f"✅ 健康检查通过")
            print(f"状态: {data['status']}")
            print(f"组件: {data['component']}")
            print(f"版本: {data['version']}")
            print(f"功能: {', '.join(data['features'])}")
            return True
            
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            return False
    
    def test_config_management(self):
        """测试配置管理"""
        print("\n=== 测试配置管理 ===")
        try:
            # 获取默认配置
            response = self.session.get(f"{self.base_url}/config")
            response.raise_for_status()
            default_config = response.json()
            print(f"✅ 获取默认配置成功: FPS={default_config['fps']}")
            
            # 更新配置
            new_config = {
                "fps": 2.0,
                "max_width": 1280,
                "max_height": 720,
                "compression_quality": 90,
                "enable_smart_resize": True,
                "target_window": "记事本"
            }
            
            response = self.session.post(f"{self.base_url}/config", json=new_config)
            response.raise_for_status()
            update_result = response.json()
            print(f"✅ 配置更新成功: {update_result['message']}")
            
            # 验证配置更新
            response = self.session.get(f"{self.base_url}/config")
            updated_config = response.json()
            
            if updated_config['fps'] == 2.0:
                print("✅ 配置验证成功")
                return True
            else:
                print("❌ 配置验证失败")
                return False
                
        except Exception as e:
            print(f"❌ 配置管理测试失败: {e}")
            return False
    
    def test_window_listing(self):
        """测试窗口列表"""
        print("\n=== 测试窗口列表 ===")
        try:
            response = self.session.get(f"{self.base_url}/windows")
            response.raise_for_status()
            data = response.json()
            
            windows = data['windows']
            print(f"✅ 获取到 {len(windows)} 个窗口:")
            
            for i, window in enumerate(windows[:5]):  # 只显示前5个
                print(f"  {i+1}. {window['title'][:50]}... (HWND: {window['hwnd']})")
                
            return len(windows) > 0
            
        except Exception as e:
            print(f"❌ 窗口列表测试失败: {e}")
            return False
    
    def test_snapshot_capture(self):
        """测试快照捕获"""
        print("\n=== 测试快照捕获 ===")
        try:
            # 启动记事本进行测试
            print("启动记事本用于测试...")
            notepad_process = subprocess.Popen(['notepad.exe'])
            time.sleep(2)  # 等待记事本启动
            
            try:
                # 捕获当前前台窗口快照
                response = self.session.get(f"{self.base_url}/snapshot")
                response.raise_for_status()
                snapshot = response.json()
                
                print("✅ 快照捕获成功")
                print(f"时间戳: {snapshot['timestamp']}")
                print(f"窗口标题: {snapshot['window_info']['title']}")
                print(f"窗口大小: {snapshot['frame_size']}")
                print(f"UI元素数量: {len(snapshot['ui_elements'])}")
                
                # 检查是否有截图数据
                has_screenshot = snapshot['screenshot_base64'] is not None
                print(f"截图数据: {'✅ 存在' if has_screenshot else '❌ 缺失'}")
                
                return True
                
            finally:
                # 关闭记事本
                notepad_process.terminate()
                
        except Exception as e:
            print(f"❌ 快照捕获测试失败: {e}")
            return False
    
    def test_stream_control(self):
        """测试数据流控制"""
        print("\n=== 测试数据流控制 ===")
        try:
            # 检查初始状态
            response = self.session.get(f"{self.base_url}/stream/status")
            initial_status = response.json()
            print(f"初始流状态: {initial_status['is_streaming']}")
            
            # 启动数据流
            response = self.session.post(f"{self.base_url}/stream/start")
            response.raise_for_status()
            start_result = response.json()
            print(f"✅ 数据流启动: {start_result['message']}")
            
            # 等待一段时间让流处理一些帧
            time.sleep(3)
            
            # 检查流状态
            response = self.session.get(f"{self.base_url}/stream/status")
            stream_status = response.json()
            print(f"流状态: 运行中={stream_status['is_streaming']}, 帧数={stream_status['frame_count']}")
            
            # 停止数据流
            response = self.session.post(f"{self.base_url}/stream/stop")
            response.raise_for_status()
            stop_result = response.json()
            print(f"✅ 数据流停止: {stop_result['message']}")
            
            # 验证停止状态
            response = self.session.get(f"{self.base_url}/stream/status")
            final_status = response.json()
            
            if final_status['is_streaming'] == False:
                print("✅ 数据流控制测试成功")
                return True
            else:
                print("❌ 数据流停止失败")
                return False
                
        except Exception as e:
            print(f"❌ 数据流控制测试失败: {e}")
            return False

async def test_websocket_stream():
    """测试WebSocket数据流"""
    print("\n=== 测试WebSocket数据流 ===")
    try:
        # 首先启动数据流
        requests.post(f"{BASE_URL}/stream/start")
        
        ws_uri = f"{WS_URL}/stream/ws"
        
        async with websockets.connect(ws_uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 接收几个数据帧
            frame_count = 0
            start_time = time.time()
            
            while frame_count < 3 and (time.time() - start_time) < 10:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data.get('type') == 'heartbeat':
                        print("💓 收到心跳")
                        continue
                    
                    frame_count += 1
                    print(f"📡 收到第 {frame_count} 帧数据")
                    
                    if 'window_info' in data:
                        print(f"   窗口: {data['window_info']['title'][:30]}...")
                        
                except asyncio.TimeoutError:
                    print("⏰ WebSocket接收超时")
                    break
            
            print(f"✅ WebSocket测试完成，收到 {frame_count} 帧数据")
            
        # 停止数据流
        requests.post(f"{BASE_URL}/stream/stop")
        return frame_count > 0
        
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始UI-TARS API测试")
    print("=" * 50)
    
    tester = UITarsAPITester()
    results = []
    
    # HTTP API测试
    test_functions = [
        ("健康检查", tester.test_health_check),
        ("配置管理", tester.test_config_management),
        ("窗口列表", tester.test_window_listing),
        ("快照捕获", tester.test_snapshot_capture),
        ("数据流控制", tester.test_stream_control),
    ]
    
    for test_name, test_func in test_functions:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试出现异常: {e}")
            results.append((test_name, False))
    
    # WebSocket测试
    try:
        ws_result = asyncio.run(test_websocket_stream())
        results.append(("WebSocket数据流", ws_result))
    except Exception as e:
        print(f"❌ WebSocket测试出现异常: {e}")
        results.append(("WebSocket数据流", False))
    
    # 输出测试结果摘要
    print("\n" + "=" * 50)
    print("📊 测试结果摘要:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过! UI-TARS组件工作正常")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关功能")
        return False

if __name__ == "__main__":
    # 运行测试
    success = run_all_tests()
    
    if success:
        print("\n✅ UI-TARS API测试完成 - 所有功能正常")
    else:
        print("\n❌ UI-TARS API测试完成 - 发现问题") 