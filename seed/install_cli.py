#!/usr/bin/env python3
"""
安装seed CLI工具的脚本
"""

import os
import sys
import shutil
from pathlib import Path

def install_cli():
    """安装seed CLI工具"""
    
    # 获取当前脚本目录
    current_dir = Path(__file__).parent
    cli_script = current_dir / "cli.py"
    
    if not cli_script.exists():
        print("❌ 找不到cli.py文件")
        return False
    
    # 检查操作系统
    if sys.platform == "win32":
        # Windows系统
        # 尝试安装到Python Scripts目录
        python_dir = Path(sys.executable).parent
        scripts_dir = python_dir / "Scripts"
        
        if scripts_dir.exists():
            target_path = scripts_dir / "seed.py"
            try:
                shutil.copy2(cli_script, target_path)
                print(f"✅ CLI工具已安装到: {target_path}")
                print("💡 现在可以使用: python -m Scripts.seed <命令>")
                return True
            except PermissionError:
                print("❌ 没有权限写入Scripts目录，请以管理员身份运行")
                return False
        else:
            print("❌ 找不到Python Scripts目录")
            
    else:
        # Unix/Linux/macOS系统
        # 尝试安装到用户的本地bin目录
        home_bin = Path.home() / ".local" / "bin"
        home_bin.mkdir(parents=True, exist_ok=True)
        
        target_path = home_bin / "seed"
        
        try:
            shutil.copy2(cli_script, target_path)
            # 设置执行权限
            os.chmod(target_path, 0o755)
            print(f"✅ CLI工具已安装到: {target_path}")
            print("💡 现在可以使用: seed <命令>")
            print("📝 请确保 ~/.local/bin 在您的PATH中")
            return True
        except PermissionError:
            print("❌ 没有权限写入~/.local/bin目录")
            return False
    
    return False

def create_alias():
    """创建命令别名"""
    current_dir = Path(__file__).parent
    cli_script = current_dir / "cli.py"
    
    print("\n📋 手动使用方法:")
    print(f"   python {cli_script} <命令>")
    print("\n💡 或者添加别名到你的shell配置文件:")
    print(f"   alias seed='python {cli_script.absolute()}'")

def main():
    print("🚀 安装seed CLI工具...")
    
    if install_cli():
        print("\n🎉 安装完成!")
    else:
        print("\n⚠️  自动安装失败，使用手动方法:")
        create_alias()
    
    print("\n📚 使用示例:")
    print("   seed health        # 检查服务器状态")
    print("   seed create myapp  # 创建新项目")
    print("   seed list          # 列出所有项目")
    print("   seed --help        # 查看完整帮助")

if __name__ == "__main__":
    main() 