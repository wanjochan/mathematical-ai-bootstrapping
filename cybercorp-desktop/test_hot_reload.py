#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热重载API测试脚本
演示如何通过API触发组件重载
"""

import requests
import json
import time
import os
from logger import app_logger


class HotReloadTester:
    def __init__(self, api_url="http://localhost:8888"):
        self.api_url = api_url
        
    def test_api_connection(self):
        """测试API连接"""
        try:
            response = requests.get(f"{self.api_url}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ API连接成功!")
                print(f"   状态: {data['status']}")
                print(f"   注册组件: {data['components']}")
                print(f"   文件监控: {data['watching']}")
                return True
            else:
                print(f"❌ API连接失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ API连接失败: {str(e)}")
            return False
    
    def reload_component(self, component_name="all"):
        """重载指定组件"""
        try:
            payload = {"component": component_name}
            response = requests.post(f"{self.api_url}/reload", 
                                   json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    if component_name == 'all':
                        print(f"✅ 批量重载成功! 重载了 {data.get('reloaded', 0)} 个组件")
                    else:
                        print(f"✅ 组件 '{component_name}' 重载成功!")
                    return True
                else:
                    print(f"❌ 重载失败: {data}")
                    return False
            else:
                print(f"❌ 重载请求失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 重载请求异常: {str(e)}")
            return False
    
    def demo_file_modification(self):
        """演示文件修改触发重载"""
        print("\n🔥 演示文件修改触发自动重载:")
        
        # 备份原文件
        ui_file = "ui_components.py"
        backup_file = "ui_components.py.backup"
        
        if not os.path.exists(ui_file):
            print(f"❌ 找不到文件: {ui_file}")
            return
        
        try:
            # 创建备份
            with open(ui_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            print(f"📁 已创建备份文件: {backup_file}")
            
            # 修改文件 - 在工具栏标题后面加上时间戳
            timestamp = int(time.time())
            modified_content = original_content.replace(
                '🛠️ 桌面窗口管理器',
                f'🛠️ 桌面窗口管理器 [更新: {timestamp}]'
            )
            
            print("✏️ 正在修改文件...")
            with open(ui_file, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            print("💾 文件已保存，等待自动重载...")
            time.sleep(2)  # 等待文件监控触发重载
            
            # 恢复原文件
            print("🔄 恢复原文件...")
            with open(ui_file, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # 删除备份
            os.remove(backup_file)
            print("✅ 演示完成，文件已恢复")
            
        except Exception as e:
            print(f"❌ 演示过程出错: {str(e)}")
            # 尝试恢复文件
            try:
                if os.path.exists(backup_file):
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        backup_content = f.read()
                    with open(ui_file, 'w', encoding='utf-8') as f:
                        f.write(backup_content)
                    os.remove(backup_file)
                    print("🔄 已从备份恢复文件")
            except:
                pass
    
    def interactive_test(self):
        """交互式测试"""
        print("\n🎮 交互式热重载测试")
        print("=" * 50)
        
        while True:
            print("\n选择操作:")
            print("1. 测试API连接")
            print("2. 重载所有组件")
            print("3. 重载工具栏")
            print("4. 重载窗口列表面板")
            print("5. 重载分析面板")
            print("6. 演示文件修改触发重载")
            print("0. 退出")
            
            choice = input("\n请输入选择 (0-6): ").strip()
            
            if choice == "0":
                print("👋 退出测试")
                break
            elif choice == "1":
                self.test_api_connection()
            elif choice == "2":
                self.reload_component("all")
            elif choice == "3":
                self.reload_component("toolbar")
            elif choice == "4":
                self.reload_component("window_list_panel")
            elif choice == "5":
                self.reload_component("analysis_panel")
            elif choice == "6":
                self.demo_file_modification()
            else:
                print("❌ 无效选择，请重试")
            
            input("\n按回车继续...")


def main():
    print("🔥 热重载API测试工具")
    print("=" * 50)
    
    tester = HotReloadTester()
    
    # 首先测试连接
    if not tester.test_api_connection():
        print("\n❌ 无法连接到API服务器")
        print("请确保热重载版本的程序正在运行:")
        print("   python main_hot_reload.py")
        return
    
    # 进入交互模式
    tester.interactive_test()


if __name__ == "__main__":
    main() 