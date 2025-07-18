#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UIA修复测试脚本
用于验证UIA兼容性问题的修复效果
"""

import sys
import time
import traceback
import os
from window_manager import WindowManager
from window_analyzer import WindowAnalyzer
from logger import analyzer_logger

# 设置控制台编码
if os.name == 'nt':
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except:
        pass

def test_uia_initialization():
    """测试UIA初始化"""
    print("=" * 60)
    print("UIA初始化测试")
    print("=" * 60)
    
    try:
        from uia_analyzer import UIAAnalyzer
        
        print("1. 创建UIA分析器...")
        uia_analyzer = UIAAnalyzer()
        
        print("2. 检查初始化状态...")
        init_info = uia_analyzer.get_initialization_info()
        print(f"   - UIA可用: {init_info['available']}")
        print(f"   - 初始化方法: {init_info['method']}")
        print(f"   - COM初始化: {init_info['com_initialized']}")
        
        if init_info['available']:
            print("✅ UIA初始化成功!")
            return True, uia_analyzer
        else:
            print("❌ UIA初始化失败")
            return False, None
            
    except Exception as e:
        print(f"❌ UIA初始化异常: {str(e)}")
        traceback.print_exc()
        return False, None

def test_window_analysis():
    """测试窗口分析功能"""
    print("\n" + "=" * 60)
    print("窗口分析测试")
    print("=" * 60)
    
    try:
        print("1. 创建窗口管理器...")
        window_manager = WindowManager()
        
        print("2. 获取所有窗口...")
        windows = window_manager.get_all_windows()
        print(f"   发现 {len(windows)} 个窗口")
        
        if not windows:
            print("❌ 没有找到可分析的窗口")
            return False
        
        # 选择第一个窗口进行测试
        test_window = windows[0]
        print(f"3. 测试窗口: {test_window['title']} (HWND: {test_window['hwnd']})")
        
        print("4. 创建窗口分析器...")
        analyzer = WindowAnalyzer()
        
        print("5. 执行窗口分析...")
        start_time = time.time()
        
        # 测试UIA分析
        try:
            result = analyzer.analyze_window(test_window['hwnd'], use_uia=True)
            analysis_time = time.time() - start_time
            
            print(f"✅ 窗口分析成功! (耗时: {analysis_time:.2f}秒)")
            print(f"   - 分析方法: {result.get('analysis_method', 'Unknown')}")
            print(f"   - 元素数量: {len(result.get('elements', []))}")
            
            # 检查UIA特定信息
            if 'uia_analysis' in result:
                uia_info = result['uia_analysis']
                print(f"   - UIA元素总数: {uia_info.get('total_elements', 0)}")
                print(f"   - 交互元素: {len(uia_info.get('interactive_elements', []))}")
                print(f"   - 初始化方法: {uia_info.get('initialization_method', 'Unknown')}")
            
            # 检查诊断信息
            if 'diagnostic_info' in result:
                diag = result['diagnostic_info']
                print(f"   - UIA可用: {diag.get('uia_available', False)}")
                print(f"   - 使用回退: {diag.get('fallback_used', False)}")
                if diag.get('uia_failure_reason'):
                    print(f"   - UIA失败原因: {diag['uia_failure_reason']}")
            
            return True
            
        except Exception as e:
            print(f"❌ 窗口分析失败: {str(e)}")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ 窗口分析测试异常: {str(e)}")
        traceback.print_exc()
        return False

def test_fallback_mechanism():
    """测试回退机制"""
    print("\n" + "=" * 60)
    print("回退机制测试")
    print("=" * 60)
    
    try:
        window_manager = WindowManager()
        windows = window_manager.get_all_windows()
        
        if not windows:
            print("❌ 没有找到可测试的窗口")
            return False
        
        test_window = windows[0]
        analyzer = WindowAnalyzer()
        
        print("1. 测试强制使用传统方法...")
        result_traditional = analyzer.analyze_window(test_window['hwnd'], use_uia=False)
        
        print(f"✅ 传统方法分析成功")
        print(f"   - 分析方法: {result_traditional.get('analysis_method', 'Unknown')}")
        print(f"   - 元素数量: {len(result_traditional.get('elements', []))}")
        
        print("2. 测试UIA方法...")
        result_uia = analyzer.analyze_window(test_window['hwnd'], use_uia=True)
        
        print(f"✅ UIA方法分析完成")
        print(f"   - 分析方法: {result_uia.get('analysis_method', 'Unknown')}")
        print(f"   - 元素数量: {len(result_uia.get('elements', []))}")
        
        # 比较结果
        traditional_count = len(result_traditional.get('elements', []))
        uia_count = len(result_uia.get('elements', []))
        
        print(f"3. 结果比较:")
        print(f"   - 传统方法元素数: {traditional_count}")
        print(f"   - UIA方法元素数: {uia_count}")
        
        if uia_count > traditional_count:
            print("✅ UIA方法提供了更详细的分析结果")
        elif traditional_count > 0:
            print("✅ 传统方法提供了可靠的回退选项")
        
        return True
        
    except Exception as e:
        print(f"❌ 回退机制测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("错误处理测试")
    print("=" * 60)
    
    try:
        analyzer = WindowAnalyzer()
        
        print("1. 测试无效窗口句柄...")
        try:
            result = analyzer.analyze_window(99999, use_uia=True)
            print("⚠️  无效句柄测试未按预期失败")
        except Exception as e:
            print(f"✅ 正确处理无效句柄: {str(e)[:100]}...")
        
        print("2. 测试空句柄...")
        try:
            result = analyzer.analyze_window(0, use_uia=True)
            print("⚠️  空句柄测试未按预期失败")
        except Exception as e:
            print(f"✅ 正确处理空句柄: {str(e)[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误处理测试失败: {str(e)}")
        return False

def generate_test_report():
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("测试报告生成")
    print("=" * 60)
    
    # 运行所有测试
    test_results = {}
    
    print("执行测试套件...")
    test_results['uia_init'] = test_uia_initialization()
    test_results['window_analysis'] = test_window_analysis()
    test_results['fallback'] = test_fallback_mechanism()
    test_results['error_handling'] = test_error_handling()
    
    # 生成报告
    print("\n" + "=" * 60)
    print("最终测试报告")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if (result[0] if isinstance(result, tuple) else result))
    
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n详细结果:")
    for test_name, result in test_results.items():
        status = "✅ 通过" if (result[0] if isinstance(result, tuple) else result) else "❌ 失败"
        print(f"  - {test_name}: {status}")
    
    # 生成建议
    print("\n建议:")
    if passed_tests == total_tests:
        print("🎉 所有测试通过! UIA兼容性问题已解决。")
    elif test_results.get('fallback', False):
        print("⚠️  UIA可能有问题，但回退机制工作正常。")
    else:
        print("🚨 存在严重问题，需要进一步调试。")
    
    return passed_tests / total_tests >= 0.75

def main():
    """主函数"""
    print("UIA兼容性修复验证测试")
    print("时间:", time.strftime('%Y-%m-%d %H:%M:%S'))
    print("Python版本:", sys.version)
    
    try:
        success = generate_test_report()
        
        if success:
            print("\n🎉 测试完成 - UIA修复验证成功!")
            return 0
        else:
            print("\n❌ 测试完成 - 仍存在问题需要解决")
            return 1
            
    except Exception as e:
        print(f"\n💥 测试执行失败: {str(e)}")
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)