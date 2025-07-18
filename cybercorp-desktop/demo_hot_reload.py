#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热重载功能演示脚本
展示如何修改UI组件并实时看到效果
"""

import time
import requests
import os


def demo_hot_reload():
    """演示热重载功能"""
    print("🔥 热重载功能演示")
    print("=" * 50)
    
    # 检查API是否可用
    try:
        response = requests.get("http://localhost:8888/status", timeout=5)
        if response.status_code != 200:
            print("❌ 热重载API服务器未运行")
            print("请先启动: python main_hot_reload.py")
            return
    except:
        print("❌ 无法连接到热重载API服务器")
        print("请先启动: python main_hot_reload.py")
        return
    
    print("✅ 热重载API服务器已连接")
    print("\n现在我将演示如何修改UI组件并实时看到效果:")
    
    # 读取原始文件
    ui_file = "ui_components.py"
    with open(ui_file, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # 演示步骤
    modifications = [
        {
            'desc': '1. 修改工具栏标题颜色',
            'old': '🛠️ 桌面窗口管理器',
            'new': '🔥 热重载演示 - 实时更新中！'
        },
        {
            'desc': '2. 修改按钮样式',
            'old': '"🔄 刷新窗口"',
            'new': '"🚀 快速刷新"'
        },
        {
            'desc': '3. 添加动态状态',
            'old': '"准备就绪"',
            'new': f'"热重载演示 - {int(time.time())}"'
        }
    ]
    
    try:
        for i, mod in enumerate(modifications, 1):
            print(f"\n📝 {mod['desc']}")
            
            # 修改文件
            modified_content = original_content.replace(mod['old'], mod['new'])
            with open(ui_file, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            print("   文件已修改，等待自动重载...")
            time.sleep(2)
            
            # 也可以手动触发API重载
            try:
                response = requests.post("http://localhost:8888/reload", 
                                       json={"component": "all"}, timeout=5)
                if response.status_code == 200:
                    print("   ✅ API重载成功")
                else:
                    print("   ⚠️ API重载失败，但文件监控应该会自动触发")
            except:
                print("   ⚠️ API重载请求失败，但文件监控应该会自动触发")
            
            # 为下次修改准备
            original_content = modified_content
            
            input("   按回车继续下一步演示...")
        
        print("\n🎉 演示完成！")
        print("你应该在界面上看到了实时的变化。")
        print("\n现在恢复原始状态...")
        
        # 恢复原始文件
        with open(ui_file, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        # 恢复原始内容
        restored_content = current_content
        for mod in reversed(modifications):
            restored_content = restored_content.replace(mod['new'], mod['old'])
        
        with open(ui_file, 'w', encoding='utf-8') as f:
            f.write(restored_content)
        
        # 触发最后一次重载
        try:
            requests.post("http://localhost:8888/reload", json={"component": "all"}, timeout=5)
            print("✅ 界面已恢复原始状态")
        except:
            print("⚠️ 请手动点击热重载按钮恢复界面")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {str(e)}")
        # 尝试恢复原始文件
        try:
            with open(ui_file, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            # 如果有备份，恢复备份
            if os.path.exists(ui_file + '.original'):
                with open(ui_file + '.original', 'r', encoding='utf-8') as f:
                    original_content = f.read()
                with open(ui_file, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                print("🔄 已恢复原始文件")
        except:
            print("⚠️ 无法自动恢复，请手动检查文件")


def show_help():
    """显示帮助信息"""
    help_text = """
🔥 Python tkinter 热重载功能说明

这个实现通过以下技术实现热重载：

1. **文件监控** (watchdog库)
   - 监控 ui_components.py 文件变化
   - 检测文件保存时自动触发重载

2. **模块重载** (importlib.reload)
   - 动态重新导入修改后的模块
   - 获取更新后的类定义

3. **组件替换**
   - 销毁旧的UI组件
   - 创建新的组件实例
   - 保持应用状态和数据

4. **API接口** (HTTP服务器)
   - 提供REST API手动触发重载
   - 支持重载特定组件或全部组件

5. **状态保持**
   - 重载时保存窗口选择状态
   - 保留分析结果内容
   - 维持用户操作上下文

技术优势：
✅ 无需重启程序
✅ 实时看到界面变化
✅ 保持程序状态
✅ 支持API控制
✅ 开发效率大幅提升

应用场景：
• UI原型快速迭代
• 界面样式调试
• 组件功能测试
• 开发环境优化
"""
    print(help_text)


def main():
    print("🔥 Python tkinter 热重载演示")
    print("=" * 50)
    
    while True:
        print("\n选择操作:")
        print("1. 🎬 运行热重载演示")
        print("2. ❓ 查看技术说明")
        print("0. 退出")
        
        choice = input("\n请选择 (0-2): ").strip()
        
        if choice == "0":
            print("👋 再见！")
            break
        elif choice == "1":
            demo_hot_reload()
        elif choice == "2":
            show_help()
        else:
            print("❌ 无效选择")
        
        input("\n按回车继续...")


if __name__ == "__main__":
    main() 